"""Exercise authentication, signed delivery, retries, and upstream failure."""
import hashlib
import hmac
import http.server
import json
import threading
import unittest
import urllib.error
import urllib.request

from relay import handler


class RelayTest(unittest.TestCase):
    def test_delivery_contract(self):
        received = []

        class Upstream(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                stamp = self.headers["X-Webhook-Timestamp"]
                expected = hmac.new(
                    b"signing-secret", stamp.encode() + b"." + body,
                    hashlib.sha256,
                ).hexdigest()
                received.append((body, self.headers["X-Request-ID"]))
                self.send_response(
                    202 if hmac.compare_digest(
                        self.headers["X-Webhook-Signature-V2"], expected
                    ) else 401
                )
                self.end_headers()

        upstream = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        relay = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            handler("test-token", "signing-secret",
                    f"http://127.0.0.1:{upstream.server_port}/webhooks/signoz"),
        )
        for server in (upstream, relay):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{relay.server_port}/alerts/signoz"
        body = json.dumps({"status": "firing", "alerts": []}).encode()

        def post(auth, payload=body):
            request = urllib.request.Request(
                url, data=payload, headers={"Authorization": auth}
            )
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    return response.status
            except urllib.error.HTTPError as error:
                return error.code

        try:
            self.assertEqual(post("Bearer wrong"), 401)
            self.assertEqual(received, [])
            self.assertEqual(post("Bearer test-token", b"not-json"), 400)
            self.assertEqual(post("Bearer test-token"), 202)
            self.assertEqual(post("Bearer test-token"), 202)
            self.assertEqual(received[0][0], body)
            self.assertEqual(received[0][1], received[1][1])
            upstream.shutdown()
            upstream.server_close()
            self.assertEqual(post("Bearer test-token"), 502)
        finally:
            relay.shutdown()
            relay.server_close()
            upstream.shutdown()
            upstream.server_close()


if __name__ == "__main__":
    unittest.main()
