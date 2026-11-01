# Deployment and operations

Guniapa has container build definitions and a single-host Docker Compose stack for PostgreSQL, Redis, Django/Gunicorn, Next.js and NGINX. Redis provides shared throttling and short-lived OTP state across backend workers; its cache is intentionally not persistent. This is a deployment foundation, **not evidence that the service is production-ready**. Do not expose it to customers until every release gate below has an owner and is verified in the target environment.

## Local Compose smoke test

Docker Engine and the Compose plugin are required.

```sh
cp .env.example .env
```

Replace the placeholder database password, Django `SECRET_KEY` and frontend `SESSION_SECRET` with unrelated local random values. Start the stack and verify health:

```sh
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8080/api/health/
```

The local example binds NGINX to loopback and runs Django in debug mode. It is not a production configuration. Create an administrator for setup:

```sh
docker compose exec backend python manage.py createsuperuser
```

Use Django admin at `http://localhost:8080/admin/` to add active service categories and configure any fee rule and moderation settings. No categories, fees, users or payment behavior are seeded by default. Local OTP may be returned as a development code; this path must not be enabled in production.

For development without Docker:

```sh
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

In another terminal:

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

The backend tests use an in-memory SQLite database. Local app development can use SQLite as shown in `backend/.env.example`; production must use PostgreSQL.

## Production configuration gates

Use a secret manager or protected deployment environment, not a committed `.env` file. Set every value explicitly:

- `DEBUG=false`.
- `SECRET_KEY`: unique, random, at least 50 characters. `SESSION_SECRET`: a different random secret of at least 32 characters.
- `DB_PASSWORD`: unique high-entropy secret. Set `DB_SSLMODE=require` when connecting to a managed PostgreSQL service. The included Compose database is unencrypted at the application protocol layer; use a private host network and encrypted persistent storage.
- The Compose Redis service is private to the application data network and has no persistence or host port. Do not expose it publicly; provision authentication, TLS and monitored capacity if moving it to a managed service.
- `ALLOWED_HOSTS`: exact public hostnames plus `127.0.0.1` for the container health check. Never use `*`.
- `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`: exact HTTPS origins only.
- `SECURE_SSL_REDIRECT=true`, `TRUST_X_FORWARDED_PROTO=true`, and `SECURE_HSTS_SECONDS=31536000` only when the trusted edge terminates TLS and sets `X-Forwarded-Proto: https`.
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` remain false until every affected hostname is HTTPS-ready and the domain owner explicitly accepts the irreversible preload implications. Django's deploy check warnings for these flags are intentional release gates, not warnings to suppress blindly.
- `NGINX_BIND_ADDRESS`: bind only to a private interface reachable from the trusted TLS ingress. Restrict it with a firewall/security group; do not make NGINX or Django directly public without that edge.
- Keep `GUNIAPA_API_BASE_URL=http://backend:8000` as an internal service address; it is server-only and must not be a `NEXT_PUBLIC_*` setting.
- Configure NGINX real-client-IP handling with the exact trusted ingress CIDRs before relying on IP-based rate limits. The default config keys limits to the immediate peer; do not trust arbitrary client-supplied forwarding headers.
- `LOG_LEVEL=INFO` is the default. Route container logs to a protected, monitored log system with a retention policy and ensure access tokens, OTPs, addresses and other personal data are not logged.

The included NGINX container is HTTP-only and is intended to sit behind a trusted TLS ingress/load balancer. It forwards the ingress `X-Forwarded-Proto` value to Django. Restrict network access so clients cannot bypass the TLS ingress or forge trusted forwarding headers. HSTS is sent only after Django observes HTTPS.

## Release and health checks

The `release` Compose service applies migrations and runs `collectstatic` before the application starts. For each release:

1. Review the migration diff and application changes; take and verify a restorable PostgreSQL backup.
2. Build the exact image digest to be released and run the complete CI workflow.
3. Apply migrations with the release image, then start the application and check every container's health:

   ```sh
   docker compose up --build -d
   docker compose ps
   curl --fail https://YOUR_HOST/api/health/
   ```

4. Smoke-test registration, real OTP delivery, login/refresh/logout, both marketplace roles, admin access, NGINX 429 handling, and the health endpoint through the public HTTPS host.
5. Confirm logs, alerts, database capacity, backups and the rollback operator are available before opening user access.

The health endpoint verifies database connectivity but does not establish that SMS, email, payments or other external providers work. `manage.py check --deploy` must be run with the actual production settings. Do not enable HSTS subdomains/preload just to silence warnings.

## Database backups and restore

The Compose PostgreSQL volume is persistent storage, not a backup. Configure encrypted, off-host, automated PostgreSQL backups and a retention schedule before launch. Restrict access to backup encryption keys and test restore into an isolated environment on a recurring schedule.

An operator can create a one-off logical backup from the Compose database (store the resulting file only in an encrypted, access-controlled backup location):

```sh
docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > guniapa-backup.dump
```

Restore drills must use an isolated database and a matching application release. Verify schema migrations, account access, marketplace records, fee ledger integrity and audit history before approving the recovery. Never experiment with a restore against the only production database; define and rehearse the production cutover/rollback procedure separately.

## Current launch blockers

- **SMS:** no production SMS adapter/provider is implemented. OTP delivery fails closed in production; signup/login cannot be treated as operational until delivery, sender registration, quotas, abuse monitoring and failure handling are verified.
- **Trust and safety:** identity/document workflows, regulated credential uploads and verification, email verification, incident escalation and a staffed support process are not implemented.
- **Payments and policy:** only provider-reported cash receipts exist; there is no digital payment/refund integration. Fee, cancellation, dispute, safety, privacy/retention, tax and consumer-protection policies require local legal and operational review.
- **Operations:** no hosting account, TLS certificate/ingress, managed secret store, monitoring/alerting, external log retention, automated backup service, restore drill, capacity/load test or incident/on-call plan is configured by this repository.
- **Product scope:** maps/geocoding, recurring/on-call bookings, calendar integrations, full admin frontend and service-category seed data are not included.
- **Security verification:** review dependency advisories, run a production configuration audit and perform an independent security review before launch. Confirm all HSTS domain requirements before enabling subdomain or preload directives.

Do not announce or represent the service as production-ready until these blockers are resolved and documented by the responsible operators.
