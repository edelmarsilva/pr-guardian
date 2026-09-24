# Queue and Async Review Skill

## Purpose

This skill reviews Pull Request changes involving background jobs, message queues, workers, scheduled tasks, asynchronous execution, event consumers, and producer/consumer workflows.

Its goal is to identify correctness, reliability, idempotency, retry, timeout, failure-handling, and observability risks introduced or exposed by the Pull Request.

The review should focus on asynchronous behavior that may not be visible from the enqueue or publish operation alone.

---

# Core Principle

Do not assume:

```text
message published
      =
work completed successfully
```

Always consider the complete lifecycle:

```text
producer
   ↓
queue or broker
   ↓
worker / consumer
   ↓
processing
   ↓
persistence / side effect
   ↓
success, retry, failure, or duplicate execution
```

---

# When to Use

Use this skill when a Pull Request changes:

* Redis Queue / RQ;
* Celery;
* RabbitMQ;
* Kafka;
* Redis Streams;
* worker processes;
* background jobs;
* scheduled jobs;
* event consumers;
* message producers;
* retry policies;
* timeout configuration;
* queue routing;
* asynchronous workflows;
* task serialization;
* dead-letter handling;
* job observability.

---

# Inputs

Recommended inputs:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
```

plus:

* changed queue/job files;
* worker configuration;
* broker configuration;
* related tests;
* producer code;
* consumer code;
* deployment configuration.

---

# Phase 1 — Detect Async Technology

Identify the technologies involved.

Possible examples:

```text
RQ
Celery
RabbitMQ
Kafka
Redis Streams
AWS SQS
Google Pub/Sub
custom worker
asyncio task execution
cron / scheduler
```

Do not assume framework behavior before identifying the actual technology.

---

# Phase 2 — Identify Async Components

Classify changed components as:

```text
PRODUCER
JOB
CONSUMER
WORKER
QUEUE
BROKER_CONFIG
SCHEDULER
RETRY_POLICY
SERIALIZER
FAILURE_HANDLER
OBSERVABILITY
```

Example:

```text
app/jobs/report.py
JOB

app/services/report_service.py
PRODUCER

worker.py
WORKER
```

---

# Phase 3 — Build Message or Job Flow

Map the lifecycle.

Example:

```text
POST /reports
    ↓
ReportService
    ↓
enqueue generate_report
    ↓
high-priority queue
    ↓
RQ worker
    ↓
generate_report()
    ↓
reports table
    ↓
email notification
```

This flow is essential for reviewing asynchronous correctness.

---

# Phase 4 — Producer Review

Inspect producer behavior.

Questions:

```text
Is the correct queue/topic used?

Are required arguments provided?

Can invalid payloads be published?

Can the same event be published twice?

