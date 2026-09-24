# Review Synthesis Skill

## Purpose

This skill consolidates all Pull Request review findings and verification results into a final developer-facing review.

Its goal is to produce a concise, prioritized, evidence-based review with minimal noise.

It must not rediscover defects from scratch.

It should operate on findings already produced by specialized reviewers and enriched by the verification layer.

---

# Core Principle

The final review should answer:

```text id="a2ko15"
What matters?

Why does it matter?

What evidence supports it?

What should the developer do?

What remains uncertain?
```

The final review should not be a dump of every analyzer warning or every specialist observation.

---

# When to Use

Use this skill after:

```text id="g512aa"
pr-understanding
change-impact
specialized reviews
finding-verification
```

have completed.

This should be the final analytical stage before optional GitHub publication.

---

# Inputs

Recommended inputs:

```text id="50nszx"
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/change-impact.json

reports/findings/<pr-id>/code-review.json
reports/findings/<pr-id>/security-review.json
reports/findings/<pr-id>/test-impact.json
reports/findings/<pr-id>/architecture-review.json
reports/findings/<pr-id>/database-review.json
reports/findings/<pr-id>/api-review.json
reports/findings/<pr-id>/queue-review.json

reports/verification/<pr-id>/verification-results.json
```

plus review metrics when available.

---

# Phase 1 — Load Findings

Load all findings from active reviewers.

Ignore reviewer artifacts that were not selected for the current Pull Request.

Do not assume every review category was executed.

---

# Phase 2 — Merge Verification Results

For each finding, attach:

```text id="xaugu7"
verification_status
verification_method
verification_evidence
updated confidence
publishable recommendation
```

Preserve the original finding identity.

---

# Phase 3 — Remove Refuted Findings

Findings marked:

```text id="l0v47k"
REFUTED
```

must not appear as defects in the final review.

They may be included only in internal metrics or verification summaries.

---

# Phase 4 — Handle Verification Failures

For:

```text id="m8p174"
VERIFICATION_FAILED
```

decide whether the underlying finding still has enough direct evidence.

Possible handling:

```text id="e0s84a"
strong direct evidence
→ include with uncertainty

weak evidence
→ omit
```

Never imply successful verification.

---

# Phase 5 — Deduplicate Findings

Multiple reviewers may report the same root cause.

Example:

```text id="9ieipr"
SEC-001
CODE-004
TEST-003
```

may all relate to:

```text id="fbhaqz"
missing tenant scoping
```

Produce one consolidated finding.

Preserve evidence from all relevant sources.

---

# Deduplication Rules

Findings may be duplicates when they share:

```text id="153ope"
same changed code
same root cause
same impact
same remediation
```

Do not merge findings merely because they occur in the same file.

---

# Phase 6 — Root Cause Grouping

When multiple symptoms result from one cause, prefer grouping.

Example:

```text id="82cuu0"
Root cause:
missing organization filter

Symptoms:
- unauthorized read
- unauthorized update
- missing tenant test
```

Final review may present:

```text id="vakeip"
HIGH — Missing tenant scoping in report lookup
```

with the test gap as supporting evidence rather than a separate blocking comment.

---

# Phase 7 — Prioritize Findings

Recommended priority order:

```text id="vdoqwi"
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Within the same severity, prefer:

```text id="9u1gnl"
VERIFIED
CONFIRMED direct evidence
LIKELY
POTENTIAL
```

---

# Phase 8 — Separate Blocking From Advisory

Classify findings as:

```text id="yq8cbw"
BLOCKING
NON_BLOCKING
ADVISORY
```

Suggested interpretation:

## BLOCKING

Issues that should normally be addressed before merge.

Examples:

```text id="4268ms"
verified authorization bypass
migration that fails on existing data
major breaking API regression
data corruption risk
```

## NON_BLOCKING

Important issues that should be addressed but may not always block merge.

## ADVISORY

Low-impact or informational recommendations.

Do not derive this classification from severity mechanically.

---

# Phase 9 — Avoid Overall Approval Decisions

The final output should provide evidence and findings, not make a merge decision unless explicitly required by the integration workflow.

Prefer:

```text id="1sh41v"
2 blocking findings remain
```

instead of:

```text id="3q18qw"
Do not merge.
```

The developer or team remains responsible for the decision.

---

# Phase 10 — Compose Executive Summary

Produce a concise summary.

Example:

```text id="g5bh2u"
This Pull Request introduces API-key authentication and affects
authentication, authorization, persistence, and API contracts.

The review identified two blocking findings:
one verified cross-tenant authorization issue and one migration-safety issue.

Three additional non-blocking test and documentation gaps were identified.
```

Keep this section short.

---

# Phase 11 — Present Blocking Findings First

Each important finding should include:

```text id="krx0sr"
severity
confidence
verification status
title
location
impact
evidence
recommendation
```

Example:

```text id="gjj2u2"
HIGH · CONFIRMED · VERIFIED

