# Architecture Review Skill

## Purpose

This skill reviews Pull Request changes for architectural impact, responsibility boundaries, coupling, dependency direction, cohesion, layering, extensibility, and maintainability risks.

Its goal is to identify changes that materially weaken or alter the structure of the system.

It must avoid theoretical design criticism without evidence.

---

# Core Principle

Do not report:

> "This violates SOLID."

Report:

> "This controller now performs persistence and business-rule validation directly, bypassing the service boundary used by the rest of the module."

Architecture findings must explain:

```text
what changed
    ↓
which boundary changed
    ↓
why it matters
    ↓
what behavior or maintenance risk it creates
```

---

# When to Use

Use this skill when a Pull Request:

* introduces new modules;
* adds large services;
* moves responsibilities;
* adds cross-layer dependencies;
* changes public interfaces;
* introduces new abstractions;
* changes dependency direction;
* touches multiple architectural layers;
* adds shared utilities;
* introduces new framework dependencies;
* changes domain boundaries;
* creates significant reuse or coupling;
* modifies dependency injection;
* introduces architectural patterns.

Skip or minimize this review for trivial localized changes.

---

# Inputs

Recommended inputs:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json
```

plus:

* repository structure;
* changed files;
* changed symbols;
* imports;
* module dependencies;
* application boundaries;
* existing architectural documentation.

---

# Phase 1 — Identify Existing Architecture

Before judging the Pull Request, understand the repository's existing structure.

Identify patterns such as:

```text
Controller
    ↓
Service
    ↓
Repository
```

or:

```text
Domain
Application
Infrastructure
Interface
```

or:

```text
Routes
Services
Models
```

Do not impose a different architectural style simply because it is preferred elsewhere.

---

# Phase 2 — Identify Architectural Boundaries

Determine the important boundaries already present.

Examples:

```text
API → Service

Service → Repository

Domain → Interface abstraction

Infrastructure → External service

Controller → Application layer
```

Record which boundaries the Pull Request crosses.

---

# Phase 3 — Dependency Direction

Inspect imports and calls introduced by the PR.

Look for unexpected dependency direction.

Example:

Expected:

```text
API
 ↓
Service
 ↓
Repository
```

PR introduces:

```text
Repository
 ↓
API
```

This may indicate reversed dependency direction.

Only report when it creates concrete structural or testing impact.

---

# Phase 4 — Layer Violations

Identify cases where a layer bypasses an established boundary.

Example:

Before:

```text
Route
 ↓
UserService
 ↓
UserRepository
```

PR:

```text
Route
 ↓
db.session.query(...)
```

Possible finding:

```text
API layer now accesses persistence directly,
bypassing the service and repository boundaries used by the module.
```

Explain consequences such as:

* duplicated business logic;
* harder testing;
* inconsistent transaction behavior.

---

# Phase 5 — Responsibility Analysis

Inspect whether changed classes or modules accumulate unrelated responsibilities.

Examples:

```text
authentication
email sending
database access
token generation
audit logging
```

all added to one class.

Avoid counting methods mechanically.

Focus on distinct reasons the component may need to change.

---

# Phase 6 — Cohesion

Determine whether newly added behavior logically belongs in the modified component.

Questions:

```text
Does this behavior operate on the same domain responsibility?

Does it depend on unrelated infrastructure?

Will unrelated feature changes require modifying this component?
```

Low cohesion should be reported only when meaningful.

---

# Phase 7 — Coupling

Identify new dependencies.

Example:

Before:

```text
ReportService
 ├── Repository
 └── Renderer
```

After PR:

```text
ReportService
 ├── Repository
 ├── Renderer
 ├── Email
 ├── Storage
 ├── Queue
 └── Audit
