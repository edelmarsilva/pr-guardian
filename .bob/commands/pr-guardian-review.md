# PR Guardian Review

Run the complete PR Guardian evidence-based Pull Request review workflow.

The argument supplied to this command identifies the Pull Request to review.

Accepted forms:

```text
owner/repository#42
https://github.com/owner/repository/pull/42
```

---

# Objective

Perform an evidence-based, repository-aware Pull Request review using the PR Guardian harness.

The workflow must:

1. retrieve the Pull Request;
2. prepare the repository workspace;
3. build repository-aware context;
4. determine which specialist reviewers are relevant;
5. execute only selected reviewers;
6. collect structured findings;
7. independently verify important findings;
8. remove refuted and duplicate findings;
9. generate the final review;
10. persist metrics and evidence.

The final objective is not to maximize comments.

The objective is to produce the smallest useful set of high-confidence findings.

---

# Core Principles

Always preserve these four PR Guardian principles:

```text
CONTEXTUAL
Understand more than the diff.

ADAPTIVE
Run only relevant reviewers.

MULTI-AGENT
Use specialized independent reviewers.

EVIDENCE-BASED
Verify important claims whenever practical.
```

---

# Mandatory Project Context

Before executing the review:

1. read `AGENTS.md`;
2. read `.bob/rules-agent/01-project-rules.md`;
3. load the `pr-understanding` skill;
4. load the `change-impact` skill.

Do not begin specialized review before repository context has been established.

---

# Step 1 — Parse Pull Request Reference

Extract:

```text
owner
repository
pull_number
```

from the command argument.

Reject malformed Pull Request references.

Do not guess missing repository information.

---

# Step 2 — Prepare Pull Request

Use the PR Guardian Python tooling to retrieve the Pull Request and prepare its local workspace.

The preparation step must obtain:

```text
title
description
base SHA
head SHA
changed files
patches
commits
```

and clone or prepare the repository under:

```text
workspace/repositories/<pr-id>/
```

The repository must be checked out at the exact Pull Request HEAD commit.

---

# Step 3 — Build Context

Build the structured Pull Request context.

Persist:

```text
reports/raw/<pr-id>/pr-context.json
```

The context should include, when available:

```text
changed files
changed symbols
repository structure
direct dependencies
affected files
call relationships
existing tests
recent relevant history
risk signals
API specifications
database migrations
queue or worker components
```

Do not review only the patch.

---

# Step 4 — Determine Reviewer Routing

Run the adaptive routing logic.

Persist:

```text
reports/raw/<pr-id>/routing.json
```

The available specialist reviewers are:

```text
code-review
security-review
test-impact
architecture-review
database-review
api-review
queue-review
```

Do not execute every reviewer automatically.

Only execute reviewers selected by the routing evidence.

---

# Step 5 — Create Review Plan

Before spawning reviewer subagents, summarize:

```text
Pull Request intent
changed domains
risk signals
selected reviewers
skipped reviewers
verification opportunities
```

Keep the plan concise.

Do not perform the specialist reviews in this step.

---

# Step 6 — Spawn Specialist Reviewers

For every selected reviewer, spawn an independent subagent.

Prefer parallel execution when reviewer tasks do not depend on one another.

Each reviewer receives:

```text
PR metadata
pr-context.json
change-impact information
local repository workspace
changed files
relevant diff
```

Each reviewer must use the corresponding PR Guardian skill.

Mapping:

```text
code-review
→ .bob/skills/code-review/

security-review
→ .bob/skills/security-review/

test-impact
→ .bob/skills/test-impact/

architecture-review
→ .bob/skills/architecture-review/

database-review
→ .bob/skills/database-review/

api-review
→ .bob/skills/api-review/

queue-review
→ .bob/skills/queue-review/
```

---

# Reviewer Isolation

Reviewer subagents must analyze independently.

Do not show one reviewer's conclusions to another reviewer before both have completed unless a dependency is explicitly required.

This reduces confirmation bias.

---

# Reviewer Permissions

General specialist reviewers should primarily use:

```text
Read
Execute
Skill
```

They should not modify production source code.

`test-impact` may create temporary verification artifacts only when required.

---

# Step 7 — Required Reviewer Output

Every reviewer must write its findings to:

```text
reports/findings/<pr-id>/<reviewer>.json
```

The canonical structure is:

```json
{
  "reviewer": "security-review",
  "findings": [
    {
      "id": "SEC-001",
      "category": "TENANT_ISOLATION",
      "severity": "HIGH",
      "confidence": "LIKELY",
      "title": "Report lookup is not scoped by organization",
      "description": "The changed lookup uses only report ID.",
      "file": "app/repositories.py",
      "line": 24,
      "evidence": [
        "ReportRepository.get_by_id accepts only report_id",
        "organization_id is available at the route but not used by the repository lookup"
      ],
      "impact": "A tenant may retrieve another tenant's resource.",
      "recommendation": "Scope the lookup using the authenticated organization.",
      "verification_status": "UNVERIFIED",
      "origin": "INTRODUCED_BY_PR",
      "reviewer": "security-review",
      "metadata": {
        "root_cause": "report lookup missing organization scope"
      }
    }
  ]
}
```

Output must be valid JSON.

Do not add Markdown around JSON files.

---

# Finding Requirements

A finding must contain enough evidence for another engineer or verifier to inspect it.

Do not report:

```text
generic best-practice comments
subjective style preferences
speculative concerns without a concrete code path
tool output without contextual interpretation
```

Prefer zero findings over unsupported findings.

---