Is publishing transactional with related state changes?
```

Example risk:

```text
database commit succeeds
queue publish fails
```

leaving persistent state without corresponding background work.

---

# Phase 5 — Consumer / Worker Review

Inspect:

* job entry point;
* argument validation;
* dependency handling;
* side effects;
* success state;
* failure state.

Ask:

```text
What happens when the worker crashes halfway through?
```

---

# Phase 6 — Payload Contract

Review message/job arguments for:

```text
required fields
types
serialization
versioning
backward compatibility
```

Potential issue:

```text
producer sends new payload shape
old worker expects previous shape
```

This is especially important during rolling deployments.

---

# Phase 7 — Serialization

Inspect serialization mechanisms.

Examples:

```text
JSON
pickle
MessagePack
framework-native serializer
```

Consider:

* compatibility;
* security;
* non-serializable objects;
* timezone handling;
* schema evolution.

Unsafe deserialization concerns should be handed to `security-review`.

---

# Phase 8 — Idempotency

Determine whether repeated execution is safe.

Ask:

```text
What happens if this job runs twice?
```

Common risk areas:

```text
payments
emails
notifications
user creation
external API calls
database inserts
file generation
```

Example:

```text
process_payment(order_id)
process_payment(order_id)
```

must not unintentionally charge twice.

---

# Phase 9 — Duplicate Delivery

Assume duplicate delivery may occur unless the infrastructure guarantees otherwise.

Inspect whether the consumer:

* detects duplicates;
* uses idempotency keys;
* relies on unique constraints;
* safely repeats side effects.

Do not assume "exactly once" semantics without evidence.

---

# Phase 10 — Retry Policy

Inspect retry configuration.

Record:

```text
maximum attempts
retry interval
backoff
retryable exceptions
non-retryable exceptions
```

Potential issues:

```text
retry everything
retry nothing
infinite retry
retry permanent failures
```

---

# Phase 11 — Retry Safety

A job may be technically retryable but not safe to retry.

Example:

```text
send invoice
then fail before marking sent
```

Retry may send the invoice twice.

Review interaction between retries and side effects.

---

# Phase 12 — Backoff

When retries occur, inspect whether backoff is appropriate.

Possible strategies:

```text
fixed
linear
exponential
exponential with jitter
```

Do not require a specific strategy universally.

Look for obvious retry storms.

---

# Phase 13 — Timeout

Inspect:

```text
job timeout
network timeout
database timeout
broker timeout
```

Potential issue:

```text
long-running external request
without any timeout
```

A missing timeout is meaningful when the dependency can block worker capacity.

---

# Phase 14 — Worker Capacity

Consider whether the PR introduces:

```text
blocking operations
long CPU tasks
large synchronous downloads
unbounded loops
```

inside workers.

This may reduce queue throughput.

Only report when impact is material.

---

# Phase 15 — Queue Selection

Inspect whether jobs are routed to appropriate queues.

Example:

```text
critical user-facing job
→ low-priority bulk queue
```

or:

```text
CPU-heavy report generation
→ latency-sensitive queue
```

Use existing project conventions.

---

# Phase 16 — Priority

If priority exists, verify:

```text
high-priority jobs
default jobs
bulk jobs
```

are routed consistently.

Avoid inventing priority rules not present in the system.

---

# Phase 17 — Failure Handling

Review what happens after final failure.

Possible mechanisms:

```text
failed-job registry
dead-letter queue
error table
alert
manual retry
```

Ask:

```text
Can operators discover the failed job?
```

---

# Phase 18 — Dead-Letter Behavior

When DLQ or equivalent exists, inspect:

```text
when message enters DLQ
what metadata is retained
how replay works
```

Potential issue:

```text
message loses original tenant or correlation context
```

---

# Phase 19 — Partial Failure

Async workflows often involve multiple side effects.

Example:

```text
generate report
    ↓
save database record
    ↓
upload file
    ↓
send email
```

Review each failure boundary.

Ask:

```text
Which steps are retryable?
Which steps are already committed?
```

---

# Phase 20 — Transactional Messaging

Look for workflows like:

```text
update database
publish event
```

Potential inconsistency:

```text
DB succeeds
publish fails
```

or the reverse.

When appropriate, identify patterns such as:

```text
transactional outbox
```

but do not prescribe it automatically.

---

# Phase 21 — Ordering

If event order matters, inspect whether ordering is guaranteed.

Examples:

```text
USER_CREATED
USER_DELETED
```

received out of order.

Consider:

* queue partitioning;
* Kafka keys;
* multiple workers;
* retry reordering.

Only report when domain behavior depends on order.

---

# Phase 22 — Concurrency

Inspect whether multiple workers can process related work concurrently.

Potential issues:

```text
same object updated simultaneously
duplicate processing
lost updates
race condition
```

Coordinate with `database-review` when persistence locking is involved.

---

# Phase 23 — Job Uniqueness

If the system intends one job per resource, inspect:

```text
deduplication
unique job ID
lock
registry
```

Potential issue:

```text
user clicks twice
two identical jobs created
```

---

# Phase 24 — Cancellation

When cancellation is supported, inspect:

```text
queued cancellation
running cancellation
partial side effects
state consistency
```

Do not assume deleting a queued message cancels downstream work safely.

---

# Phase 25 — Scheduling

For scheduled tasks, review:

```text
schedule
timezone
duplicate scheduling
missed execution
restart behavior
```

Potential issue:

```text
scheduler restart registers the same periodic job twice
```

---

# Phase 26 — Timezone Handling

Scheduled jobs should consider:

```text
UTC
local timezone
DST
timezone-aware datetime
```

Only report actual inconsistency.

---

# Phase 27 — Job Expiration

Inspect:

```text
TTL
result TTL
message expiration
job expiration
```

Potential issue:

```text
stale job executes long after business event is relevant
```

---

# Phase 28 — Result Handling

If job results are stored, inspect:

```text
result persistence
TTL
consumer expectations
large result payload
```

Do not require storing results when unnecessary.

---

# Phase 29 — Error Classification

Differentiate:

```text
TRANSIENT
PERMANENT
UNKNOWN
```

Examples:

```text
HTTP timeout
→ potentially transient