```

High coupling may indicate orchestration responsibilities are expanding.

Explain impact instead of assigning a generic score.

---

# Phase 8 — Circular Dependencies

Inspect imports and dependency direction for cycles.

Example:

```text
service.py → repository.py
repository.py → service.py
```

Potential impacts:

* initialization problems;
* difficult testing;
* hidden coupling.

Verify actual imports before reporting.

---

# Phase 9 — Shared Utility Growth

Pay attention when generic modules such as:

```text
utils.py
helpers.py
common.py
```

gain domain-specific behavior.

Example:

```text
utils.py now imports UserRepository
```

This may indicate domain logic leaking into generic infrastructure.

---

# Phase 10 — Public Interface Growth

Inspect new public methods, functions, or modules.

Questions:

```text
Is the new public interface necessary?

Does it expose internal implementation details?

Will callers depend on unstable internals?
```

Do not recommend hiding interfaces without concrete value.

---

# Phase 11 — Encapsulation

Look for changes that expose internal mutable state.

Example:

```python
return self._items
```

when callers can mutate internal state unexpectedly.

Prefer encapsulation findings only when mutation risk exists.

---

# Phase 12 — Dependency Injection

When dependencies are instantiated directly inside business logic:

```python
client = ExternalAPIClient()
```

consider whether this reduces testability or creates hidden coupling.

Compare with repository conventions.

Do not require dependency injection everywhere.

---

# Phase 13 — Interface Segregation

When interfaces change, inspect whether clients are forced to depend on unrelated behavior.

Example:

```text
Storage

save()
load()
send_email()
generate_pdf()
```

If consumers only need storage, unrelated methods may indicate abstraction drift.

Report concrete client impact.

---

# Phase 14 — Dependency Inversion

Review whether high-level business logic becomes directly dependent on low-level infrastructure.

Example:

```text
BillingService
    ↓
requests.post()
```

instead of a repository-established integration boundary.

Only report if the project already uses such abstractions or if testability materially worsens.

---

# Phase 15 — Open/Closed Principle

Use OCP carefully.

Do not report:

> "This violates OCP."

Instead identify patterns such as:

```python
if provider == "aws":
    ...
elif provider == "azure":
    ...
elif provider == "gcp":
    ...
```

when every new provider requires modifying a central service.

Potential finding:

```text
The new provider branch extends an already centralized conditional.
Adding another provider will require modifying the same orchestration logic again.
```

Report only when extensibility is clearly part of the design.

---

# Phase 16 — Liskov Substitution

When inheritance changes, inspect whether subclasses preserve expected behavior.

Examples:

```text
base method guarantees return value
subclass now returns None

base implementation accepts broad input
subclass rejects valid base input
```

Avoid abstract textbook criticism.

Use caller expectations as evidence.

---

# Phase 17 — Interface Compatibility

When abstract interfaces or protocols change, identify affected implementations.

Example:

```text
Storage.save(data)
```

becomes:

```text
Storage.save(data, metadata)
```

Affected implementations:

```text
S3Storage
LocalStorage
MemoryStorage
```

This may create broad implementation impact.

---

# Phase 18 — Domain Boundary Review

If repository structure suggests domain separation, inspect cross-domain imports.

Example:

```text
billing
 ↓
authentication internals
```

Potentially problematic if an established public boundary exists.

Do not invent domain boundaries not present in the project.

---

# Phase 19 — Data Access Boundaries

Inspect whether persistence details leak into higher layers.

Examples:

```text
SQLAlchemy query objects returned to controllers

database sessions passed across layers

