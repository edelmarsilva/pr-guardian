# API Review Skill

## Purpose

This skill reviews Pull Request changes that affect HTTP APIs, routes, request and response schemas, status codes, authentication requirements, versioning, and API documentation.

Its goal is to identify contract regressions, undocumented behavior changes, compatibility risks, and inconsistencies between implementation and API specifications.

The review should focus on externally observable behavior.

---

# Core Principle

An API change is not just a code change.

It may affect:

```text
server implementation
        ↓
API contract
        ↓
clients
        ↓
integrations
```

The review must therefore consider both implementation and consumer expectations.

---

# When to Use

Use this skill when a Pull Request changes:

* routes;
* controllers;
* handlers;
* serializers;
* schemas;
* request validation;
* response payloads;
* HTTP methods;
* status codes;
* authentication requirements;
* authorization requirements;
* pagination;
* versioning;
* OpenAPI;
* Swagger;
* API documentation;
* webhooks.

---

# Inputs

Recommended inputs:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
```

plus:

* repository path;
* changed route files;
* request/response schemas;
* OpenAPI or Swagger files;
* API tests;
* authentication middleware;
* client contracts when available.

---

# Phase 1 — Identify API Framework

Detect the framework.

Examples:

```text
Flask
FastAPI
Django REST Framework
Express
Spring
ASP.NET
```

Use framework conventions when analyzing routes and schemas.

---

# Phase 2 — Identify Changed Endpoints

Build an endpoint inventory.

Example:

```text
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/{id}
DELETE /api/v1/users/{id}
```

For each changed endpoint, record:

* method;
* path;
* handler;
* authentication;
* authorization;
* request schema;
* response schema;
* documented status codes.

---

# Phase 3 — Classify API Changes

Classify each API change as:

```text
ENDPOINT_ADDED
ENDPOINT_REMOVED
METHOD_CHANGED
PATH_CHANGED
REQUEST_CHANGED
RESPONSE_CHANGED
STATUS_CHANGED
AUTH_CHANGED
AUTHORIZATION_CHANGED
VERSION_CHANGED
DOCUMENTATION_CHANGED
```

A single endpoint may have multiple classifications.

---

# Phase 4 — Public Contract Classification

Classify the overall contract impact as:

```text
NO_EXTERNAL_CHANGE
BACKWARD_COMPATIBLE
POTENTIAL_BREAKING_CHANGE
BREAKING_CHANGE
UNCERTAIN
```

Do not claim a breaking change without evidence.

---

# Phase 5 — Request Schema Review

Inspect changes involving:

```text
required fields
optional fields
types
formats
enums
nested objects
arrays
default values
```

Potential breaking changes include:

```text
optional → required
accepted type removed
enum value removed
field renamed
request structure changed
```

---

# Phase 6 — Response Schema Review

Inspect:

```text
fields added
fields removed
field types changed
nullability changed
nested structures changed
error shapes changed
```

Adding optional response fields is often compatible.

Removing or changing existing fields may break clients.

---

# Phase 7 — Status Code Review

Check whether status codes match behavior.

Examples:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Content
500 Internal Server Error
```

Avoid mechanically enforcing one code without considering project conventions.

---

# Phase 8 — Error Response Consistency

Inspect whether errors use a consistent structure.