invalid email format
→ permanent
```

Retry logic should respect this distinction.

---

# Phase 30 — External API Calls

For jobs calling external systems, inspect:

```text
timeouts
retries
idempotency
rate limits
authentication
```

Security issues should be handed to `security-review`.

---

# Phase 31 — Rate Limits

Retries can amplify API rate limits.

Example:

```text
100 failed jobs
×
5 retries
=
500 requests
```

Potential retry storms should be considered.

---

# Phase 32 — Poison Messages

Inspect whether malformed messages can repeatedly fail.

Ask:

```text
Will one invalid message retry forever?
```

Look for final-failure handling.

---

# Phase 33 — Observability

Review whether operators can understand:

```text
job started
job completed
job failed
retry scheduled
processing duration
queue backlog
```

Do not require excessive logging.

Focus on diagnosability.

---

# Phase 34 — Structured Logging

Useful context may include:

```text
job_id
correlation_id
tenant_id
resource_id
attempt
queue
```

Avoid logging secrets or sensitive payloads.

Coordinate with `security-review`.

---

# Phase 35 — Metrics

Consider metrics such as:

```text
queue depth
processing time
failure count
retry count
worker availability
```

Only report missing observability when operational impact is significant.

---

# Phase 36 — Traceability

For distributed workflows, correlation IDs may improve traceability.

Example:

```text
HTTP request
→ job
→ worker
→ external API
```

Use existing observability conventions.

---

# Phase 37 — RQ-Specific Review

When RQ is detected, inspect:

```text
Queue(...)
enqueue(...)
job_timeout
Retry
FailedJobRegistry
ScheduledJobRegistry
Worker
```

Questions:

```text
Is job_timeout configured?

Is Retry used where transient failure is expected?

Can failed jobs be discovered?

