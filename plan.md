# Plan: Query MongoDB via API (No CSV Uploads)

## Overview

- __Goal__: Let users select Month/Insurer in `index_timeframe.html` and fetch filtered data directly from MongoDB (no CSV upload), without impacting existing systems or managing per-client IP allowlisting.
- __Approach__: Add a secure API layer in front of MongoDB that the front-end calls. Keep MongoDB locked down to trusted egress IP(s) only.

## Options

- __Atlas Data API (no server)__
  - Managed HTTPS API by MongoDB Atlas; clients call endpoints using API keys/App Services auth.
  - Pros: No server ops, quick to enable, fine-grained rules (read-only, field-level, query validation).
  - Cons: Less flexibility than custom server for advanced logic/caching.

- __Small Backend API (FastAPI/Flask)__
  - Host a tiny service that connects to MongoDB with a read-only user. Allowlist only this server’s static egress IP in Atlas.
  - Pros: Full control, custom logic, pagination, CSV export, caching, rate limiting, detailed logging.
  - Cons: Need hosting with static egress IP and minimal DevOps.

- __Serverless with Static Egress__
  - Use Lambda/Cloud Run/Fly/Render with NAT or provider static egress IP add-on. Allowlist that IP in Atlas.
  - Pros: Scales easily; less server management.
  - Cons: Some platform setup to ensure fixed outbound IP(s).

## What Not To Do

- Do __not__ expose MongoDB to the public internet (avoid 0.0.0.0/0 in Atlas network rules).
- Do __not__ connect directly from the browser; it leaks credentials and runs into IP/CORS/security issues.
- Do __not__ share write privileges; use least-privilege, read-only access for this reporting API.

## Recommendation

- If you want fastest minimal-ops path: __Atlas Data API__ with read-only rules and projections.
- If you need richer features (formatting, CSV export, caching, custom business logic): __FastAPI__ microservice with a static egress IP allowlisted in Atlas.

## Proposed API Design (for a custom backend)

- `GET /api/filters/months`
  - Returns distinct months available, e.g., `["2025-06", "2025-07"]`.
- `GET /api/filters/insurers`
  - Returns distinct insurers.
- `GET /api/report?month=YYYY-MM&insurer=Acme&limit=100&skip=0`
  - Returns filtered records as JSON, with strict field projections.
- `GET /api/report/export.csv?month=YYYY-MM&insurer=Acme`
  - Streams CSV for current filters.

## Backend Implementation Notes

- __Framework__: FastAPI + Uvicorn (or Flask) + `pymongo`.
- __Config__: Environment variables for `MONGODB_URI`, `MONGO_DB`, `MONGO_COLLECTION`.
- __Security__: Read-only Mongo user; input validation; strict projections; rate limiting; API keys/JWT; CORS restricted to your front-end origin.
- __Performance__: Indexes on `month`, `insurer`; pagination with `limit/skip`; server-side caching for common queries.
- __Resilience__: Connection pooling tuned; timeouts; structured logging.

## Frontend Adjustments (`index_timeframe.html`)

- Replace file upload UI with:
  - Month select (populated via `/api/filters/months`).
  - Insurer select (populated via `/api/filters/insurers`).
  - Load button calls `/api/report` with chosen filters.
- Render JSON in your existing table.
- Optional: “Download CSV” button linking to `/api/report/export.csv` with the same filters.

## Security and Guardrails

- Read-only DB user dedicated to the API; separate from existing apps.
- Principle of least privilege and field-level projection.
- Input validation (whitelists/regex for month, insurer; enforce `limit` max).
- Rate limiting and auth; per-client API keys if distributing broadly.
- Logging/auditing for requests and query performance.

## Zero-Downtime Rollout

1. Create a read-only MongoDB user limited to required DB/collections.
2. Host API with static egress IP; allowlist that IP in Atlas (keep existing IPs unchanged).
3. Validate queries against staging; tune indexes and projections.
4. Deploy to production; enable HTTPS and CORS for your front-end only.
5. Update front-end to call API; keep CSV upload as fallback initially.
6. Monitor performance and logs; remove CSV flow later if desired.

## Atlas Data API Path (Alternative)

- Enable Data API for your cluster.
- Define App Services rules: read-only, allowed filters, and field projections.
- Create a Function to handle filtered finds and validation.
- Issue per-client API keys (optional) and set quotas/rate limits.
- Point front-end to HTTPS endpoints; no IP allowlisting required for clients.

## Information Needed to Implement

- Preferred route: Atlas Data API or FastAPI backend.
- Mongo details: DB/collection names, month and insurer field names, column list to return.
- Hosting preference (to ensure static egress IP if not using Data API).
- Any additional filter semantics (e.g., month format, “All Insurers”).

## Optional Enhancements

- Server-side caching; Redis for repeated month/insurer queries.
- Download as Excel alongside CSV.
- Simple auth portal or per-client API keys management.
- Usage analytics and cost guardrails.
