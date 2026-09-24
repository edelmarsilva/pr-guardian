# Security Review Skill

## Purpose

This skill reviews Pull Request changes for application security risks introduced, exposed, or materially affected by the change.

Its objective is to identify meaningful security issues with clear evidence and low review noise.

It should combine semantic reasoning with deterministic evidence whenever practical.

---

# Core Principle

Do not treat every suspicious pattern as a confirmed vulnerability.

Prefer:

```text
suspicious change
      ↓
security reasoning
      ↓
evidence
      ↓
verification
      ↓
finding
```

over:

```text
pattern match
      ↓
vulnerability claim
```

---

# When to Use

Use this skill when Pull Request changes affect:

* authentication;
* authorization;
* access control;
* user-controlled input;
* SQL;
* ORM queries;
* shell commands;
* filesystem paths;
* external URLs;
* HTTP clients;
* file uploads;
* secrets;
* tokens;
* sessions;
* API keys;
* cryptography;
* serialization;
* deserialization;
* permissions;
* tenant isolation;
* sensitive logging;
* dependency versions;
* security middleware.

---

# Inputs

Recommended inputs:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
```

and:

* repository path;
* diff;
* changed files;
* related callers;
* related tests;
* schemas;
* configuration;
* dependency files.

---

# Review Scope

Focus primarily on security impact introduced or modified by the Pull Request.

Do not turn the review into a repository-wide penetration test unless explicitly requested.

Classify findings as:

```text
INTRODUCED_BY_PR
EXPOSED_BY_PR
PRE_EXISTING
UNCERTAIN
```

Prioritize the first two.

---

# Phase 1 — Identify Security Boundaries

Determine whether the PR crosses or changes trust boundaries.

Examples:

```text
external request
      ↓
API endpoint
      ↓
service
      ↓
database
```

or:

```text
user input
      ↓
filesystem
```

or:

```text
webhook payload
      ↓
command execution
```

Record:

* source of untrusted data;
* transformations;
* sensitive sink;
* validation;
* authorization checks.

---

# Phase 2 — Authentication Review

Inspect changes affecting identity verification.

Review:

* login;
* password validation;
* API keys;
* JWT;
* OAuth;
* sessions;
* refresh tokens;
* service credentials.

Look for:

```text
authentication bypass
missing credential validation
acceptance of malformed credentials
weak expiration validation
inconsistent authentication paths
```

Example questions:

```text
Can an unauthenticated request reach this code path?

Can an expired token still be accepted?

Can revoked credentials still be used?
```

---

# Phase 3 — Authorization Review

Authentication does not imply authorization.

Inspect:

```text
role checks
resource ownership
tenant boundaries
organization boundaries
permissions
scopes
admin privileges
```

Look for:

```text
missing authorization
authorization performed too late
cross-tenant access
horizontal privilege escalation
vertical privilege escalation
```

Example:

```python
user = User.query.get(user_id)
return user.to_dict()
```

Potential issue if the resource should be scoped to:

```python
organization_id
```

Verify with repository context before reporting.

---

# Phase 4 — Tenant Isolation

For multi-tenant systems, explicitly inspect:

```text
organization_id
tenant_id
account_id
workspace_id
```

Check reads and writes.

Questions:

```text
Can tenant A read tenant B data?

Can tenant A modify tenant B data?

