# HTTP 5xx errors and upstream timeouts (fictional service)

Symptoms: HTTP 500, 502, 503 or 504 errors; elevated request latency; upstream timeout.

1. Identify affected routes and compare error rates with the previous healthy period.
2. Correlate the first errors with deployments or configuration changes.
3. Check application logs and upstream service health.
4. Check database connection pool and queue backlog if requests depend on them.
5. Escalate with request identifiers, timestamps and affected routes. An operator can evaluate rollback using the deployment procedure.

Do not disable authentication, delete data or retry requests without considering idempotency. These are suggested checks, not observed system measurements.