ORM models exposed directly as API contracts
```

Report only when this creates coupling or behavioral inconsistency.

---

# Phase 20 — Framework Leakage

Look for business logic becoming tightly coupled to framework objects.

Example:

```python
def calculate_discount(request):
```

when logic should operate on domain values.

Framework coupling is not automatically wrong.

Evaluate reuse and testing impact.

---

# Phase 21 — Configuration Coupling

Check whether domain logic begins reading environment variables directly.

Example:

```python
os.getenv("MAX_RETRY")
```

inside a core business function.

Potential consequences:

* hidden dependency;
* difficult testing;
* inconsistent configuration access.

Compare with repository conventions.

---

# Phase 22 — Transaction Boundaries

Architecture review may consider transaction ownership.

Example:

```text
Controller begins transaction
Service commits transaction
Repository rolls back
```

This may create unclear ownership.

Detailed database correctness belongs to `database-review`.

---

# Phase 23 — Cross-Cutting Concerns

Inspect introduction of:

```text
logging
metrics
authorization
caching
retry
auditing
```

inside many business components.

If the same concern is duplicated broadly, note architectural impact.

---

# Phase 24 — Duplication With Architectural Impact

Do not report every duplicate code block.

Report duplication when it creates multiple sources of truth.

Example:

```text
authorization logic duplicated across five routes
```

Potential impact:

```text
future permission changes must be synchronized manually
```

---

# Phase 25 — Architectural Regression

Compare architecture before and after PR.

Examples:

```text
service boundary removed
repository abstraction bypassed
domain logic moved into controller
shared abstraction duplicated
```

PRs should be judged relative to existing design.

---

# Phase 26 — New Abstractions

New abstractions should solve an actual repeated or structural problem.

Potential over-abstraction signals:

```text
interface with one implementation
factory with one option
wrapper with no behavioral isolation
```

Do not report this automatically.

Only report when abstraction adds meaningful complexity without current value.

---

# Phase 27 — Under-Abstraction

Conversely, identify repeated patterns introduced by the PR.

Example:

```text
three routes implement identical authorization and query logic
```

This may justify shared behavior.

---

# Phase 28 — God Object / God Service Signals

Look for components that accumulate many unrelated responsibilities.

Evidence may include:

```text
database access
HTTP integrations
business rules
email
queue orchestration
report rendering
```

all inside one service.

Do not classify solely based on file length.

---

# Phase 29 — Constructor Complexity

A rapidly growing dependency list can indicate coupling.

Example:

```python
UserService(
    repository,
    mailer,
    queue,
    audit,
    storage,
    billing,
    metrics
)
```

This is a signal, not automatically a defect.

Inspect whether responsibilities are coherent.

---

# Phase 30 — Change Amplification

Use `change-impact` evidence.

A component may be architecturally sensitive if small changes affect many modules.

Example:

```text
1 changed method
17 dependent components
```

Consider whether the abstraction is stable enough.

---

# Phase 31 — Testability Impact

Architecture findings should consider whether the change makes testing significantly harder.

Examples:

```text
hardcoded external client
global mutable state
database call inside pure domain logic
```

Testability is a useful indicator of coupling.

---

# Phase 32 — Replaceability

Where abstractions exist specifically to allow replacement, verify the PR preserves that ability.

Example:

```text
Storage interface
```

but new code imports:

```text
S3Storage
```

directly into business logic.

That may bypass the abstraction.

---

# Phase 33 — Architecture Documentation

If significant architecture changes occur, inspect:

```text
docs/architecture.md
ADR files
README architecture sections
```

A major architectural change with stale documentation may be reported as a low or medium impact issue.

---

# Finding Categories

Use categories such as:

```text
LAYER_VIOLATION
DEPENDENCY_DIRECTION
EXCESSIVE_COUPLING
LOW_COHESION
RESPONSIBILITY_OVERLOAD
CIRCULAR_DEPENDENCY
ENCAPSULATION
ABSTRACTION_LEAK
FRAMEWORK_COUPLING
DUPLICATED_RESPONSIBILITY
PUBLIC_INTERFACE
DOMAIN_BOUNDARY
TESTABILITY
ARCHITECTURAL_REGRESSION
```

---

# Severity Guidance

## HIGH

Use when architectural changes create broad functional or maintenance risk.

Examples:

```text
shared authorization boundary bypassed
core dependency cycle introduced
major transaction ownership ambiguity
```

---

## MEDIUM

Examples:

```text
business logic duplicated across multiple layers
service takes on unrelated responsibilities
public abstraction bypassed
```

---

## LOW

Examples:

```text
localized coupling increase
minor abstraction inconsistency
documentation drift
```

Architecture findings should rarely be CRITICAL.

---

# Confidence

Use:

```text
CONFIRMED
LIKELY
POTENTIAL
INFORMATIONAL
```

Architecture findings should normally be CONFIRMED only when dependency or structural evidence is clear.

---

# Evidence Requirements

Every finding should include structural evidence.

Example:

```text
Existing pattern:
routes → UserService → UserRepository