Cross-tenant report access is possible

app/api/reports.py:72

The report lookup uses a global ID without organization scoping.
A generated regression test reproduced the issue: a token from
Organization A accessed a report owned by Organization B.

Recommendation:
Scope the lookup to the authenticated organization and retain the
regression test.
```

---

# Phase 12 — Keep Findings Concise

Avoid large essays.

Each finding should explain:

```text id="1gv4fo"
problem
evidence
impact
fix direction
```

Detailed raw evidence remains in report artifacts.

---

# Phase 13 — Inline Comment Eligibility

Mark findings as inline-comment candidates when:

```text id="leq13x"
specific changed line exists
finding is actionable
confidence is high
finding is not duplicate noise
```

Preferred:

```text id="wpxrh4"
VERIFIED
CONFIRMED
LIKELY with strong evidence
```

Avoid inline comments for speculative or broad architectural observations.

---

# Phase 14 — Summary-Only Findings

Keep findings in the summary rather than inline when they concern:

```text id="7xj04d"
architecture-wide impact
missing tests across several files
migration strategy
overall API compatibility
general observability
```

---

# Phase 15 — Test Gap Presentation

Do not produce multiple comments saying:

```text id="hb2x18"
needs tests
```

Instead group missing coverage.

Example:

```text id="a7lx86"
Test coverage gaps

The new API-key flow has no tests for:
- revoked keys
- cross-tenant access
- malformed credentials
```

---

# Phase 16 — Architecture Findings

Architecture findings should be included only when:

* impact is concrete;
* evidence is clear;
* remediation is actionable.

Avoid design commentary that does not materially affect maintainability.

---

# Phase 17 — Tool Findings

Do not dump raw output from:

```text id="aryr9o"
Ruff
Bandit
Semgrep
pip-audit
mypy
```

Use them only as supporting evidence.

Example:

```text id="ovjp0i"
Semgrep independently identified the same unsafe subprocess path.
```

---

# Phase 18 — Preserve Uncertainty

When a finding remains uncertain, say so.

Example:

```text id="fxfehi"
MEDIUM · POTENTIAL · UNVERIFIED
```

Do not rewrite uncertainty into certainty during synthesis.

---

# Phase 19 — Recommendations

Recommendations should be:

```text id="22h7ss"
specific
minimal
aligned with repository conventions
```

Avoid vague recommendations such as:

```text id="92u68g"
Improve security.
```

Prefer:

```text id="f83tkr"
Scope ReportRepository.get_by_id() by organization_id and add a cross-tenant regression test.
```

---

# Phase 20 — Do Not Auto-Fix During Synthesis

This skill is responsible for review generation only.

Do not modify production code.

If remediation is requested later, use a separate implementation task.

---

# Phase 21 — Metrics Summary

Include review metrics when useful.

Example:

```text id="k61q5f"
Files analyzed: 14
Specialized reviewers: 5
Initial findings: 12
Verified findings: 6
Refuted findings: 2
Final publishable findings: 7
Generated verification tests: 3
```

Metrics must come from actual artifacts.

---

# Phase 22 — False Positive Reduction

If verification refuted findings, surface this as an internal quality metric.

Example:

```text id="a3z6hi"
Initial findings: 14
Refuted during verification: 3
Final findings: 9
```

This demonstrates review filtering.

Do not imply perfect accuracy.

---

# Phase 23 — Reviewer Coverage

Optionally summarize which reviewers ran.

Example:

```text id="0z1qg7"
Executed reviewers:
- code-review
- security-review
- test-impact
- database-review
- api-review
```

This improves transparency.

---

# Phase 24 — Final Review Structure

Use:

```text id="pwxp4s"
# Pull Request Review

## Summary

## Blocking Findings

## Non-Blocking Findings

## Test Coverage Gaps

## Advisory Notes

## Verification Summary

## Review Metrics
```

Omit empty sections.

---

# Phase 25 — GitHub-Friendly Format

The Markdown should render cleanly in GitHub.

Avoid:

* oversized tables;
* excessive nesting;
* very long paragraphs;
* unnecessary raw JSON;
* tool logs.

Keep the review easy to scan.

---

# Phase 26 — Finding Format

Recommended Markdown:

```text id="8sec0f"
### HIGH · VERIFIED — Cross-tenant report access

`app/api/reports.py:72`

The new report lookup is not scoped to the authenticated organization.

**Evidence**
- repository lookup uses only report ID
- generated regression test returned HTTP 200 for another tenant's report

**Impact**
Users may access reports belonging to other organizations.

