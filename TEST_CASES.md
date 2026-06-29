# Test Scenarios

Four synthetic incident scenarios for validating MultiverseGuard. Each has example logs, operator notes, and alert summaries in `data/examples/`.

## 1. Checkout SEV-1

### Signals

- Checkout 5xx spike
- p95 latency rise
- Database pool saturation
- Payment API retries
- Deployment shortly before incident

### Expected Universes

1. Deployment/configuration regression
2. Database or connection-pool saturation
3. Upstream dependency/payment-provider latency
4. Infrastructure/network/load-balancer failure

### Notes

This is the primary recorded demo scenario. Example: `data/examples/checkout_sev1.md`, `data/examples/checkout_sev1_notes.txt`, `data/examples/checkout_dashboard.png`.

## 2. Auth/Login Outage

### Signals

- Login failures
- 401/403 spike
- JWKS cache errors
- Identity provider latency
- Recent certificate rotation

### Expected Universes

1. Bad certificate rotation
2. Stale JWKS cache
3. Identity provider regional outage
4. API gateway auth middleware regression

### Notes

Example: `data/examples/auth_login_outage_notes.txt`, `data/examples/auth_dashboard.png`.

## 3. Kafka/Event Pipeline Lag

### Signals

- Consumer lag rising
- Dead-letter queue growth
- Schema validation errors
- Delayed order fulfillment
- Stale inventory updates

### Expected Universes

1. Schema incompatibility
2. Consumer deployment regression
3. Broker partition imbalance
4. Downstream warehouse throttling

### Notes

Example: `data/examples/kafka_pipeline_lag_notes.txt`, `data/examples/kafka_dashboard.png`.

## 4. Regional Load Balancer Failure

### Signals

- Elevated 502s in one region
- Healthy pods but failed target checks
- TLS handshake errors
- WAF or load-balancer rule change
- Regional p95 latency spike

### Expected Universes

1. Load balancer routing regression
2. WAF false positive
3. TLS certificate mismatch
4. Regional network degradation

### Notes

Example: `data/examples/regional_lb_failure_notes.txt`, `data/examples/regional_lb_dashboard.png`.

## Automated Tests

Offline unit tests live under `tests/`:

- `test_multiverse_flow.py` - core 4-universe flow
- `test_reliability.py` - four-universe invariants and repair retry
- `test_speed_benchmark.py` - single-call benchmark helpers
- `test_parallel_benchmark.py` - 4-way parallel benchmark helpers

Run: `pytest -q` (expected: 36 passed).
