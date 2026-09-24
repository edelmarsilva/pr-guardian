# Database Review Skill

## Purpose

This skill reviews Pull Request changes that affect database schemas, ORM models, migrations, queries, transactions, constraints, indexes, and persistence behavior.

Its goal is to identify defects or regression risks introduced by the Pull Request that may affect:

* data integrity;
* correctness;
* performance;
* migration safety;
* transactional consistency;
* compatibility with existing data.

The review must remain focused on the Pull Request.

---

# Core Principle

Do not review database code in isolation.

Always consider:

```text
schema
  ↓
data
  ↓
application behavior
  ↓
migration
  ↓
runtime queries
```

A schema change that looks valid syntactically may still break existing data or application assumptions.

---

# When to Use

Use this skill when a Pull Request changes:

* ORM models;
* database migrations;
* SQL queries;
* indexes;
* constraints;
* foreign keys;
* nullability;
* transaction handling;
* repositories;
* persistence services;
* table relationships;
* query filters;
* pagination;
* locking;
* bulk operations.

---

# Inputs

Recommended inputs:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
```

plus:

* repository path;
* changed model files;
* migrations;
* SQL;
* repository/data-access files;
* database configuration;
* related tests.

---

# Phase 1 — Identify Database Technology

Determine which persistence technology is used.

Examples:

```text
PostgreSQL
MySQL
MariaDB
SQLite
SQL Server
MongoDB
Redis
```

For ORM-based projects, identify:

```text
SQLAlchemy
Django ORM
Peewee
Tortoise ORM
Prisma
Hibernate
```

Database-specific behavior matters.

Do not assume SQLite semantics represent PostgreSQL behavior.

---

# Phase 2 — Identify Changed Persistence Components

Classify changed files as:

```text
MODEL
MIGRATION
QUERY
REPOSITORY
TRANSACTION
DATABASE_CONFIG
SEED
FIXTURE
```

Example:

```text
app/models/user.py
MODEL

migrations/20260924_add_org_id.py
MIGRATION

app/repositories/user.py
QUERY
REPOSITORY
```

---

# Phase 3 — Model Changes

Inspect changes to:

* fields;
* types;
* defaults;
* relationships;
* uniqueness;
* nullability;
* indexes;
* cascade rules.

Example:

```text
User.organization_id

Before:
nullable=True

After:
nullable=False
```

Ask:

```text
What happens to existing rows?
```

---

# Phase 4 — Nullability Changes

Pay special attention to:

```text
nullable → required
required → nullable
```

Potential risks:

```text
migration failure
existing invalid data
unexpected application nulls
missing backfill
```

A non-null change without migration strategy is a strong finding candidate.

---

# Phase 5 — Type Changes

Inspect type changes such as:

```text
string → integer
integer → UUID
text → enum
datetime → timestamp with timezone
```

Consider:

```text
existing data conversion
precision loss
length constraints
application compatibility
index behavior
```

---

# Phase 6 — Default Values

Check new or modified defaults.

Example:

```text
status DEFAULT 'ACTIVE'
```

Questions:

```text
Should existing rows receive this value?

Is the default valid for every existing record?

Is application behavior relying on a different default?
```

---

# Phase 7 — Unique Constraints

Inspect:

```text
unique=True
UNIQUE indexes
composite uniqueness
```

Potential risks:

```text
existing duplicate data
wrong uniqueness scope
cross-tenant collisions
```

Example:

```text
UNIQUE(email)
```

may be wrong if uniqueness should be:

```text
UNIQUE(organization_id, email)
```

Use domain context.

---

# Phase 8 — Foreign Keys

Review:

* target table;
* nullability;
* delete behavior;
* update behavior;
* cascade settings.

Examples:

```text
ON DELETE CASCADE
ON DELETE SET NULL
ON DELETE RESTRICT
```

Ask whether deletion behavior matches application expectations.

---

# Phase 9 — Cascades

Cascade behavior deserves special attention.

Potentially dangerous:

```text
User deletion
  ↓
CASCADE
  ↓
