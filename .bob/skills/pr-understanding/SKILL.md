# PR Understanding Skill

## Purpose

This skill analyzes a Pull Request and builds a structured understanding of its intent, scope, changed components, and likely technical impact.

It is the first analysis step in the PR Guardian workflow.

Its responsibility is not primarily to discover defects.

Its responsibility is to create an accurate and reusable context package that allows downstream reviewers to perform focused analysis without repeatedly rediscovering the Pull Request structure.

---

# Core Objective

Transform:

```text
Pull Request
+
diff
+
repository context
```

into:

```text
structured PR context
```

containing:

* declared intent;
* actual implementation scope;
* changed files;
* changed symbols;
* affected technical domains;
* related repository components;
* test changes;
* potential risk triggers;
* recommended specialist reviewers.

---

# When to Use

Use this skill:

* at the beginning of every non-trivial Pull Request review;
* before security review;
* before test-impact analysis;
* before architecture review;
* before database review;
* before API review;
* before queue review;
* when the PR description is incomplete or unclear;
* when many files have changed;
* when understanding repository context is necessary.

This skill may be skipped only for extremely trivial changes where intent and scope are obvious.

Examples:

* typo correction;
* comment-only change;
* simple documentation update.

Even in those cases, verify that no code behavior changed.

---

# Primary Principle

Do not assume that the Pull Request description accurately represents the implementation.

Compare:

```text
DECLARED INTENT
      vs
ACTUAL CHANGE
```

The final context must identify discrepancies when they exist.

---

# Inputs

The skill may consume:

* repository path;
* Pull Request number;
* PR title;
* PR description;
* base branch;
* head branch;
* commit list;
* changed files;
* diff;
* repository structure;
* existing tests;
* project configuration.

When GitHub metadata is unavailable, derive as much context as possible from local Git state.

---

# Phase 1 — Read Pull Request Metadata

Collect:

```text
PR number
title
description
author
base branch
head branch
commit count
changed file count
lines added
lines removed
```

Do not treat author identity as relevant to code quality.

The review must focus on technical evidence.

---

# Phase 2 — Understand Declared Intent

Extract the stated objective from:

* title;
* description;
* linked technical explanation if locally available;
* commit messages.

Summarize the intended change.

Example:

```text
Declared Intent

Add API-key authentication for external integrations while
maintaining existing JWT authentication for human users.
```

Avoid copying large amounts of PR description verbatim.

Produce a concise technical summary.

---

# Phase 3 — Inspect Commit History

Review commits associated with the Pull Request.

Identify:

* major implementation stages;
* refactors;
* fixes added after initial implementation;
* tests added later;
* migration commits;
* documentation changes.

Example:

```text
Commits

1. add API key model
2. add authentication middleware
3. fix tenant validation
4. add integration tests
```

Commit history may reveal intent that is not obvious from the final diff.

Do not assume each commit represents a valid final design.

---

# Phase 4 — Classify Changed Files

Classify each changed file.

Suggested categories:

```text
APPLICATION_CODE
TEST
DATABASE
MIGRATION
API
CONFIGURATION
DEPENDENCY
DOCUMENTATION
CI_CD
INFRASTRUCTURE
SECURITY
QUEUE
OBSERVABILITY
UNKNOWN
```

Example:

```text
app/auth/api_key.py
APPLICATION_CODE
SECURITY

app/models/api_key.py
DATABASE

tests/test_api_key.py
TEST

openapi.yaml
API
DOCUMENTATION
```

A file may belong to multiple categories.

---

# Phase 5 — Detect Changed Symbols

When practical, identify changed:

* functions;
* methods;
* classes;
* modules;
* routes;
* database models;
* schemas;
* jobs;
* workers;
* configuration values.

Example:

```text
Changed Symbols

AuthService.validate_api_key()
ApiKey.create()
ApiKey.revoke()
api_key_required()
POST /api/v1/keys
```

Prefer symbol-level understanding over merely listing files.

---

# Phase 6 — Determine Change Type

Classify each significant change as one or more of:

```text
ADDED
MODIFIED
REMOVED
RENAMED
MOVED
REFACTORED
BEHAVIOR_CHANGED
CONTRACT_CHANGED
CONFIG_CHANGED
DEPENDENCY_CHANGED
```

Example:

```text
AuthService.authenticate()
MODIFIED
BEHAVIOR_CHANGED

POST /api/v1/keys
ADDED
CONTRACT_CHANGED
```

---

# Phase 7 — Identify Technical Domains

Determine which engineering domains are affected.

Possible domains:

```text
BUSINESS_LOGIC
AUTHENTICATION
AUTHORIZATION
SECURITY
API
DATABASE
MIGRATION
BACKGROUND_JOB
QUEUE
CONFIGURATION
DEPENDENCY
TESTING
ARCHITECTURE
OBSERVABILITY
PERFORMANCE
CI_CD
DOCUMENTATION
```

Only select domains supported by evidence.

---