Can user-controlled tenant IDs override authenticated scope?
```

Cross-tenant issues are high-value verification candidates.

---

# Phase 5 — Input Validation

Identify untrusted inputs from:

```text
HTTP requests
query parameters
headers
JSON
forms
files
webhooks
message queues
environment variables
external APIs
```

Check whether input is:

* validated;
* normalized;
* constrained;
* safely converted.

Do not confuse business validation with security validation.

---

# Phase 6 — SQL Injection

Inspect:

```text
raw SQL
string interpolation
dynamic WHERE clauses
dynamic ORDER BY
dynamic table names
```

Potentially unsafe:

```python
query = f"SELECT * FROM users WHERE id = {user_id}"
```

Prefer parameterized execution.

Do not automatically flag ORM usage unless unsafe raw SQL is actually constructed.

---

# Phase 7 — Command Injection

Inspect:

```text
subprocess
os.system
shell=True
Popen
command builders
```

Trace user-controlled values.

High-risk example:

```python
subprocess.run(
    request.json["command"],
    shell=True
)
```

Determine:

```text
source
sanitization
sink
```

This is a strong candidate for Semgrep or regression-test verification.

---

# Phase 8 — Path Traversal

Inspect filesystem operations involving external input.

Examples:

```python
open(filename)
Path(base_dir) / user_input
```

Look for:

```text
../
absolute paths
symlink assumptions
insufficient path normalization
```

Prefer safe resolved-path checks.

---

# Phase 9 — SSRF

Inspect outbound HTTP requests.

Example:

```python
requests.get(request.json["url"])
```

Consider whether an attacker can reach:

```text
localhost
metadata services
internal APIs
private networks
```

Do not report SSRF when URLs come from a trusted fixed configuration.

---

# Phase 10 — File Upload Security

When uploads change, inspect:

```text
filename handling
file size
extension validation
MIME type
storage path
overwrite behavior
execution risk
```

Potential issues:

```text
path traversal
unbounded upload
executable content
unsafe filename reuse
```

---

# Phase 11 — Secrets

Inspect changed code for:

```text
API keys
passwords
tokens
private keys
connection strings
credentials
```

If a real secret is detected:

* never reproduce it in report output;
* redact the value;
* describe the location;
* recommend rotation when appropriate.

Example:

```text
Possible hardcoded credential found in config.py.