PR change:
routes/users.py directly imports db.session

Affected operations:
create_user
delete_user
```

This is stronger than:

```text
This violates layered architecture.
```

---

# Example Finding

```json
{
  "id": "ARCH-001",
  "category": "LAYER_VIOLATION",
  "severity": "MEDIUM",
  "confidence": "CONFIRMED",
  "title": "User route bypasses the existing service boundary",
  "description": "The new delete endpoint performs persistence directly in the route, while the rest of the user module routes operations through UserService.",
  "file": "app/api/users.py",
  "line": 118,
  "evidence": [
    "create and update routes call UserService",
    "the new delete route imports db.session directly",
    "UserService already contains user deletion orchestration"
  ],
  "impact": "Deletion rules and transaction behavior can diverge from other user operations and become harder to test consistently.",
  "recommendation": "Route the deletion operation through the established user service boundary.",
  "verification_status": "VERIFIED",
  "introduced_by_pr": "INTRODUCED_BY_PR"
}
```

---

# SOLID Usage Rules

SOLID principles may support reasoning but should not be the finding title by default.

Avoid:

```text
SRP violation
OCP violation
DIP violation
```

Prefer concrete descriptions.

Example:

Instead of:

```text
SRP violation
```

use:

```text
UserService now owns email delivery in addition to user lifecycle logic.
```

Then explain why it matters.

---

# Design Pattern Rules

Do not recommend a design pattern simply because one exists.

Patterns should solve an observed problem.

Bad recommendation:

```text
Use Strategy Pattern.
```

Better:

```text
Provider-specific behavior is now spread across four conditional branches.
A provider abstraction could isolate these changes if more providers are expected.
```

---

# Required Output

Generate:

```text
reports/findings/<pr-id>/architecture-review.json
```

Optionally:

```text
reports/findings/<pr-id>/architecture-review.md
```

---

# Metrics

Record:

```text
files_reviewed
modules_reviewed

new_dependencies
cross_layer_dependencies
circular_dependencies

layer_violations
responsibility_findings
coupling_findings
cohesion_findings
public_interface_changes
architectural_regressions

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
reports/metrics/<pr-id>-architecture-review.json
```

---

# Reviewer Handoff

When architecture analysis exposes specialized concerns:

```text
database transaction issue
→ database-review

authorization boundary issue
→ security-review

missing regression coverage
→ test-impact

public API compatibility
→ api-review
```

Do not duplicate specialist analysis unnecessarily.

---

# What This Skill Must Not Do

Do not:

* refactor production code automatically;
* impose a new architecture on the repository;
* report textbook pattern violations without impact;
* criticize naming or formatting;
* recommend abstractions with no current value;
* turn the review into a complete redesign proposal.

---

# Completion Criteria

The skill is complete when:

* existing architecture is understood sufficiently;
* changed dependency directions are reviewed;
* boundaries are inspected;
* responsibilities and coupling are evaluated;
* meaningful architectural regressions are identified;
* findings contain concrete evidence;
* specialist handoffs are identified;
* metrics are persisted.

---

# Human Summary Format

Use:

```text
Architecture Review

Architecture areas affected:
...

New dependencies:
...

Boundary changes:
...

Findings:
High:
Medium:
Low:

Primary concerns:
...

Specialist handoffs:
...
```

---

# Engineering Principle

Architecture review should answer:

> Does this Pull Request make the system structurally harder to understand, change, test, or safely extend?

The goal is not architectural purity.

The goal is to preserve clear boundaries and reduce future change risk.