# Step 8 — Collect Findings

After all selected reviewer subagents complete:

1. read every generated reviewer artifact;
2. validate JSON structure;
3. normalize findings;
4. preserve reviewer attribution.

Do not discard reviewer artifacts.

---

# Step 9 — Select Verification Candidates

Load the `finding-verification` skill.

Prioritize:

```text
CRITICAL findings
HIGH findings
authorization issues
tenant-isolation issues
security issues
data-integrity issues
breaking API changes
migration failures
queue idempotency issues
behavioral regressions
```

Do not spend significant verification effort on low-value informational findings.

---

# Step 10 — Generate Targeted Verification Tests

When a finding can be reproduced behaviorally, spawn an independent verification subagent.

The verifier may create temporary tests only under:

```text
reports/verification/<pr-id>/tests/
```

The test must express the expected correct behavior.

Example:

```python
def test_cross_tenant_access_is_denied():
    response = client.get(
        "/reports/2",
        headers={
            "X-Organization-ID": "100"
        },
    )

    assert response.status_code in {
        403,
        404,
    }
```

A test must not be written merely to force failure.

It must represent a legitimate expected invariant.

---

# Step 11 — Deterministic Verification

Use deterministic tools when appropriate.

Available verification mechanisms may include:

```text
pytest
pytest-cov
Ruff
Bandit
Semgrep
pip-audit
OpenAPI comparison
migration execution
database tests
queue tests
```

Tool output is evidence.

Tool output is not automatically a PR Guardian finding.

---

# Step 12 — Interpret Verification Results

Use:

```text
VERIFIED
UNVERIFIED
NOT_APPLICABLE
VERIFICATION_FAILED
REFUTED
```

Rules:

```text
test reproduces the suspected defect
→ VERIFIED

direct deterministic evidence confirms mismatch
→ VERIFIED

verification contradicts the finding
→ REFUTED

environment prevents verification
→ VERIFICATION_FAILED

insufficient evidence
→ UNVERIFIED
```

Never convert uncertainty into confirmation without evidence.

---

# Step 13 — Preserve Verification Evidence

Write:

```text
reports/verification/<pr-id>/verification-results.json
```

Also preserve relevant raw outputs under:

```text
reports/raw/<pr-id>/
```

Examples:

```text
pytest-verification.txt
bandit.json
semgrep.json
pip-audit.json
migration-test.txt
```

---

# Step 14 — Review Synthesis

Load the `review-synthesis` skill.

The synthesis step must:

```text
attach verification results
remove REFUTED findings
deduplicate findings with the same root cause
suppress low-value unsupported noise
prioritize important findings
preserve uncertainty
```

Do not discover new defects during synthesis.

---

# Step 15 — Root-Cause Consolidation

When multiple reviewers identify the same underlying defect, create one final finding.

Example:

```text
SEC-001
CODE-004
TEST-003
```

may represent:

```text
missing organization scope in report lookup
```

The final finding should retain:

```text
source_findings
source_reviewers
combined evidence
```

---

# Step 16 — Final Review Artifacts

Generate:

```text
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md
```

The final review should contain, when applicable:

```text
Summary

Blocking Findings

Non-Blocking Findings

Test Coverage Gaps

Advisory Notes

Verification Summary

Review Metrics
```

Omit empty sections.

---

# Step 17 — Metrics

Generate measurable review metrics.

At minimum capture:

```text
available reviewers
selected reviewers
skipped reviewers

initial findings
verified findings
refuted findings
duplicate findings removed
suppressed findings
final findings

generated verification tests
reviewer execution durations
total analysis duration
```

Persist metrics under:

```text
reports/metrics/
```

---

# Step 18 — Adaptive Routing Metric

Calculate:

```text
reviewers skipped
-----------------
available reviewers
```

Do not present this as a quality score.

Present it as resource reduction.

---

# Step 19 — Finding Reduction Metric

Capture:

```text
initial findings
        ↓
refuted
        ↓
duplicates removed
        ↓
weak findings suppressed
        ↓
final findings
```

This demonstrates noise reduction.

---

# Step 20 — Do Not Publish Automatically

Do not automatically submit GitHub review comments.

The workflow should first generate:

```text
review.json
review.md
```

and present the result to the user.

Publishing to GitHub requires a separate explicit action.

---

# Step 21 — Final Task Summary

When the workflow completes, report:

```text
PR reviewed
changed files
selected reviewers
skipped reviewers

initial findings
verified findings
refuted findings
final findings

generated verification tests

review artifact path
metrics artifact path
```

Also explicitly identify any:

```text
reviewer failures
verification failures
missing tools
incomplete analysis
```

Do not hide degraded coverage.

---

# Demo-Sensitive Behavior

This workflow is used for the IBM Bob hackathon.

Use Bob capabilities visibly and meaningfully:

```text
Agent Mode
Skills
Subagents
parallelizable work
Execute tools
repository context
structured artifacts
```

Do not create fake Bob results.

Do not pre-populate findings before reviewers execute.

All benchmark results must come from actual workflow execution.

---

# Safety

Never:

```text
use production credentials
modify production data
run destructive database operations
perform active attacks against unauthorized systems
publish secrets
send real emails
charge real payment methods
```

Use synthetic or authorized test environments.

---

# Completion Condition

The workflow is complete only when:

```text
context exists
routing exists
selected reviewers completed or failures were recorded
findings were collected
verification was attempted where appropriate
review synthesis completed
final review artifacts exist
metrics exist
```

The final principle is:

> Don't just comment. Prove it.