Value redacted.
```

---

# Phase 12 — Logging

Check whether sensitive values are logged.

Examples:

```text
password
JWT
refresh token
API key
session identifier
personal or confidential values
```

Example:

```python
logger.info("api_key=%s", api_key)
```

This may create credential exposure.

---

# Phase 13 — Session Security

When session logic changes, inspect:

* session invalidation;
* logout;
* fixation;
* expiration;
* secure cookie settings;
* privilege changes.

Example question:

```text
Are existing sessions invalidated after password change?
```

---

# Phase 14 — JWT Review

When JWT is used, inspect:

```text
signature verification
algorithm handling
expiration
issuer
audience
key selection
revocation strategy
```

Do not require every optional JWT claim unless the system design needs it.

---

# Phase 15 — API Key Review

Inspect:

```text
generation
storage
display
hashing
revocation
expiration
scope
tenant binding
logging
```

Prefer storing a non-reversible representation when possible.

Check whether API keys can be:

```text
reused after revocation
used across tenants
logged
enumerated
```

---

# Phase 16 — Cryptography

Inspect cryptographic changes for:

```text
weak algorithms
hardcoded keys
predictable randomness
insecure modes
homegrown cryptography
incorrect nonce handling
```

Do not claim cryptographic weakness solely because an unfamiliar library is used.

Verify library and configuration behavior.

---

# Phase 17 — Unsafe Deserialization

Inspect:

```text
pickle
yaml.load
eval
exec
custom object deserialization
```

Example:

```python
pickle.loads(user_data)
```

may be dangerous when input is untrusted.

Determine whether attacker-controlled input reaches the sink.

---

# Phase 18 — Dynamic Execution

Review:

```text
eval
exec
dynamic imports
template execution
script execution
```

Treat these as sensitive sinks, not automatic vulnerabilities.

Trace input origin.

---

# Phase 19 — Open Redirect

Inspect redirect targets derived from:

```text
query parameters
forms
headers
```

Example:

```python
return redirect(request.args["next"])
```

Check whether destination is constrained.

---

# Phase 20 — CSRF

For browser-based state-changing operations, determine whether CSRF protections are relevant.

Do not report missing CSRF for APIs that use authentication models not vulnerable to browser credential replay.

Use framework context.

---

# Phase 21 — CORS

When CORS settings change, inspect:

```text
allowed origins
credentials
wildcards
methods
headers
```

Example:

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

may indicate unsafe configuration depending on implementation.

---

# Phase 22 — Rate Limiting and Abuse Controls

Consider rate limits for sensitive operations:

```text
login
password reset
token generation
API key creation
expensive endpoints
```

Do not report lack of rate limiting for every endpoint.

Focus on abuse-sensitive paths.

---

# Phase 23 — Error Information Leakage

Inspect whether new error handling exposes:

```text
stack traces
SQL
filesystem paths
internal hostnames
tokens
secrets
```

Example:

```python
return {"error": str(exception)}, 500
```

may leak internals depending on exception content.

---

# Phase 24 — Dependency Security

When dependency files change, inspect:

```text
new dependency
version upgrade
version downgrade
removed security patch
```

Use tools such as:

```text
pip-audit
```

when appropriate.

A dependency finding should identify:

* package;
* version;
* advisory evidence;
* whether the PR introduced the affected version.

---

# Phase 25 — Authorization Ordering

Security checks should generally happen before sensitive side effects.

Potentially unsafe:

```text
load sensitive object
modify state
check permission
```

Prefer:

```text
authenticate
authorize
perform operation
```

unless architecture intentionally differs.

---

# Phase 26 — Mass Assignment

Inspect patterns where request objects are directly applied to models.

Example:

```python
user.update(**request.json)
```

Potentially attacker-controlled fields may include:

```text
is_admin
role
organization_id
permissions
```

Check explicit field allowlists.

---

# Phase 27 — Insecure Direct Object References

Inspect endpoints that receive object IDs.

Example:

```text
GET /users/<id>
```

Check whether object lookup is constrained by authenticated access rules.

ID presence alone is not a vulnerability.

---

# Phase 28 — Security Regression

Compare security behavior before and after the Pull Request.

Look for removed:

```text
permission check
validation
token expiration
tenant filter
sanitization
security header
```

Removed security controls deserve strong attention.

---

# Phase 29 — Security Test Impact

Identify existing tests for:

```text
authentication failure
authorization failure
cross-tenant access
invalid input
expired credentials
revoked credentials
```

If critical security behavior lacks tests, pass the gap to `test-impact`.

---

# Phase 30 — Deterministic Tools

Use tools when they add evidence.

Potential tools:

```text
Bandit
Semgrep
pip-audit
pytest
```

Possible additional tools if already available:

```text
Trivy
OWASP ZAP
```

Do not install large toolchains automatically unless justified.

---

# Bandit Usage

Bandit is useful for Python security patterns.

Possible command:

```bash
bandit -r app -f json
```

Preserve raw output:

```text
reports/raw/<pr-id>/bandit.json
```

Do not convert every Bandit warning into a review finding.

---

# Semgrep Usage

Use Semgrep for source-to-sink and known security patterns.

Example:

```bash
semgrep scan --config auto --json
```

Preserve:

```text
reports/raw/<pr-id>/semgrep.json
```

Interpret findings in Pull Request context.

---

# pip-audit Usage

For Python dependencies:

```bash
pip-audit -f json
```

Preserve:

```text
reports/raw/<pr-id>/pip-audit.json
```

Distinguish:

```text
introduced by PR
pre-existing
```

---

# OWASP ZAP

OWASP ZAP may be used when:

* the application can run locally;
* relevant HTTP behavior changed;
* safe isolated scanning is possible.

Prefer baseline/passive scanning for hackathon workflows.

Do not run active attacks against production or unauthorized systems.

ZAP findings require interpretation.

---

# Verification Candidates

Prioritize executable verification for:

```text
authorization bypass
tenant isolation failure
unsafe input handling
security regression
```

Example:

```text
Potential:
Cross-tenant resource access.