Is is_async=False used only in testing?
```

---

# Phase 38 — Celery-Specific Review

When Celery is detected, inspect:

```text
acks_late
autoretry_for
retry_backoff
max_retries
task_time_limit
soft_time_limit
routing
```

Consider delivery semantics before reporting.

---

# Phase 39 — RabbitMQ-Specific Review

Inspect:

```text
acknowledgement
nack
requeue
DLX
prefetch
durability
```

Potential issues:

```text
ack before processing
infinite requeue
```

---

# Phase 40 — Kafka-Specific Review

Inspect:

```text
consumer groups
partition keys
offset commit
ordering
reprocessing
schema compatibility
```

Potential issue:

```text
offset committed before durable processing
```

Only report with framework evidence.

---

# Phase 41 — Queue Tests

Identify existing tests for:

```text
enqueue
execution
retry
timeout
failure
duplicate execution
idempotency
```

Missing scenarios should be handed to `test-impact`.

---

# Phase 42 — Deterministic Verification

When practical, verify using:

```text
synchronous worker mode
isolated Redis/broker
synthetic messages
testcontainers
framework test utilities
```

For RQ, synchronous execution may be useful:

```python
Queue(
    connection=redis_connection,
    is_async=False
)
```

Do not use production queues.

---

# Finding Categories

Use:

```text
IDEMPOTENCY
DUPLICATE_EXECUTION
RETRY_POLICY
RETRY_SAFETY
TIMEOUT
QUEUE_ROUTING
FAILURE_HANDLING
DEAD_LETTER
TRANSACTIONAL_MESSAGING
ORDERING
CONCURRENCY
SERIALIZATION
SCHEDULING
POISON_MESSAGE
OBSERVABILITY
WORKER_CAPACITY
```

---

# Severity Guidance

## CRITICAL

Use rarely.

Examples:

```text
duplicate execution can trigger irreversible high-impact side effects at scale
```

## HIGH

Examples:

```text
payment job is not idempotent
permanent failure retries indefinitely
message can be acknowledged before processing completes
```

## MEDIUM

Examples:

```text
missing timeout can exhaust workers
failed jobs are not operationally visible
important job has no retry for transient failure
```

## LOW

Examples:

```text
minor observability gap
localized queue routing inconsistency
```

---

# Confidence

Use:

```text
CONFIRMED
LIKELY
POTENTIAL
INFORMATIONAL
```

---

# Example Finding

```json
{
  "id": "QUEUE-001",
  "category": "IDEMPOTENCY",
  "severity": "HIGH",
  "confidence": "LIKELY",
  "title": "Payment job can create duplicate charges when retried",
  "description": "The job charges the external payment provider before persisting completion state, and the retry configuration may execute the same job again after a failure.",
  "file": "app/jobs/payment.py",
  "line": 54,
  "evidence": [
    "charge_customer() executes before payment status is committed",
    "the job retries transient exceptions up to three times",
    "no idempotency key is passed to the payment provider"
  ],
  "impact": "A transient failure after the external charge may result in a second charge when the job is retried.",
  "recommendation": "Use an idempotency mechanism around the external payment operation and add a retry regression test.",
  "verification_status": "UNVERIFIED",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/queue-review.json
```

Optionally:

```text
reports/findings/<pr-id>/queue-review.md
```

---

# Metrics

Record:

```text
async_components_reviewed
producers_reviewed
consumers_reviewed
jobs_reviewed
queues_reviewed

retry_policies_reviewed
timeouts_reviewed
idempotency_paths_reviewed

retry_findings
timeout_findings
idempotency_findings
duplicate_execution_findings
failure_handling_findings
observability_findings

findings_total
critical_findings
high_findings
medium_findings
low_findings

confirmed_findings
likely_findings
potential_findings

verification_candidates
```

Save:

```text
reports/metrics/<pr-id>-queue-review.json
```

---

# Specialist Handoff

When issues overlap:

```text
cross-tenant job behavior
→ security-review

transaction / locking issue
→ database-review

missing queue tests
→ test-impact

architectural queue coupling
→ architecture-review

message API contract
→ api-review
```

Avoid duplicate findings.

---

# What This Skill Must Not Do

Do not:

* assume every background job needs retries;
* assume every job must be idempotent in the same way;
* require a DLQ when the framework uses another failure mechanism;
* run jobs against production brokers;
* modify queue infrastructure during analysis;
* treat generic async complexity as a defect.

---

# Completion Criteria

The skill is complete when:

* producer and consumer paths are understood;
* message/job lifecycle is mapped;
* retry and timeout behavior are reviewed;
* idempotency is considered;
* duplicate execution risk is considered;
* failure handling is inspected;
* observability is considered when relevant;
* high-value findings are structured;
* verification candidates are identified;
* metrics are persisted.

---

# Human Summary Format

Use:

```text
Queue / Async Review

Technology:
...

Jobs reviewed:
...

Queues / topics reviewed:
...

Retry behavior:
...

Timeout behavior:
...

Idempotency concerns:
...

Findings:
Critical:
High:
Medium:
Low:

Verification candidates:
...
```

---

# Engineering Principle

Asynchronous code should be reviewed according to what can happen during failure, retry, delay, duplication, and partial execution.

The goal is:

> Determine whether the Pull Request remains correct when asynchronous execution behaves imperfectly.