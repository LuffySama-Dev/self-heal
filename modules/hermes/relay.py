"""Private SigNoz Bearer-auth webhook to Hermes HMAC-V2 relay."""
import hashlib
import hmac
import http.server
import json
import os
import time
import urllib.error
import urllib.request


def allowed_notification(data, state):
    if state.get('phase', 'active') != 'active':
        return False
    cutoff = state.get('resumed_at', 0)
    if not cutoff:
        return True
    import datetime
    for alert in data.get('alerts', []):
        try:
            started = datetime.datetime.fromisoformat(alert['startsAt'].replace('Z', '+00:00')).timestamp()
        except (KeyError, ValueError, TypeError):
            return False
        if started >= cutoff:
            return True
    return False


def handler(token, secret, target, maintenance_file=None):
    # Never forward redirects containing the webhook payload or signature.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect()
    )

    class Handler(http.server.BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def reply(self, status):
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            # Bodies and authentication headers must not appear in logs.
            pass

        def do_GET(self):
            self.reply(200 if self.path == "/health" else 404)

        def do_POST(self):
            if self.path != "/alerts/signoz":
                return self.reply(404)
            auth = self.headers.get("Authorization", "").encode()
            if not hmac.compare_digest(auth, ("Bearer " + token).encode()):
                return self.reply(401)
            if self.headers.get("Transfer-Encoding"):
                return self.reply(400)
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self.reply(400)
            if size <= 0 or size > 1024 * 1024:
                return self.reply(413)
            try:
                body = self.rfile.read(size)
                data = json.loads(body)
            except (ValueError, OSError):
                return self.reply(400)
            if len(body) != size or not isinstance(data, dict):
                return self.reply(400)
            if not isinstance(data.get("alerts"), list):
                return self.reply(400)
            if maintenance_file is not None:
                try:
                    state = json.loads(maintenance_file.read_text()) if maintenance_file.exists() else {}
                    if state.get('phase', 'active') != 'active':
                        return self.reply(204)
                    if state.get('resumed_at'):
                        data['alerts'] = [a for a in data['alerts']
                                          if allowed_notification({'alerts':[a]}, state)]
                        if not data['alerts']:
                            return self.reply(204)
                        body = json.dumps(data).encode()
                except (OSError, ValueError):
                    return self.reply(503)
            stamp = str(int(time.time()))
            signature = hmac.new(
                secret.encode(), stamp.encode() + b"." + body, hashlib.sha256
            ).hexdigest()
            request = urllib.request.Request(
                target, data=body, headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Timestamp": stamp,
                    "X-Webhook-Signature-V2": signature,
                    # Exact retries have the same ID; Hermes deduplicates for 1h.
                    "X-Request-ID": hashlib.sha256(body).hexdigest(),
                },
            )
            try:
                with opener.open(request, timeout=15) as response:
                    status = response.status
            except (urllib.error.URLError, TimeoutError, OSError):
                status = 502
            print(f"hermes_delivery_status={status}", flush=True)
            self.reply(status)

    return Handler


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import selfheal_config as config
    server = http.server.ThreadingHTTPServer(
        (os.environ["RELAY_HOST"], int(os.environ.get("RELAY_PORT", "8645"))),
        handler(os.environ["RELAY_TOKEN"], os.environ["WEBHOOK_SECRET"],
                os.environ.get("HERMES_WEBHOOK_URL", "http://127.0.0.1:8644/webhooks/signoz"),
                config.CONFIG_PATH.parent / "maintenance.json"),
    )
    server.serve_forever()