Verification:
Create two synthetic organizations and attempt access using the wrong token.
```

Pass to:

```text
finding-verification
```

---

# Finding Categories

Suggested categories:

```text
AUTHENTICATION
AUTHORIZATION
ACCESS_CONTROL
TENANT_ISOLATION
SQL_INJECTION
COMMAND_INJECTION
PATH_TRAVERSAL
SSRF
FILE_UPLOAD
SECRET_EXPOSURE
SENSITIVE_LOGGING
SESSION_SECURITY
TOKEN_SECURITY
CRYPTOGRAPHY
DESERIALIZATION
DYNAMIC_EXECUTION
OPEN_REDIRECT
CSRF
CORS
MASS_ASSIGNMENT
IDOR
DEPENDENCY_VULNERABILITY
INFORMATION_DISCLOSURE
```

---

# Severity Guidance

## CRITICAL

Use rarely.

Examples:

```text
unauthenticated remote command execution
widespread authentication bypass
direct compromise of highly sensitive system
```

---

## HIGH

Examples:

```text
cross-tenant data access
privilege escalation
SQL injection with meaningful reach
credential exposure
authorization bypass
```

---

## MEDIUM

Examples:

```text
limited information disclosure
unsafe validation requiring specific conditions
session weakness with constrained impact
```

---

## LOW

Examples:

```text
minor hardening gap
limited security robustness issue
low-impact disclosure
```

---

## INFO

Use only for contextual security observations.

---

# Confidence

Use:

```text
CONFIRMED
LIKELY
POTENTIAL
INFORMATIONAL
```

CONFIRMED requires direct evidence or reproduction.

---

# Required Finding Structure

Each finding should include:

```text
id
category
severity
confidence
title
description
file
line
source
sink
evidence
impact
recommendation
verification_status
introduced_by_pr
```

`source` and `sink` may be omitted when not applicable.

---

# Example Finding

```json
{
  "id": "SEC-001",
  "category": "AUTHORIZATION",
  "severity": "HIGH",
  "confidence": "LIKELY",
  "title": "Resource lookup is not scoped to the authenticated organization",
  "description": "The new endpoint loads Report by its global ID without applying organization scope.",
  "file": "app/api/reports.py",
  "line": 72,
  "source": "request path parameter report_id",
  "sink": "Report.query.get(report_id)",
  "evidence": [
    "authenticated organization is available in request context",
    "the query does not filter by organization_id",
    "other report endpoints apply organization scoping"
  ],
  "impact": "A user may be able to access a report belonging to another organization if the identifier is known.",
  "recommendation": "Scope the report lookup to the authenticated organization and add a cross-tenant regression test.",
  "verification_status": "UNVERIFIED",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/security-review.json
```

Optionally:

```text
reports/findings/<pr-id>/security-review.md
```

The JSON artifact is canonical.

---

# Metrics

Record:

```text
files_reviewed
security_sensitive_files
trust_boundaries_reviewed

findings_total
critical_findings
high_findings
medium_findings
low_findings

confirmed_findings
likely_findings
potential_findings

authentication_findings
authorization_findings
injection_findings
tenant_isolation_findings
secret_findings
dependency_findings

bandit_findings_raw
semgrep_findings_raw
dependency_findings_raw

verification_candidates
```

Save:

```text
reports/metrics/<pr-id>-security-review.json
```

---

# False Positive Control

Before reporting a security finding:

1. verify the input is actually attacker-controlled or untrusted;
2. verify the sensitive operation actually occurs;
3. inspect existing controls;
4. determine whether framework behavior already mitigates the risk;
5. inspect repository conventions;
6. assign confidence appropriately.

Do not report theoretical exploit paths unsupported by code.

---

# Duplicate Control

If Bandit, Semgrep, and semantic review identify the same issue:

produce one consolidated finding.

Preserve multiple evidence sources.

Example:

```text
Evidence:
- semantic review
- Semgrep rule python.lang.security.audit.subprocess-shell-true
```

---

# What This Skill Must Not Do

Do not:

* automatically modify production code;
* expose discovered secrets;
* run destructive security scans;
* exploit external systems;
* publish findings directly to GitHub;
* treat tool warnings as confirmed vulnerabilities;
* perform unrelated repository-wide pentesting.

---

# Completion Criteria

The skill is complete when:

* relevant security boundaries are identified;
* security-sensitive changes are reviewed;
* authentication and authorization are considered when applicable;
* untrusted-input paths are inspected;
* deterministic tools are used where useful;
* high-value findings are structured;
* verification candidates are identified;
* duplicate findings are removed;
* metrics are saved.

---

# Human Summary Format

Use:

```text
Security Review

Security-sensitive files:
...

Findings:
Critical:
High:
Medium:
Low:

Confirmed:
Likely:
Potential:

Primary risks:
...

Verification candidates:
...

Tool evidence:
...
```

Keep the human summary concise.

---

# Engineering Principle

Security review quality is not measured by the number of warnings produced.

The objective is:

> Identify security changes that materially affect trust boundaries and provide enough evidence for developers to act with confidence.