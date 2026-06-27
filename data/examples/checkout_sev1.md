Timeline: Saturday 10:36-10:51 PT

10:36 PT - checkout-api v2.18.0 canary reaches 50%.
10:38 PT - canary promoted to 100%.
10:40 PT - checkout p95 latency climbs from 480ms to 2.9s.
10:42 PT - checkout-api 5xx rate crosses 12%.
10:43 PT - database pool active connections pinned at 100/100.
10:44 PT - customer support reports payment spinner and intermittent "Unable to place order" banner.
10:45 PT - payment-adapter logs show retries, but provider status page is green.
10:47 PT - autoscaling adds pods but error rate does not improve.
10:49 PT - Redis hit rate appears slightly lower, but not enough data yet.
10:51 PT - Incident Commander requests root-cause hypotheses and reversible mitigation plan.

Representative logs:

checkout-api-7ddc9f:
ERROR order_submit request_id=8f7 timeout="db connection acquisition exceeded 2500ms" cart_id=redacted
WARN payment_authorize retry=2 elapsed_ms=3100 request_id=8f7
ERROR order_submit status=504 route=/checkout/submit version=v2.18.0

orders-db:
WARN pool_wait_ms=2480 active=100 idle=0 pending=372 service=checkout-api
WARN slow_query fingerprint="SELECT promotions.*, inventory.* FROM..." p95_ms=1840

feature_flags:
INFO checkout_recommendations_v2 cohort=25% enabled_at=10:34 PT
INFO checkout_release_guardrails enabled=true

