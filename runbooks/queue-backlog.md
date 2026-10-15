# Queue backlog / consumer lag (fictional service)

Symptoms: queue backlog grows, consumer lag increases, messages process slowly.

1. Compare incoming message rate with consumer processing rate.
2. Check consumer error logs for repeated failures and retry loops.
3. Inspect dead-letter queue count. Preserve failed messages for investigation.
4. Check database latency and connection pool saturation before adding consumers.
5. If consumers are healthy and downstream capacity is available, ask the operator to consider scaling consumers gradually.

Escalate if lag continues to rise after the bottleneck is identified. Do not purge the queue: that can lose business events. These are suggested checks, not observed system measurements.
