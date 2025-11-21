# QuMail-KMS – Testsprite Product Specification

Version: 1.0
Date: 2025-11-01
Scope: KMS service (FastAPI) running two instances on localhost ports 9010 (KMS-1) and 9020 (KMS-2).

## Purpose
Provide a clear, testable specification for QuMail-KMS so Testsprite can generate and execute backend tests that validate functional behavior and non-functional requirements (stability, no socket leaks, sequential reliability).

## Actors & Topology
- KMS-1 (default):
  - KMS_ID: kms-1
  - SAE_ID: 25840139-0dd4-49ae-ba1e-b86731601803
  - Port: 9010
  - Peer: http://127.0.0.1:9020
- KMS-2:
  - KMS_ID: kms-2
  - SAE_ID: c565d5aa-8670-4446-8471-b0e53e315d2a
  - Port: 9020
  - Peer: http://127.0.0.1:9010

## Non-Functional Requirements (NFR)
- Reliability: 10 sequential request cycles must pass without hangs or timeouts.
- Connection hygiene: No uncontrolled growth of CLOSE_WAIT/FIN_WAIT sockets. Outbound requests include `Connection: close`.
- Latency: Typical enc/dec operation completes in < 2s per request under local conditions.
- Idempotency: Verification endpoints must be safe to call repeatedly.
- Security: HTTP allowed in dev; no client certs required. One-time pad enforcement: consumed keys are not re-issued.

## API Surface (KMS)
Base URL examples:
- KMS-1: http://127.0.0.1:9010
- KMS-2: http://127.0.0.1:9020

### 1) Health
GET /health
- 200 OK Body:
  - status: "healthy" | "unhealthy"
  - kms_id: string
  - total_keys: number
  - available_keys: number

### 2) Key Management (ETSI QKD 014 parity)

Headers used:
- X-SAE-ID: string (master or slave depending on endpoint)
- X-Slave-SAE-ID: string (paired SAE)

POST /api/v1/keys/enc_keys
- Request JSON:
  - number: int (1..100)
  - size: int? (bytes, optional)
- Response 200 JSON:
  - keys: [{ key_ID: string, key: string }]
- Behavior:
  - Generates (and/or draws from pool) keys for (master, slave) pair.
  - Triggers sync to peer KMS-2 via /kme/sync.

POST /api/v1/keys/dec_keys
- Request JSON:
  - key_IDs: string[] (1..100)
- Headers:
  - X-SAE-ID: slave SAE
  - X-Slave-SAE-ID: master SAE
- Response 200 JSON:
  - keys: [{ key_ID: string, key: string }]
- Behavior:
  - Returns keys that must already exist on this KMS due to previous sync.
  - Marks keys as consumed.

GET /api/v1/keys/{master_sae_id}/status
- Headers:
  - X-Slave-SAE-ID: string
- Response 200 JSON includes:
  - source_KME_ID, target_KME_ID, stored_key_count, key_size limits.

### 3) KME Internal

POST /api/v1/kme/sync
- Headers: X-KMS-ID: string (source KMS ID)
- Request JSON:
  - keys: [{ key_ID, key, key_size, master_sae_id, slave_sae_id, created_at?, entropy?, quantum_source?, origin_kms_id? }]
  - source_kms_id: string
  - target_sae_id: string
  - timestamp: string (ISO8601)
- Response 200 JSON:
  - { synced_count: number, status: "success"|"partial", timestamp: string }

POST /api/v1/kme/verify
- Headers: X-KMS-ID: string
- Request JSON:
  - key_ids: string[]
  - master_sae_id: string
  - slave_sae_id: string
- Response 200 JSON:
  - { all_verified: boolean, verified_count: number, missing_keys: string[] }

GET /api/v1/kme/status
- Response 200 JSON:
  - { KME_ID, SAE_ID, status, version, uptime_seconds, total_keys, available_keys, sync_enabled }

POST /api/v1/kme/pool/status
- Request JSON:
  - { master_sae_id: string, slave_sae_id: string }
- Response 200 JSON:
  - { master_sae_id, slave_sae_id, current_count, min_pool_size, max_pool_size, replenish_threshold, needs_replenishment, health }

GET /api/v1/kme/stats
- Response 200 JSON aggregates stats across store, synchronizer, and pool manager.

## Success Criteria for Testsprite
- Happy path:
  1. On KMS-1, call enc_keys(number=2, size=256) with headers (X-SAE-ID=master, X-Slave-SAE-ID=slave).
  2. Verify KMS-2 /kme/sync receives 2 keys (synced_count >= 2).
  3. On KMS-2, call dec_keys for the returned key_IDs (headers swapped) and receive same keys.
- Sequential reliability: Repeat above flow 10 times with fresh key_IDs.
- Verification: After enc_keys on KMS-1, POST /kme/verify on KMS-2 returns all_verified=true for those IDs.
- Status endpoints: /health and /kme/status return 200 with valid schema.
- Pool behavior: /kme/pool/status returns consistent counts; pool replenishment triggers when low.

## Error Handling
- 400: Missing headers or invalid payloads.
- 403: KMS ID mismatch on /kme/sync.
- 404: dec_keys when some key_IDs not present.
- 429: (if enabled) Excessive request rate.
- 500: Unhandled server errors with logged stack traces.

## Environment & Startup
- Start KMS-1 (9010) and KMS-2 (9020) locally. Instance configs in qumail-kms/.env.kms1 and .env.kms2
- Outbound sync/verify requests use Python requests with `Connection: close`.

## Out of Scope (for these tests)
- Gmail OAuth, email UI, and full backend application.
- Real QKD hardware; simulated quantum source is used.

## Notes for Test Generation
- Prefer deterministic steps by reading key IDs from enc_keys response.
- Keep per-test cleanup minimal; consumed keys are not reusable by design.
- Use short timeouts (<= 5s) for HTTP calls; services are local.
