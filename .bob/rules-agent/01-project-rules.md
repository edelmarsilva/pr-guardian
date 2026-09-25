# PR Guardian Agent Rules

These rules apply to all Bob Agent Mode tasks executed inside the PR Guardian project.

They are mandatory unless the current task explicitly overrides a rule.

---

## 1. Understand Before Acting

Before modifying code, generating findings, or proposing remediation:

1. inspect the relevant Pull Request context;
2. identify changed files;
3. understand the stated intent of the change;
4. inspect surrounding code when needed;
5. identify affected components and dependencies;
6. determine which specialized review skills are relevant.

Do not begin implementation or publish review findings based only on a superficial diff inspection.

---

## 2. Do Not Review Only the Diff

The diff is the starting point, not the entire review context.

When required, inspect:

* callers;
* callees;
* related services;
* models;
* schemas;
* tests;
* configuration;
* migrations;
* API contracts;
* queue workers;
* documentation;
* repository conventions.

A finding that depends on repository behavior should include repository evidence.

---

## 3. Preserve Read-Only Review Semantics

Pull Request analysis is read-only by default.

Do not modify target repository production code unless the active task explicitly requests remediation or implementation.

Allowed during analysis:

* reading files;
* executing safe tests;
* running static analyzers;
* generating reports;
* creating temporary verification tests in isolated locations;
* producing metrics.

Not allowed during analysis:

* changing application behavior;
* silently fixing reviewed code;
* rewriting the Pull Request;
* committing changes.

---

## 4. Use Adaptive Review Routing

Do not invoke every specialized reviewer for every Pull Request.

Select reviewers based on actual change scope.

Examples:

### Authentication changes

Use:

* code-review;
* security-review;
* test-impact.

### Database migration changes

Use:

* code-review;
* database-review;
* test-impact.

### API contract changes

Use:

* code-review;
* api-review;
* test-impact.

### Background job changes

Use:

* code-review;
* queue-review;
* test-impact.

### Documentation-only changes

Avoid unrelated technical reviewers unless the documentation reveals a relevant inconsistency.

---

## 5. Findings Must Be Evidence-Based

Every meaningful finding must contain supporting evidence.

Preferred evidence sources:

* changed code;
* repository context;
* call relationships;
* existing tests;
* failing tests;
* static analysis output;
* security analysis output;
* API contract mismatch;
* database constraints;
* reproducible behavior.

Do not present unsupported speculation as a confirmed defect.

---

## 6. Separate Severity From Confidence

Severity and confidence are independent.

Severity describes technical impact.

Use:

* CRITICAL
* HIGH
* MEDIUM
* LOW
* INFO

Confidence describes certainty.

Use:

* CONFIRMED
* LIKELY
* POTENTIAL
* INFORMATIONAL

Examples:

A severe-looking issue without sufficient evidence may be:

```text
HIGH / POTENTIAL
```

A small but directly reproducible issue may be:

```text
LOW / CONFIRMED
```

Do not artificially raise severity because confidence is high.

---

## 7. Verification Status Must Be Explicit

Use one of:

* VERIFIED
* UNVERIFIED
* NOT_APPLICABLE
* VERIFICATION_FAILED
* REFUTED

A finding should not be described as verified unless deterministic evidence or direct reproduction exists.

---

## 8. Prefer Verification Over Speculation

When a meaningful finding can be verified safely, attempt verification.

Preferred methods include:

* existing tests;
* generated regression tests;
* pytest;
* coverage;
* Ruff;
* Bandit;
* Semgrep;
* pip-audit;
* type checking;
* repository inspection.

Verification must be safe and isolated.

Do not perform destructive actions against external systems.

---

## 9. Generated Verification Tests

Temporary verification tests may be created when needed to prove or disprove a finding.

Requirements:

* use synthetic data;
* avoid production services;
* avoid external destructive APIs;
* remain isolated from production behavior;
* clearly identify that the test is verification evidence.

A generated verification test must not silently become a permanent production test unless explicitly requested.

---

## 10. Avoid Review Noise

Do not create findings for:

* trivial formatting;
* subjective naming preferences;
* stylistic differences already enforced by tooling;
* unrelated refactoring opportunities;
* duplicated findings;
* low-value commentary without clear impact.

Prioritize actionable engineering findings.

---

## 11. Do Not Duplicate Deterministic Tool Output

Static analyzers are evidence sources, not review output generators.

Do not copy every Ruff, Bandit, Semgrep, or other analyzer warning into the final review.

Instead:

1. collect tool findings;
2. validate relevance to the Pull Request;
3. deduplicate;
4. interpret impact;
5. report only meaningful items.

---

## 12. Review the Change, Not the Entire Repository

The primary review scope is the Pull Request.

Repository-wide issues should only be reported when:

* the Pull Request introduces them;
* the Pull Request materially worsens them;
* they directly affect the changed behavior;
* they are necessary to understand the risk.

Do not turn a Pull Request review into an unrelated repository audit.

---