# Phase 8 — Detect Risk Triggers

Identify signals that should influence reviewer selection.

Examples:

## Authentication

Triggers:

```text
login
token
JWT
session
API key
credential
password
middleware
```

Recommended reviewers:

```text
security-review
test-impact
code-review
```

---

## Authorization

Triggers:

```text
role
permission
tenant
organization
ownership
access control
```

Recommended reviewers:

```text
security-review
test-impact
```

---

## Database

Triggers:

```text
model
migration
SQL
ORM
transaction
index
constraint
```

Recommended reviewers:

```text
database-review
test-impact
```

---

## API

Triggers:

```text
route
endpoint
serializer
schema
OpenAPI
HTTP
```

Recommended reviewers:

```text
api-review
test-impact
```

---

## Queue / Async

Triggers:

```text
RQ
Celery
worker
job
queue
Kafka
RabbitMQ
async
scheduler
```

Recommended reviewers:

```text
queue-review
test-impact
```

---

# Phase 9 — Inspect Related Repository Context

Do not stop at changed files.

Identify directly related files when they materially affect understanding.

Possible related context:

```text
caller
callee
service
repository
model
test
schema
configuration
migration
worker
OpenAPI definition
```

Example:

PR changes:

```text
app/auth/service.py
```

Relevant context may include:

```text
app/api/middleware.py
app/models/user.py
tests/test_auth.py
openapi.yaml
```

Do not recursively inspect the entire repository without a reason.

---

# Phase 10 — Detect Existing Tests

Find tests related to changed behavior.

Record:

```text
existing tests
modified tests
new tests
potentially affected tests
```

Example:

```text
Existing Related Tests

tests/test_auth.py
tests/test_api_permissions.py

Modified by PR:
tests/test_auth.py

Not modified:
tests/test_api_permissions.py
```

This information is passed to the `test-impact` reviewer.

---

# Phase 11 — Compare Intent With Implementation

Explicitly compare:

```text
declared intent
        vs
actual implementation
```

Possible result:

```text
Intent Alignment: PARTIAL

Declared:
Add read-only API keys.

Observed:
The new API key middleware authorizes both GET and POST requests.

Potential mismatch:
Write operations appear to be enabled despite the stated read-only scope.
```

Do not classify this as a confirmed bug yet unless direct evidence exists.

Pass it downstream as an investigation point.

---

# Phase 12 — Detect Unexpected Scope

Look for changes not obviously related to the Pull Request objective.

Examples:

```text
unrelated dependency upgrade
large refactor
configuration change
database migration
authentication behavior change
removed validation
```

Record them under:

```text
Unexpected Scope
```

Example:

```text
Unexpected Scope

requirements.txt upgrades cryptography from 42.x to 46.x.

This change is not mentioned in the PR description.
```

Unexpected does not automatically mean incorrect.

---

# Phase 13 — Identify Public Surface Changes

Determine whether the PR changes externally visible behavior.

Examples:

```text
API route
HTTP response
public function
public class
CLI command
environment variable
database contract
event payload
queue message
configuration format
```

Record:

```text
Public Surface Changes
```

This information is particularly important for breaking-change analysis.

---

# Phase 14 — Identify Configuration Changes

Inspect:

```text
.env.example
config files
Docker files
Compose files
CI definitions
application settings
```

Detect:

* new environment variables;
* removed variables;
* renamed variables;
* changed defaults;
* new service dependencies.

Example:

```text
New configuration:

API_KEY_SECRET

Documentation status:
.env.example updated: YES
README updated: NO
```

---

# Phase 15 — Identify Dependency Changes

Inspect project dependency files.

Examples:

```text
requirements.txt
pyproject.toml
poetry.lock
package.json
pom.xml
go.mod
```

Record:

```text
dependency added
dependency removed
version upgraded
version downgraded
```

Dependency risk evaluation belongs to later reviewers.

This skill only records the change.

---

# Phase 16 — Identify Database Changes

Record whether the Pull Request touches:

```text
ORM models
SQL
schema
migrations
indexes
constraints
transactions
```

Example:

```text
Database Impact Detected

New table:
api_keys

New indexes:
organization_id

Migration:
20260924_add_api_keys.py
```

Pass this information to `database-review`.

---

# Phase 17 — Identify API Changes

Record:

```text
new endpoints
removed endpoints
changed methods
changed request schemas
changed response schemas
changed status codes
changed authentication requirements
```

Example:

```text
API Changes

Added:
POST /api/v1/api-keys

Changed:
GET /api/v1/resources
Authentication now accepts JWT or API Key.
```

---

# Phase 18 — Identify Queue and Async Changes

Record:

```text
new jobs
modified jobs
changed queue selection
retry changes
timeout changes
worker changes
scheduled task changes
```

Example:

```text
Queue Changes

Modified job:
generate_report

Retry:
3 → 5

Timeout:
unchanged
```

Do not evaluate correctness yet.

---

# Phase 19 — Determine Review Complexity

