# Change Impact Analysis Skill

## Purpose

This skill analyzes the direct and indirect impact of Pull Request changes across the repository.

Its goal is to identify which components, behaviors, interfaces, tests, consumers, and operational paths may be affected by the modified code.

This skill does not primarily search for defects.

It builds an impact map that helps downstream reviewers focus on the areas most likely to regress.

---

# Core Question

For every meaningful change, determine:

```text
What changed?
    ↓
Who depends on it?
    ↓
What behavior can be affected?
    ↓
What should be reviewed or tested?
```

The output should make hidden dependencies visible.

---

# When to Use

Use this skill when:

* functions or methods are modified;
* public interfaces change;
* database models or schemas change;
* API behavior changes;
* shared services change;
* authentication or authorization logic changes;
* background jobs change;
* configuration changes;
* dependencies change;
* a refactor moves responsibilities;
* common utilities change;
* changes may affect multiple modules.

This skill is especially important for medium and large Pull Requests.

---

# Inputs

The skill may consume:

* `pr-context.json`;
* repository path;
* changed files;
* changed symbols;
* diff;
* dependency metadata;
* tests;
* API definitions;
* database models;
* queue definitions;
* project structure.

Recommended input:

```text
reports/raw/<pr-id>/pr-context.json
```

---

# Phase 1 — Identify Impact Roots

Start from the changed symbols identified by `pr-understanding`.

Impact roots may include:

* functions;
* methods;
* classes;
* modules;
* routes;
* database models;
* schemas;
* configuration values;
* queue jobs;
* shared utilities;
* public constants.

Example:

```text
Impact Roots

AuthService.validate_token()
User.organization_id
POST /api/v1/users
send_email_job()
```

Do not begin with repository-wide dependency exploration.

---

# Phase 2 — Determine Symbol Visibility

Classify changed symbols as:

```text
PRIVATE
MODULE_INTERNAL
PACKAGE_INTERNAL
PUBLIC
EXTERNAL_INTERFACE
```

Examples:

```text
_private_helper()
PRIVATE

UserService.create()
PACKAGE_INTERNAL

GET /api/v1/users
EXTERNAL_INTERFACE
```

Public and external interfaces generally require broader impact analysis.

---

# Phase 3 — Identify Direct Dependents

Find code that directly depends on the changed symbol.

Examples:

```text
callers
imports
inheritance
composition
route registration
dependency injection
ORM relationships
schema references
job invocation
```

Example:

```text
Changed:
AuthService.validate_token()

Direct dependents:
- auth_middleware()
- websocket_auth()
- admin_required()
```

Record file and symbol when possible.

---

# Phase 4 — Identify Indirect Dependents

Trace one or more dependency levels when useful.

Example:

```text
AuthService.validate_token()
        ↓
auth_middleware()
        ↓
7 API endpoints
```

Do not recursively traverse the entire repository without limits.

Prioritize dependencies that influence observable behavior.

---

# Phase 5 — Build an Impact Graph

Represent significant relationships.

Example:

```text
validate_token()
    ↓
auth_middleware()
    ├── GET /users
    ├── POST /users
    ├── DELETE /users/{id}
    └── GET /reports
```

Machine-readable representation may be:

```json
{
  "source": "AuthService.validate_token",
  "direct_dependents": [
    "auth_middleware"
  ],
  "indirect_dependents": [
    "GET /users",
    "POST /users",
    "DELETE /users/{id}",
    "GET /reports"
  ]
}
```

---

# Phase 6 — Analyze API Impact

When changed code affects APIs, determine:

* endpoints affected;
* HTTP methods affected;
* authentication requirements;
* authorization behavior;
* request schemas;
* response schemas;
* status codes;
* external clients.

Example:

```text
Changed:
UserSerializer

Affected endpoints:
GET /users
GET /users/{id}
POST /users
```

A serializer change may affect multiple endpoints even when route files were not modified.

---

# Phase 7 — Analyze Database Impact

When changed code touches persistence, identify:

* affected tables;
* models;
* relationships;
* migrations;
* constraints;
* indexes;
* queries;
* transactions.

Example:

```text
Changed:
User.organization_id nullable → required

Potentially affected:
- user creation
- imports
- test fixtures
- seed scripts
- migration of existing records
```

Pass this context to `database-review`.

---

# Phase 8 — Analyze Authentication and Authorization Impact

For auth-related changes, determine:

```text
which entry points use the modified logic
which roles are affected
which resources are affected
which tenants are affected
```

Example:

```text
Changed:
has_permission()

Affected:
- admin routes
- billing routes
- organization settings
```

This should trigger broader security and test analysis.

---

# Phase 9 — Analyze Queue and Async Impact

For async changes, identify:

* producers;
* consumers;
* workers;
* scheduled tasks;
* retries;
* downstream services;
* persistence changes;
* notification paths.

Example:

```text
Changed:
generate_report()

Called by:
POST /reports

Executed by:
RQ worker

Writes:
reports table

Notifies:
email service
```

This impact chain is more useful than only identifying the changed job file.

---

# Phase 10 — Analyze Configuration Impact

If configuration changes, identify consumers.

Example:

```text
Changed:
API_TIMEOUT

Consumers:
- external_api_client.py
- report_service.py
- sync_worker.py
```

Configuration changes can have broad runtime impact even when few files are changed.

---

# Phase 11 — Analyze Dependency Changes

When package dependencies change, identify:

```text
imports
usage locations
public APIs used
behavior-sensitive integrations
```

Example:

```text
Dependency:
PyJWT upgraded

Used by:
auth/token.py
auth/api_key.py

Risk:
token decoding behavior may change
```

This is impact mapping, not vulnerability analysis.

---

# Phase 12 — Identify Affected Tests

Map changed behavior to existing tests.

Example:

```text
Changed:
UserService.create()

Related tests:
tests/test_user_service.py
tests/test_users_api.py
tests/test_permissions.py
```

Also identify tests that may require updates even if unchanged in the PR.

---

# Phase 13 — Identify Missing Test Relationships

Detect situations like:

```text
Production code changed
but related tests were not modified
```

This is not automatically a defect.

Record it as a test-impact signal.

Example:

```text
Change impact signal:

AuthService.validate_token() changed.

Related tests:
12

Modified tests:
0
```

Pass to `test-impact`.

---

# Phase 14 — Detect Public Contract Changes

Determine whether the PR affects:

```text
function signatures
class interfaces
API endpoints
event payloads
queue messages
configuration formats
database schemas
CLI behavior
```

Classify:

```text
NO_PUBLIC_CHANGE
BACKWARD_COMPATIBLE_CHANGE
POTENTIAL_BREAKING_CHANGE
BREAKING_CHANGE
UNCERTAIN
```

Do not claim a breaking change without evidence.

---

# Phase 15 — Detect Removed Behavior

Pay special attention to removals.

Examples:

```text
deleted validation
removed argument
removed endpoint
removed config
removed database field
removed retry
```

Removal can produce impact that is not obvious from added code.

---

# Phase 16 — Identify State Transition Impact

For stateful systems, detect changes affecting transitions.

Example:

```text
PENDING
  ↓
PROCESSING
  ↓
COMPLETED
```

If PR adds:

```text
CANCELLED
```

identify:

```text
services using state
queries filtering state
UI assumptions
queue behavior
tests
```

---

# Phase 17 — Identify Cross-Cutting Concerns

Determine whether changes affect:

```text
logging
metrics
tracing
authorization
transactions
caching
rate limiting
error handling
```

Example:

```text
Shared exception handler modified

Affected:
all API endpoints
```

Cross-cutting changes require broader review.

---

# Phase 18 — Detect Change Amplification

Some small diffs have large impact.

Example:

```text
1 line changed
```

in:

```text
authorization middleware
```

may affect dozens of endpoints.

Record:

```text
CHANGE_AMPLIFICATION
```

when the observable impact is much larger than the diff size suggests.

---

# Phase 19 — Detect Isolated Changes

Also identify truly local changes.

Example:

```text
Formatting helper used only by one report
```

Output:

```text
Impact scope:
LOCAL
```

This helps avoid unnecessary reviewers.

---

# Impact Scope Classification

Classify overall impact as:

```text
LOCAL
MODULE
CROSS_MODULE
SYSTEM_WIDE
EXTERNAL
```

Definitions:

### LOCAL

Only the modified component is affected.

### MODULE

Multiple symbols within the same module or feature are affected.

### CROSS_MODULE

Multiple application modules depend on the change.

### SYSTEM_WIDE

Cross-cutting infrastructure or behavior is affected.

### EXTERNAL

Public or integration contracts are affected.

Multiple scopes may apply.

---

# Phase 20 — Identify Review Expansion Needs

Based on impact, recommend additional reviewers.

