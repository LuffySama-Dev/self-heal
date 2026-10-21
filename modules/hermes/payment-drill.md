# Payment failure drill — 20 October 2026

The Payment Charge alert detected the injected failure and Hermes investigated
payment and checkout telemetry. The failure flag is off, SigNoz has cleared the alert, and Hermes received and
investigated the resolved notification. The full alert lifecycle passed.

## Timeline

| Event | Time |
|---|---|
| paymentFailure set to 50% | 12:06:14 IST |
| Alert firing | 12:14:17 IST |
| paymentFailure restored to off | 12:16:13 IST |
| Alert inactive | 12:20:17 IST |
| Resolved webhook received by Hermes | 12:24:47 IST |
| Hermes recovery report completed | 12:25:29 IST |

Hermes received the firing webhook at 12:14:47 IST and completed its investigation
at 12:15:37 IST. It correlated PaymentService/Charge failures with warning logs
at `charge.js:48` and an upstream failed Checkout PlaceOrder trace. It used
read-only SigNoz MCP tools; no remediation was executed.

The investigation did not establish the feature-flag cause from telemetry.
It also compared the historical alert value with a different, fresh time window
and flagged that rate discrepancy. After the drill, the alert notification annotation was clarified to explain
the evaluator's two-minute delay and the need to inspect all three query points.
The threshold, routing and evaluation behavior were preserved.

The alert remains enabled. Every demo feature flag matches its pre-drill value.
The 20-minute fallback reset timer was cancelled after the manual reset.

## Hermes firing report

**Firing warning—not a delivery test or resolved alert.** SigNoz currently reports the rule active for `payment` in `opentelemetry-demo`, starting **2026-10-20 06:44:17 UTC**.

- **Window and rate:** Alert history records **36.4%**, above the 20% threshold. A fresh query of Charge server spans for **06:39:17–06:44:17 UTC** returned **7 errors and 4 successes**. Raw spans confirm those counts; they do not reproduce the historical percentage, so the exact rate discrepancy remains unresolved.
- **Correlated failure:** Payment spans and matching warning logs report `Payment request failed. Invalid token. demo.user_context.loyalty_level=gold`, with a stack location of `charge.js:48`. Failures continued at **06:44:41 UTC**.
- **Checkout impact:** Trace `f64a6123cffc3b134c271db7b6f7daef` links the payment failure to an errored checkout `PlaceOrder` request. Successful payment logs and nonzero `demo.payment.transactions` metric samples also exist: this is partial transaction failure, not evidence of a complete outage.
- **Uncertainty:** No matching flagd logs or `paymentFailure` log events were found in the inspected window. A feature-flag cause is **not established**.

**Proposed next step:** Have the payment owner inspect invalid-token handling and flag-evaluation evidence for the linked trace, and reconcile the rule’s historical percentage against its exact namespace-filtered query before choosing a remediation. **Only read-only SigNoz tools were used; no changes made. Any change requires approval.**

## Recovery verification

The actual webhook payload had status `resolved`, startsAt
`2026-10-20T06:44:17.385644716Z` and endsAt
`2026-10-20T06:50:17.385644716Z`. The relay returned HTTP 202 from Hermes.
Independent telemetry verification at 12:25 IST found 23 Charge requests after
the flag reset, all successful. All three alert query samples were zero and the
rule was inactive. The alert remains enabled for future failures.

The raw Hermes report below describes its query range as extending to 07:00 UTC;
that was a requested range extending beyond the observation time, not verified
future recovery. Its feature-flag attribution remains unconfirmed from telemetry.

## Hermes recovery report

**Resolved — payment Charge errors, not a delivery test.**

- **Window:** October 20, 2026, **06:44:17–06:50:17 UTC**. Affected service: `payment`, namespace `opentelemetry-demo`; failures propagated to `checkout`. The rule currently reports **inactive**.
- **Evidence:** Payment spans and matching warning logs report `Payment request failed. Invalid token. demo.user_context.loyalty_level=gold`, with the exception at `charge.js:48`. Trace `64f32852514802d4403a5e743addd46f` links the failed payment Charge to a failed checkout `PlaceOrder` at **06:46:01 UTC**.
- **Recovery:** No further Charge server-span errors appeared after that failure in the inspected window through **07:00 UTC**. After resolution, **5 Charge server spans were successful, none errored**. The `demo.payment.transactions` counter also continued increasing.
- **Uncertainty:** This supports an application-level payment rejection, not a service-wide outage. A feature-flag cause is **unconfirmed**: targeted flag-event log searches returned no matches. The notification’s reported **30.8%** was not independently reproduced. Low traffic can also clear this rule, so resolution alone does not establish full recovery.

**Proposed next step:** Have the payment owner review the invalid-token path and feature-flag evaluation/audit history for the gold-loyalty cohort around **06:38–06:46 UTC**, while monitoring subsequent Charge requests.

Only read-only SigNoz tools were used; no changes were made.