Orders
  ↓
Audit logs
```

Do not assume cascade is correct merely because the migration applies.

---

# Phase 10 — Index Analysis

Inspect indexes added, removed, or implied by new queries.

Look for:

```text
frequently filtered columns
join columns
foreign keys
ordering columns
tenant scope columns
```

Potential missing index:

```python
User.query.filter_by(
    organization_id=org_id,
    email=email
)
```

may benefit from a composite index depending on usage and scale.

Do not report every unindexed filter as a defect.

---

# Phase 11 — Redundant Indexes

Also inspect whether new indexes duplicate existing ones.

Example:

```text
INDEX(email)
UNIQUE(email)
```

may be redundant depending on database behavior.

Database-specific evidence is required.

---

# Phase 12 — Migration Safety

Review whether migrations are safe for existing data.

Consider:

```text
table rewrite
long lock
non-null addition
column type conversion
column removal
large data update
index creation
```

Distinguish development convenience from production safety.

---

# Phase 13 — Destructive Migrations

Look for:

```text
DROP COLUMN
DROP TABLE
TRUNCATE
data rewrite
```

Questions:

```text
Is data intentionally discarded?

Is backward compatibility required?

Is rollback possible?
```

Destructive changes should be explicitly documented.

---

# Phase 14 — Migration Ordering

Check dependency order.

Example:

```text
code expects column
before migration creates it
```

or:

```text
migration removes field
while old application version still uses it
```

This matters for rolling deployments.

---

# Phase 15 — Expand/Contract Migrations

When zero-downtime deployment matters, prefer compatible sequencing.

Concept:

```text
EXPAND
  ↓
deploy compatible code
  ↓
migrate data
  ↓
CONTRACT
```

Do not require this pattern for every project.

Use deployment context.

---

# Phase 16 — Migration Rollback

Inspect whether rollback logic:

* exists;
* is safe;
* preserves data;
* is realistically reversible.

Some migrations are intentionally irreversible.

If so, this should be explicit.

---

# Phase 17 — Raw SQL

Inspect raw SQL for:

```text
correctness
parameters
joins
filter conditions
grouping
ordering
locking
```

Security-sensitive SQL injection belongs primarily to `security-review`.

Database correctness remains in scope.

---

# Phase 18 — Missing Filters

A common regression pattern is missing scope filters.

Example:

```python
Invoice.query.filter_by(id=invoice_id).first()
```

when repository convention requires:

```text
organization_id
```

This may overlap with authorization concerns.

Coordinate with `security-review` when tenant isolation is involved.

---

# Phase 19 — N+1 Queries

Look for loops that trigger repeated database queries.

Example:

```python
for user in users:
    print(user.orders.count())
```

Potential result:

```text
1 query for users
N queries for orders
```

Verify ORM loading behavior before reporting.

---

# Phase 20 — Eager and Lazy Loading

Inspect relationship-loading changes.

Potential issues:

```text
unexpected N+1
loading huge relationship graphs
detached-instance errors
```

Do not demand eager loading everywhere.

---

# Phase 21 — Pagination

Review:

```text
LIMIT
OFFSET
cursor pagination
ordering
```

Potential defects:

```text
pagination without deterministic ORDER BY
duplicate rows across pages
missing maximum page size
```

API-specific behavior may also involve `api-review`.

---

# Phase 22 — Query Semantics

Inspect changes involving:

```text
INNER JOIN
LEFT JOIN
EXISTS
IN
GROUP BY
DISTINCT
```

Check whether result semantics changed unintentionally.

Example:

Changing:

```text
LEFT JOIN
```

to:

```text
INNER JOIN
```

may exclude valid records.

---

# Phase 23 — Transaction Boundaries

Identify:

```text
begin
commit
rollback
```

Determine ownership.

Potential issue:

```text
repository commits
service expects atomic multi-step transaction
```

Transaction boundaries should reflect the logical unit of work.

---

# Phase 24 — Partial Commit Risks

Example:

```text
create invoice
commit