Examples:

```text
Database relationship impacted
→ database-review

Public API impacted
→ api-review

Authorization path impacted
→ security-review

Queue consumer impacted
→ queue-review

Many modules affected
→ architecture-review
```

Do not recommend specialists without impact evidence.

---

# Required Output

Generate:

```text
reports/raw/<pr-id>/change-impact.json
```

Optionally:

```text
reports/raw/<pr-id>/change-impact.md
```

The JSON file is canonical.

---

# Recommended JSON Structure

```json
{
  "pr_id": "42",

  "impact_roots": [
    {
      "file": "app/auth/service.py",
      "symbol": "AuthService.validate_token",
      "visibility": "PACKAGE_INTERNAL"
    }
  ],

  "impact_scope": [
    "CROSS_MODULE"
  ],

  "dependencies": [
    {
      "source": "AuthService.validate_token",
      "direct_dependents": [
        "auth_middleware"
      ],
      "indirect_dependents": [
        "GET /users",
        "POST /users",
        "GET /reports"
      ]
    }
  ],

  "affected_tests": [
    "tests/test_auth.py",
    "tests/test_permissions.py"
  ],

  "public_contracts": {
    "affected": true,
    "classification": "BACKWARD_COMPATIBLE_CHANGE"
  },

  "risk_signals": [
    "authorization_path_changed",
    "shared_middleware_changed"
  ],

  "recommended_reviewers": [
    "security-review",
    "test-impact",
    "api-review"
  ]
}
```

Do not invent relationships that cannot be supported.

---

# Metrics

Produce:

```text
impact_roots
direct_dependents
indirect_dependents
affected_modules
affected_endpoints
affected_jobs
affected_models
affected_tests
public_contracts_affected
cross_cutting_changes
recommended_reviewers
```

Save:

```text
reports/metrics/<pr-id>-change-impact.json
```

---

# Impact Evidence

Each important relationship should include evidence when practical.

Example:

```text
Changed:
AuthService.validate_token()

Dependent:
auth_middleware()

Evidence:
app/api/middleware.py imports AuthService and calls validate_token()
```

Do not rely only on naming similarity.

---

# Confidence Classification

Use:

```text
CONFIRMED
LIKELY
POTENTIAL
```

Examples:

### CONFIRMED

Direct static reference exists.

### LIKELY

Framework behavior strongly implies dependency.

### POTENTIAL

Relationship is inferred but cannot be verified.

---

# Repository History

Git history may be consulted when useful to understand:

* why code is structured a certain way;
* which modules change together;
* whether the modified symbol is historically sensitive.

Do not use historical activity as proof of a defect.

---

# Framework Awareness

Adapt analysis to framework conventions.

Examples:

## Flask

Inspect:

```text
route decorators
Blueprint registration
application factories
middleware
extensions
```

## Django

Inspect:

```text
URLs
views
models
signals
middleware
serializers
```

## FastAPI

Inspect:

```text
routers
dependencies
Pydantic models
security dependencies
```

Use framework-specific relationships only when detected.

---

# Avoid Over-Expansion

Do not keep traversing dependencies indefinitely.

Stop when:

* observable affected behavior is identified;
* reviewer selection is clear;
* additional traversal produces little new value.

Prefer focused impact maps.

---

# What This Skill Must Not Do

Do not:

* generate final defect findings;
* assign final severity;
* publish GitHub comments;
* modify production code;
* perform full security review;
* perform complete test generation;
* run destructive commands.

Its role is impact mapping.

---

# Completion Criteria

This skill is complete when:

* impact roots are identified;
* direct dependents are mapped;
* relevant indirect dependents are mapped;
* affected tests are identified;
* public contracts are classified;
* impact scope is classified;
* cross-cutting changes are detected;
* reviewer expansion needs are identified;
* metrics are persisted.

---

# Human Summary Format

Use:

```text
Change Impact

Impact roots:
...

Scope:
...

Direct dependents:
...

Indirect dependents:
...

Affected APIs:
...

Affected tests:
...

Public contract impact:
...

Recommended reviewers:
...
```

Keep human output concise.

Store detailed dependency mappings in JSON.

---

# Engineering Principle

A Pull Request should not be evaluated only by the number of files or lines it changes.

A one-line change in a shared authorization function may have greater impact than a 500-line isolated feature.

The goal of this skill is therefore:

> Measure the behavioral reach of the change, not merely the size of the diff.