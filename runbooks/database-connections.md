# Database connection pool exhaustion (fictional service)

Symptoms: database connection timeout, exhausted pool, requests waiting for connections.

1. Compare active and idle connections with the configured pool limit.
2. Look for long-running queries and transactions holding connections.
3. Review recent application deployments for connection leaks.
4. Check database CPU, memory and query latency before increasing the pool size.
5. Escalate to the database owner with timestamps, pool metrics and slow-query examples.

Do not terminate sessions or restart the database automatically. These are suggested checks, not observed system measurements.