## 13. Identify Introduced vs Existing Issues

Whenever possible, distinguish:

```text
INTRODUCED_BY_PR
PRE_EXISTING
UNCERTAIN
```

The final review should prioritize issues introduced or exposed by the Pull Request.

Do not blame the Pull Request for unrelated historical defects.

---

## 14. Assess Test Impact

For meaningful code changes, determine whether existing tests cover:

* successful behavior;
* failure behavior;
* edge cases;
* authorization boundaries;
* regression risks.

If tests are missing, describe the missing behavior rather than simply stating:

```text
"Needs more tests."
```

Prefer:

```text
"No regression test covers cross-organization access after the new authorization branch."
```

---

## 15. Detect Behavior Changes

Identify whether the Pull Request changes:

* public APIs;
* function signatures;
* database schemas;
* configuration;
* environment variables;
* queue behavior;
* persistence semantics;
* authentication;
* authorization;
* error handling;
* retry behavior.

Potential breaking changes should be reported explicitly.

---

## 16. Inspect Security-Sensitive Boundaries

Security analysis should be triggered when changes affect:

* authentication;
* authorization;
* user-controlled input;
* SQL;
* shell execution;
* file paths;
* URLs;
* deserialization;
* secrets;
* tokens;
* sessions;
* cryptography;
* uploads;
* permissions.

Trace data from source to sink when practical.

---

## 17. Inspect Database Changes Carefully

When a Pull Request affects database behavior, inspect:

* migrations;
* indexes;
* constraints;
* nullability;
* foreign keys;
* transaction boundaries;
* query count;
* N+1 patterns;
* destructive migration behavior;
* rollback implications.

Do not treat schema changes as ordinary code changes.

---

## 18. Inspect Asynchronous Changes Carefully

When a Pull Request changes background jobs or queues, inspect:

* retries;
* timeouts;
* idempotency;
* duplicate execution;
* failure handling;
* queue routing;
* serialization;
* observability.

Avoid assuming that successful enqueue means successful execution.

---

## 19. Inspect API Contracts

When routes, schemas, serializers, or response objects change:

* inspect OpenAPI or Swagger definitions if present;
* compare implementation with documentation;
* identify undocumented breaking changes;
* validate status codes;
* validate required fields;
* validate authentication requirements.

---

## 20. Use Existing Repository Conventions

Before recommending changes, inspect current project patterns.

Prefer consistency with established repository conventions unless those conventions create a meaningful defect.

Do not introduce a new architectural style merely because it is preferred in another project.

---

## 21. Minimize Scope During Remediation

If remediation is explicitly requested:

* fix only the identified issue;
* preserve existing public behavior unless intentionally changed;
* avoid unrelated refactoring;
* add or update relevant tests;
* run verification after the change.

Prefer small, reviewable patches.

---

## 22. Always Re-Verify After Modification

After any remediation:

1. run focused tests;
2. run affected test suites;
3. run relevant static checks;
4. verify the original finding is resolved;
5. confirm no obvious regression was introduced.

Do not mark a remediation as complete without verification.

---

## 23. Record Structured Findings

Every finding should use a consistent representation containing, where applicable:

```text
id
category
severity
confidence
status
title
description
file
line
evidence
impact
recommendation
verification_status
introduced_by_pr
```

Structured findings should be machine-readable when possible.

---

## 24. Produce Metrics

Each review should capture measurable output when available.

Examples:

* files changed;
* files analyzed;
* lines added;
* lines removed;
* reviewers executed;
* findings by severity;
* findings by confidence;
* findings verified;
* tests executed;
* tests passed;
* tests failed;
* generated verification tests;
* analysis duration.

Metrics should reflect actual execution.

Do not invent values.

---

## 25. Preserve Raw Evidence

When tools are executed, preserve raw evidence separately from synthesized findings when practical.

Suggested destinations:

```text
reports/raw/
reports/verification/
reports/findings/
reports/reviews/
reports/metrics/
```

This supports auditability and benchmark evaluation.

---

## 26. Never Expose Secrets

Do not print, persist, or commit:

* tokens;
* API keys;
* passwords;
* private keys;
* webhook secrets;
* database credentials.

If a secret is discovered during review:

1. redact it from output;
2. describe the issue without reproducing the secret;
3. recommend rotation when relevant.

---

## 27. Use Safe Data

Use synthetic data for:

* tests;
* verification;
* benchmark cases;
* demonstrations.

Do not use confidential repositories or personal information in hackathon benchmark material.

---

## 28. Final Review Quality

The final review should be:

* concise;
* evidence-based;
* prioritized;
* actionable;
* free of duplicates;
* focused on the Pull Request.

The goal is not to maximize the number of comments.

The goal is to improve developer decision-making with minimal review noise.

---

## 29. Default Decision Rule

When evidence is insufficient:

do not guess.

Classify the finding as:

```text
POTENTIAL / UNVERIFIED
```

or omit it when the signal is too weak.

A smaller set of reliable findings is better than a large set of speculative comments.