Classify operational review complexity:

```text
SMALL
MEDIUM
LARGE
```

Use repository evidence.

Suggested factors:

```text
number of changed files
cross-module impact
number of technical domains
security sensitivity
public surface change
database migration
async behavior
dependency changes
```

Do not convert this into a quality score.

---

# Phase 20 — Recommend Reviewers

Based on detected domains and triggers, recommend specialists.

Example:

```text
Recommended Reviewers

REQUIRED
- code-review
- security-review
- test-impact
- api-review

OPTIONAL
- architecture-review

NOT REQUIRED
- database-review
- queue-review
```

Provide a short reason for each required reviewer.

---

# Phase 21 — Produce Review Questions

Generate targeted questions for downstream reviewers.

Example:

```text
Security Review Questions

1. Can API keys access resources belonging to another organization?
2. Are revoked keys rejected consistently?
3. Are API keys ever written to logs?

Test Impact Questions

1. Is cross-tenant access tested?
2. Is revoked-key behavior covered?
3. Is malformed-key behavior covered?
```

This is much better than sending a generic instruction such as:

```text
Review this PR for security.
```

---

# Required Output Artifact

Generate:

```text
reports/raw/<pr-id>/pr-context.json
```

and optionally:

```text
reports/raw/<pr-id>/pr-context.md
```

The JSON representation is the canonical machine-readable artifact.

---

# Recommended JSON Structure

Use a structure equivalent to:

```json
{
  "pull_request": {
    "id": "42",
    "title": "Add API key authentication",
    "base": "main",
    "head": "feature/api-keys"
  },

  "intent": {
    "declared": "Add API key authentication for integrations.",
    "observed": "Adds API key model, middleware and management endpoint.",
    "alignment": "ALIGNED"
  },

  "change_summary": {
    "files_changed": 8,
    "lines_added": 214,
    "lines_removed": 31,
    "commits": 4
  },

  "domains": [
    "AUTHENTICATION",
    "AUTHORIZATION",
    "API",
    "DATABASE",
    "TESTING"
  ],

  "risk_triggers": [
    "authentication_boundary_changed",
    "credential_handling_added",
    "database_schema_changed"
  ],

  "changed_symbols": [
    {
      "file": "app/auth/api_key.py",
      "symbol": "validate_api_key",
      "change": "ADDED"
    }
  ],

  "related_files": [
    "tests/test_auth.py",
    "app/models/user.py",
    "openapi.yaml"
  ],

  "tests": {
    "related": 6,
    "added": 3,
    "modified": 2
  },

  "recommended_reviewers": [
    "code-review",
    "security-review",
    "test-impact",
    "database-review",
    "api-review"
  ]
}
```

Adapt fields when necessary.

Do not invent unavailable information.

---

# Metrics

Produce the following metrics whenever available:

```text
files_changed
files_classified
files_analyzed
lines_added
lines_removed
commits_analyzed

symbols_changed

domains_detected
risk_triggers_detected

related_files_discovered

tests_related
tests_added
tests_modified

reviewers_recommended
```

Store machine-readable metrics in:

```text
reports/metrics/<pr-id>-pr-understanding.json
```

---

# Evidence Requirements

Every detected technical domain should be traceable to evidence.

Example:

```text
Domain:
DATABASE

Evidence:
app/models/api_key.py
migrations/20260924_add_api_keys.py
```

Avoid classification solely from keyword matches.

Keywords may trigger investigation, but repository evidence should confirm the classification.

---

# Confidence

When classification is uncertain, record the uncertainty.

Example:

```text
Possible queue behavior detected.

Confidence:
POTENTIAL

Reason:
File imports redis but no queue framework has been identified.
```

Do not force a definitive classification.

---

# What This Skill Must Not Do

Do not:

* publish final review comments;
* assign final defect severity;
* perform broad security auditing;
* fix production code;
* automatically create regression tests;
* perform full architecture review;
* run destructive commands;
* analyze unrelated repository areas.

Those responsibilities belong to downstream skills.

---

# Completion Criteria

The skill is complete when:

* PR intent is summarized;
* changed files are classified;
* important changed symbols are identified where practical;
* technical domains are identified;
* related repository context is mapped;
* relevant tests are identified;
* risk triggers are recorded;
* specialist reviewers are recommended;
* targeted review questions are produced;
* metrics are saved;
* context artifacts are persisted.

---

# Final Summary Format

When presenting the result, use:

```text
PR Understanding

Intent:
...

Scope:
...

Changed files:
...

Technical domains:
...

Risk triggers:
...

Related components:
...

Test impact indicators:
...

Recommended reviewers:
...

Questions for reviewers:
...
```

Keep the human summary concise.

Persist detailed context in structured artifacts.

---

# Engineering Principle

The quality of every downstream review depends on the quality of the context supplied to it.

The objective is therefore not:

> Read every repository file.

The objective is:

> Build the smallest accurate context package necessary for specialized reviewers to understand the Pull Request and its real impact.