create items
commit
```

If item creation fails, invoice may remain partially created.

Review whether atomicity is required.

---

# Phase 25 — Exception and Rollback Handling

Inspect whether transaction failures trigger:

```text
rollback
cleanup
compensation
```

Potential issue:

```python
try:
    db.session.add(item)
    db.session.commit()
except Exception:
    return False
```

without rollback may leave session unusable.

---

# Phase 26 — Concurrency

Look for:

```text
check-then-insert
read-modify-write
counters
inventory
balance updates
```

Potential race:

```python
if not exists(email):
    create(email)
```

Database uniqueness may be the correct enforcement mechanism.

---

# Phase 27 — Locking

If explicit locking changes, inspect:

```text
SELECT ... FOR UPDATE
advisory locks
optimistic locking
version columns
```

Consider:

```text
deadlock risk
lock duration
lock ordering
```

---

# Phase 28 — Optimistic Concurrency

When version fields exist, verify updates preserve them.

Example:

```text
version
updated_at
ETag
```

A PR bypassing optimistic concurrency can reintroduce lost updates.

---

# Phase 29 — Bulk Operations

Inspect:

```text
bulk insert
bulk update
bulk delete
```

Potential concerns:

```text
hooks bypassed
ORM events skipped
validation bypassed
large transaction
```

Framework-specific behavior matters.

---

# Phase 30 — ORM Event Behavior

When ORM lifecycle hooks are used, inspect whether new query methods bypass them.

Examples:

```text
before_insert
after_update
signals
listeners
```

Bulk operations often behave differently.

---

# Phase 31 — Soft Delete

If soft deletion exists, check whether new queries respect it.

Example:

```text
deleted_at IS NULL
```

Potential regression:

```text
new query returns archived/deleted records
```

---

# Phase 32 — Audit Fields

Inspect consistency of:

```text
created_at
updated_at
created_by
updated_by
```

Do not report minor omissions unless auditability matters in the application.

---

# Phase 33 — Timezone Handling

Database datetime changes should consider:

```text
timestamp
timestamp with timezone
UTC storage
application timezone
```

Avoid naive/aware mismatches.

---

# Phase 34 — Numeric Precision

For financial or precise numeric fields, inspect changes involving:

```text
FLOAT
DOUBLE
DECIMAL
NUMERIC
```

Avoid floating-point storage for exact monetary values unless explicitly intended.

---

# Phase 35 — JSON Fields

When JSON/JSONB fields change, inspect:

```text
schema assumptions
indexing
queryability
validation
```

Do not assume JSON flexibility is harmless if application code expects structure.

---

# Phase 36 — Enum Changes

Inspect:

```text
new enum value
removed enum value
renamed enum value
```

Potential impact:

```text
existing records
application mapping
migration compatibility
```

---

# Phase 37 — Seed and Fixture Changes

Check whether seed data remains compatible with:

```text
new required fields
new constraints
new relationships
```

Broken fixtures can reveal migration incompatibility.

---

# Phase 38 — Test Database Fidelity

Determine whether tests use the same database engine as production.

Example:

```text
Production:
PostgreSQL