**Recommendation**
Scope the lookup by organization and keep the regression test.
```

---

# Phase 27 — Inline Finding Payload

For findings eligible for GitHub inline comments, generate a machine-readable representation.

Example:

```json id="ca2r54"
{
  "finding_id": "SEC-001",
  "file": "app/api/reports.py",
  "line": 72,
  "publish_inline": true,
  "body": "The new report lookup is not scoped to the authenticated organization..."
}
```

Store separately from human Markdown.

---

# Phase 28 — GitHub Review Action

The synthesis output may recommend one of:

```text id="rwde13"
COMMENT
REQUEST_CHANGES
```

only if the integration explicitly requires GitHub review actions.

Do not automatically publish.

A human or higher-level orchestration step should control publication.

---

# Phase 29 — Review Action Guidance

If an action must be suggested:

```text id="74q6sx"
verified blocking finding exists
→ REQUEST_CHANGES may be appropriate

no blocking findings
→ COMMENT
```

This is workflow guidance, not a substitute for human merge policy.

---

# Phase 30 — Suppress Weak Findings

Omit findings that are:

```text id="crqem7"
POTENTIAL + low impact + unverified
duplicate
pure style
unsupported
refuted
```

Review quality improves when low-value noise is removed.

---

# Phase 31 — Preserve Traceability

Every final finding should reference its source finding IDs internally.

Example:

```json id="yriblg"
{
  "final_id": "FINAL-001",
  "source_findings": [
    "SEC-001",
    "TEST-003"
  ]
}
```

This allows auditability.

---

# Phase 32 — Consolidated Finding Model

Recommended structure:

```json id="dbduko"
{
  "id": "FINAL-001",
  "severity": "HIGH",
  "confidence": "CONFIRMED",
  "verification_status": "VERIFIED",
  "priority": "BLOCKING",
  "title": "Cross-tenant report access",
  "file": "app/api/reports.py",
  "line": 72,
  "description": "...",
  "evidence": [],
  "impact": "...",
  "recommendation": "...",
  "source_findings": [
    "SEC-001",
    "TEST-003"
  ],
  "publish_inline": true
}
```

---

# Required Output

Generate:

```text id="3m5m20"
reports/reviews/<pr-id>/review.md
```

and:

```text id="mhsarg"
reports/reviews/<pr-id>/review.json
```

The JSON representation is canonical for integrations.

---

# GitHub Publication Artifact

If publication integration is enabled, also generate:

```text id="q98tfj"
reports/reviews/<pr-id>/github-review.json
```

Example:

```json id="3lvt7a"
{
  "body": "Pull Request review summary...",
  "comments": [
    {
      "path": "app/api/reports.py",
      "line": 72,
      "body": "..."
    }
  ]
}
```

Do not publish directly from this skill.

---

# Metrics

Record:

```text id="ekf99r"
initial_findings
refuted_findings
duplicate_findings_removed
low_value_findings_suppressed

final_findings
blocking_findings
non_blocking_findings
advisory_findings

critical_findings
high_findings
medium_findings
low_findings

verified_final_findings
unverified_final_findings

inline_comments
summary_only_findings

reviewers_executed
```

Save:

```text id="hl9hwt"
reports/metrics/<pr-id>-review-synthesis.json
```

---

# Quality Metrics

Useful project-level metrics include:

```text id="7x7hny"
initial findings
        ↓
verification
        ↓
deduplication
        ↓
final findings
```

Example:

```text id="x6d3cy"
Initial:       17
Refuted:        3
Duplicates:     2
Suppressed:     2
Final:         10
```

This demonstrates noise reduction.

---

# Example Final Review

```text id="rr9ng5"
# Pull Request Review

## Summary

This PR adds API-key authentication and modifies authentication,
authorization, database, and API behavior.

Two blocking findings were identified and independently verified.

## Blocking Findings

### HIGH · VERIFIED — Cross-tenant report access

`app/api/reports.py:72`

The new report lookup is not scoped to the authenticated organization.

A generated regression test reproduced access to an Organization B
resource using Organization A credentials.

Recommendation: scope the repository lookup by organization and keep
the regression test.

### HIGH · VERIFIED — Migration fails for existing users

`migrations/20260924_add_org.py:18`

The migration introduces a non-null organization_id without backfilling
existing rows.

Recommendation: use a staged migration.

## Test Coverage Gaps

The API-key flow still lacks coverage for revoked credentials.

## Verification Summary

Reviewed findings: 9
Verified: 5
Refuted: 2
Unverified: 1
Not applicable: 1
```

---

# What This Skill Must Not Do

Do not:

* invent new findings;
* override verification evidence;
* hide refuted findings from internal metrics;
* publish raw analyzer output;
* modify production code;
* automatically publish GitHub comments;
* maximize comment count;
* remove uncertainty from unverified findings.

---

# Completion Criteria

The skill is complete when:

* all active reviewer findings are loaded;
* verification results are merged;
* refuted findings are excluded;
* duplicates are consolidated;
* findings are prioritized;
* low-value noise is removed;
* final Markdown and JSON reviews are generated;
* inline-comment candidates are identified;
* metrics are persisted.

---

# Engineering Principle

The quality of a Pull Request review is not measured by how many comments it contains.

The goal is:

> Deliver the smallest set of high-value findings that gives the developer the strongest evidence about what matters before merge.