Example:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found"
  }
}
```

Potential regression:

```text
existing endpoints return structured errors
new endpoint returns plain text
```

---

# Phase 9 — Authentication Contract

Check whether authentication requirements changed.

Examples:

```text
public → authenticated
authenticated → public
JWT → JWT or API key
```

This may be a breaking behavioral change.

Coordinate with `security-review`.

---

# Phase 10 — Authorization Contract

Inspect whether access rules changed for:

```text
roles
permissions
tenant scope
resource ownership
```

API documentation should reflect meaningful authorization expectations when relevant.

---

# Phase 11 — Method Semantics

Review whether HTTP methods match behavior.

Examples:

```text
GET should not mutate state
PUT generally replaces a resource
PATCH modifies part of a resource
DELETE removes or logically deletes a resource
```

Do not enforce textbook semantics blindly when existing API design differs.

---

# Phase 12 — Idempotency

Review methods expected to be safely repeatable.

Examples:

```text
PUT
DELETE
some PATCH operations
```

Also inspect POST operations that may be retried by clients.

Potential issue:

```text
retrying request creates duplicate resources
```

Coordinate with code and database reviewers.

---

# Phase 13 — Pagination

When pagination changes, review:

```text
page
limit
offset
cursor
next token
total count
ordering
```

Look for:

```text
unstable ordering
unbounded page size
duplicate records between pages
missing pagination metadata
```

---

# Phase 14 — Filtering

Review filter parameters for:

```text
documented behavior
validation
supported values
default behavior
```

Example:

```text
status=active
```

should not silently accept invalid values unless intentionally designed.

---

# Phase 15 — Sorting

Inspect:

```text
sort field
direction
default ordering
allowed fields
```

Dynamic sorting can also create database or security concerns.

Coordinate with appropriate specialists.

---

# Phase 16 — Versioning

Identify API version strategy.

Examples:

```text
/api/v1/
Accept header
custom media type
```

If a breaking change is introduced inside an existing version, flag compatibility risk.

Do not demand version bump for every minor change.

---

# Phase 17 — Deprecation

When removing or replacing behavior, check for:

```text
deprecation notice
transition period
replacement endpoint
documentation
```

This is especially relevant for public integrations.

---

# Phase 18 — Content Types

Inspect:

```text
Content-Type
Accept
multipart/form-data
application/json
```

Check whether newly accepted or returned content types are documented.

---

# Phase 19 — Header Contract

Review changed headers such as:

```text
Authorization
ETag
Location
Retry-After
Idempotency-Key
X-Request-ID
```

Potential regression:

```text
header previously required but silently removed
```

---

# Phase 20 — Location Header

For created resources, consider whether project convention expects:

```text
201 Created
Location: /resource/<id>
```

Do not require this unless consistent with the API design.

---

# Phase 21 — Empty Responses

Check consistency between:

```text
204 No Content
```

and actual response body.

Do not return meaningful bodies with 204.

---

# Phase 22 — PATCH Semantics

When PATCH endpoints change, inspect:

```text
partial update
missing fields
explicit null
immutable fields
authorization
```

Ensure omitted values are distinguishable from explicit null when needed.

---

# Phase 23 — PUT Semantics

If PUT is used, determine whether omitted fields are:

```text
preserved
reset
required
```

Behavior should match documented contract.

---

# Phase 24 — Validation Errors

Check how invalid requests are represented.

Look for:

```text
field errors
type errors
missing values
invalid enum
malformed JSON
```

API behavior should be predictable.

---

# Phase 25 — Resource Not Found

Inspect whether missing resources consistently return:

```text
404
```

versus ambiguous errors such as:

```text
500
200 with null payload
```

Consider security patterns that intentionally use 404 instead of 403.

---

# Phase 26 — Conflict Handling

Check operations where:

```text
duplicate creation
state conflict
uniqueness violation
concurrent modification
```

may justify:

```text
409 Conflict
```

Use repository conventions.

---

# Phase 27 — Rate Limit Contract

If rate limiting behavior changes, inspect:

```text
429 Too Many Requests
Retry-After
documentation
```

Coordinate with `security-review` when abuse prevention is relevant.

---

# Phase 28 — Webhook Review

When webhooks change, inspect:

```text
payload schema
event type
signature
retry behavior
idempotency
response expectations
```

Webhook security belongs partly to `security-review`.

---

# Phase 29 — OpenAPI Detection

Look for:

```text
openapi.yaml
openapi.yml
openapi.json
swagger.yaml
swagger.json
```

When present, compare implementation and documentation.

---

# Phase 30 — OpenAPI Endpoint Coverage

Check whether:

```text
implemented endpoints
```

are represented in the API specification.

Example metric:

```text
implemented changed endpoints: 5
documented changed endpoints:   4
missing documentation:          1
```

---

# Phase 31 — OpenAPI Request Schema

Compare implementation with:

```text
requestBody
parameters
required fields
schemas
```

Potential finding:

```text
Implementation requires organization_id but OpenAPI marks it optional.
```

---

# Phase 32 — OpenAPI Response Schema

Compare:

```text
response fields
status codes
content types
```

Example:

```text
Implementation now returns 409,
but OpenAPI documents only 201 and 400.
```

---

# Phase 33 — OpenAPI Security Schemes

Check:

```text
securitySchemes
security
OAuth scopes
API keys
Bearer authentication
```

If implementation authentication changes but specification does not, report contract drift.

---

# Phase 34 — OpenAPI Version Compatibility

If the specification version changes, avoid unnecessary migration recommendations unless required.

Support whatever version the repository currently uses.

---

# Phase 35 — Client Compatibility

When client code is available, inspect likely consumers.

Example:

```text
frontend/
sdk/
integration/
```

A response-field change may directly break typed clients.

Use `change-impact` evidence.

---

# Phase 36 — Breaking Change Detection

Strong breaking-change candidates include:

```text
endpoint removed
HTTP method removed
required request field added
response field removed
response type changed
authentication requirement strengthened
enum value removed
```

Confirm whether the contract is externally consumed before assigning severity.

---

# Phase 37 — Compatible Change Detection

Usually compatible changes include:

```text
new optional field
new endpoint
new optional query parameter
new optional response field
```

Context still matters.

---

# Phase 38 — Error Contract Changes

Error structures are part of API contracts.

Example:

Before:

```json
{
  "error": "invalid token"
}
```

After:

```json
{
  "message": "invalid token"
}
```

Clients may depend on the old shape.

---

# Phase 39 — API Documentation Drift

Inspect:

```text
README
API docs
OpenAPI
examples
```

Potential finding:

```text
API behavior changed but documentation was not updated.
```

Severity depends on integration impact.

---

# Phase 40 — Tests

Identify tests covering:

```text
success responses
validation failures
authentication
authorization
not found
conflicts
schema
```

Missing test scenarios should be handed to `test-impact`.

---

# Finding Categories

Use:

```text
BREAKING_CHANGE
REQUEST_CONTRACT
RESPONSE_CONTRACT
STATUS_CODE
ERROR_CONTRACT
AUTH_CONTRACT
AUTHORIZATION_CONTRACT
PAGINATION
FILTERING
VERSIONING
DOCUMENTATION_DRIFT
OPENAPI_MISMATCH
WEBHOOK_CONTRACT
HTTP_SEMANTICS
```

---

# Severity Guidance

## HIGH

Examples:

```text
existing endpoint removed without version change
required field added to widely used endpoint
authentication removed unexpectedly
```

## MEDIUM

Examples:

```text
documented schema differs from implementation
error response shape changed
pagination behavior unstable
```

## LOW

Examples:

```text
minor documentation inconsistency
missing optional response documentation
```

CRITICAL should be rare and usually requires broader security or availability impact.

---

# Confidence

Use:

```text
CONFIRMED
LIKELY
POTENTIAL
INFORMATIONAL
```

Contract mismatches with direct implementation/spec evidence are typically CONFIRMED.

---

# Example Finding

```json
{
  "id": "API-001",
  "category": "OPENAPI_MISMATCH",
  "severity": "MEDIUM",
  "confidence": "CONFIRMED",
  "title": "New 409 response is missing from the OpenAPI contract",
  "description": "The updated user creation endpoint returns 409 when the email already exists, but the OpenAPI specification documents only 201, 400, and 401.",
  "file": "openapi.yaml",
  "line": 214,
  "evidence": [
    "app/api/users.py returns 409 on duplicate email",
    "the documented responses for POST /users do not include 409"
  ],
  "impact": "Generated clients and API consumers may not handle the new conflict response correctly.",
  "recommendation": "Document the 409 response and its error schema in the OpenAPI definition.",
  "verification_status": "VERIFIED",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# OpenAPI Verification

When practical, use deterministic validation.

Possible checks:

```text
OpenAPI parser validation
schema validation
route/spec comparison
response contract tests
```

Do not add heavy tooling unless useful.

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/api-review.json
```

Optionally:

```text
reports/findings/<pr-id>/api-review.md
```

---

# Metrics

Record:

```text
endpoints_reviewed
endpoints_added
endpoints_removed
endpoints_modified

request_contract_changes
response_contract_changes
status_code_changes
authentication_changes
authorization_changes

openapi_endpoints_checked
openapi_mismatches
undocumented_endpoints
undocumented_status_codes

breaking_changes
potential_breaking_changes

findings_total
high_findings
medium_findings
low_findings

confirmed_findings
likely_findings
potential_findings
```

Save:

```text
reports/metrics/<pr-id>-api-review.json
```

---

# Specialist Handoff

When concerns overlap:

```text
authentication or authorization
→ security-review

missing contract tests
→ test-impact

query or pagination performance
→ database-review

public interface structural change
→ architecture-review
```

Avoid duplicate findings.

---

# What This Skill Must Not Do

Do not:

* redesign the entire API;
* require REST purity where the project uses another convention;
* automatically version every changed endpoint;
* treat every documentation difference as high severity;
* duplicate security findings;
* modify API definitions during analysis.

---

# Completion Criteria

The skill is complete when:

* changed endpoints are inventoried;
* request and response contracts are compared;
* status codes are reviewed;
* authentication and authorization contract changes are noted;
* OpenAPI is compared when available;
* compatibility risks are classified;
* findings are structured;
* metrics are persisted.

---

# Human Summary Format

Use:

```text
API Review

Endpoints reviewed:
...

Added:
...

Modified:
...

Breaking changes:
...

OpenAPI mismatches:
...

Findings:
High:
Medium:
Low:

Primary contract risks:
...
```

---

# Engineering Principle

An API review should answer:

> Will existing and future consumers correctly understand and safely use the API after this Pull Request is merged?

The goal is not REST purity.

The goal is contract stability, predictability, and documented behavior.