Tests:
SQLite
```

Record limitations when changed behavior relies on:

```text
JSONB
arrays
locking
constraints
PostgreSQL SQL syntax
```

This may become a test-impact finding.

---

# Phase 39 — PostgreSQL-Specific Review

When PostgreSQL is detected, consider:

```text
JSONB
GIN/GiST indexes
partial indexes
concurrent index creation
transaction isolation
sequences
generated columns
```

Do not apply PostgreSQL-specific recommendations to other engines.

---

# Phase 40 — Query Performance With Functional Impact

Report performance findings when they may materially affect system behavior.

Examples:

```text
new unbounded full-table query
N+1 in high-volume endpoint
large synchronous aggregation
```

Avoid speculative micro-optimization.

---

# Finding Categories

Use:

```text
SCHEMA_COMPATIBILITY
MIGRATION_SAFETY
DATA_INTEGRITY
NULLABILITY
CONSTRAINT
FOREIGN_KEY
CASCADE
INDEX
N_PLUS_ONE
QUERY_CORRECTNESS
TRANSACTION
PARTIAL_COMMIT
CONCURRENCY
LOCKING
PAGINATION
TYPE_CONVERSION
PRECISION
SOFT_DELETE
DATABASE_COMPATIBILITY
```

---

# Severity Guidance

## CRITICAL

Use rarely.

Examples:

```text
migration can irreversibly destroy core production data
```

## HIGH

Examples:

```text
new migration fails on existing valid rows
cross-tenant query returns unrelated data
non-atomic financial update can corrupt balances
```

## MEDIUM

Examples:

```text
N+1 query on a meaningful endpoint
missing rollback path
pagination instability
```

## LOW

Examples:

```text
minor redundant index
localized persistence inconsistency
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
  "id": "DB-001",
  "category": "MIGRATION_SAFETY",
  "severity": "HIGH",
  "confidence": "CONFIRMED",
  "title": "Required organization_id is added without backfilling existing users",
  "description": "The migration adds organization_id as NOT NULL immediately, but existing user rows do not currently have this value.",
  "file": "migrations/20260924_add_organization_id.py",
  "line": 18,
  "evidence": [
    "organization_id is created with nullable=False",
    "the migration does not populate existing rows before applying the constraint",
    "existing User fixtures contain records without organization_id"
  ],
  "impact": "The migration may fail when applied to a database containing existing users.",
  "recommendation": "Use a staged migration: add the field as nullable, backfill existing records, then apply the NOT NULL constraint.",
  "verification_status": "VERIFIED",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# Deterministic Verification

When practical, verify database findings with:

```text
migration execution
database integration tests
EXPLAIN
EXPLAIN ANALYZE
constraint tests
transaction tests
```

Use isolated databases only.

Never run destructive verification against production.

---

# EXPLAIN Usage

For significant query changes, consider:

```sql
EXPLAIN
SELECT ...
```

Use:

```text
EXPLAIN ANALYZE
```

only in safe test environments because it executes the query.

Preserve relevant output.

---

# Migration Verification

Suggested workflow:

```text
create isolated database
        ↓
apply previous migrations
        ↓
load synthetic representative data
        ↓
apply PR migration
        ↓
run integrity checks
```

This is strong verification evidence.

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/database-review.json
```

Optionally:

```text
reports/findings/<pr-id>/database-review.md
```

---

# Metrics

Record:

```text
models_reviewed
migrations_reviewed
queries_reviewed

schema_changes
constraints_added
constraints_removed
indexes_added
indexes_removed

transaction_changes
n_plus_one_candidates
migration_safety_findings
data_integrity_findings

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
reports/metrics/<pr-id>-database-review.json
```

---

# Specialist Handoff

When findings overlap:

```text
tenant data exposure
→ security-review

missing database tests
→ test-impact

API pagination contract
→ api-review

transaction ownership across layers
→ architecture-review
```

Avoid duplicate reporting.

---

# What This Skill Must Not Do

Do not:

* optimize every query;
* redesign the schema without need;
* run destructive migrations against production;
* require indexes without evidence;
* assume every raw SQL statement is insecure;
* conflate performance preferences with correctness defects;
* modify migrations automatically during analysis.

---

# Completion Criteria

The skill is complete when:

* model changes are reviewed;
* migration safety is evaluated;
* constraints and indexes are considered;
* query correctness is reviewed;
* transaction boundaries are inspected;
* concurrency-sensitive changes are considered;
* high-value findings are structured;
* verification candidates are identified;
* metrics are persisted.

---

# Human Summary Format

Use:

```text
Database Review

Database technology:
...

Models reviewed:
...

Migrations reviewed:
...

Schema changes:
...

Findings:
Critical:
High:
Medium:
Low:

Primary risks:
...

Verification candidates:
...
```

---

# Engineering Principle

Database review should answer:

> Can this Pull Request safely preserve the meaning, integrity, and accessibility of existing data while supporting the new behavior?

The goal is not database perfection.

The goal is safe evolution of persistent state.