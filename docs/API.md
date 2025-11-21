# API Reference (Quick)

Base path: `/api/v1`

- `POST /api/v1/voice/incoming-call` — Twilio webhook for incoming calls (TwiML response).
- `POST /api/v1/voice/outbound-call` — Trigger an outbound call.
- `GET /api/v1/monitoring/health` — Health check.
- `GET /api/v1/monitoring/metrics` — Metrics exposition (text).
- `POST /api/v1/agents/customer-order/process` — Send a text message to customer order agent.
- `POST /api/v1/orders/calculate` — Calculate totals for session order.
