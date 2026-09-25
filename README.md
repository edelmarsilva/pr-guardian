# PR Guardian

> **Evidence-Based Multi-Agent Pull Request Review powered by IBM Bob**

**Don't just comment. Prove it.**

PR Guardian is a Pull Request review harness designed to reduce noisy AI review comments and improve review quality through repository context, adaptive specialist routing, independent verification, and evidence-based synthesis.

Instead of sending every Pull Request to every reviewer and publishing every AI-generated concern, PR Guardian builds repository context first, selects only the relevant specialist agents, verifies important findings with deterministic evidence whenever possible, and publishes only the final high-signal review.

---

## The Problem

AI-assisted code review can accelerate development, but it also introduces a new problem:

```text
more automated comments
does not necessarily mean
better code review
```

Traditional AI review workflows may:

* analyze only the Pull Request diff;
* apply the same generic reviewer to every change;
* generate speculative findings;
* duplicate the same issue across different review perspectives;
* report best-practice suggestions as if they were defects;
* publish findings without independently verifying them.

This can increase review noise and reduce developer trust.

PR Guardian is designed around a different question:

> Can an AI reviewer produce fewer, stronger, and more verifiable findings?

---

# Core Principles

PR Guardian is built around four principles.

## Contextual

**Understand more than the diff.**

Before reviewing the change, PR Guardian builds repository-aware context that may include:

* changed files;
* changed symbols;
* repository structure;
* direct dependencies;
* affected modules;
* call relationships;
* existing tests;
* API specifications;
* database migrations;
* background workers;
* relevant repository history;
* security and architecture risk signals.

A change in one file may affect behavior elsewhere.

PR Guardian attempts to identify that context before specialist review begins.

---

## Adaptive

**Run only the reviewers that matter.**

A documentation-only change should not automatically trigger security, database, API, and queue reviewers.

PR Guardian analyzes the Pull Request and dynamically selects relevant review domains.

Example:

```text
README.md changed

Selected:
minimal review

Skipped:
security
database
queue
API
```

Another Pull Request may change:

```text
auth.py
models.py
migration.sql
```

and activate:

```text
code-review
security-review
test-impact
database-review
architecture-review
```

Reviewer selection is recorded so the process remains explainable.

---

## Multi-Agent

**Use specialized independent reviewers.**

PR Guardian separates review concerns into specialist agents.

Available review domains include:

```text
code-review
security-review
test-impact
architecture-review
database-review
api-review
queue-review
```

Each specialist uses its own IBM Bob skill and focuses on a specific engineering concern.

The reviewers produce structured findings independently before final synthesis.

This reduces the tendency for one large prompt to mix unrelated concerns.

---

## Evidence-Based

**Important findings should be supported by evidence.**

Reviewer findings are treated as hypotheses.

PR Guardian attempts to independently verify important findings using deterministic mechanisms such as:

* generated regression tests;
* existing tests;
* direct repository evidence;
* Ruff;
* Bandit;
* Semgrep;
* pip-audit;
* OpenAPI comparison;
* migration execution;
* database integration tests;
* queue execution tests.

A finding may become:

```text
VERIFIED
UNVERIFIED
NOT_APPLICABLE
VERIFICATION_FAILED
REFUTED
```

A refuted finding is removed before the final review is produced.

---

# Architecture

The high-level workflow is:

```text
GitHub Pull Request
        │
        ▼
Pull Request Ingestion
        │
        ▼
Repository Preparation
        │
        ▼
Context Builder
        │
        ▼
Adaptive Reviewer Router
        │
        ▼
IBM Bob Specialist Subagents
   ┌────┼────┬────┬────┐
   ▼    ▼    ▼    ▼    ▼
 Code Security API DB  Test ...
   └────┼────┴────┴────┘
        ▼
Structured Findings
        │
        ▼
Finding Verification
        │
        ▼
Deduplication + Noise Reduction
        │
        ▼
Review Synthesis
        │
        ▼
review.json
review.md
metrics
        │
        ▼
Optional GitHub Publication
```

---

# IBM Bob Integration

IBM Bob is the agentic execution layer of PR Guardian.

The project uses:

* Agent Mode;
* custom skills;
* custom modes;
* specialist subagents;
* project rules;
* structured output contracts;
* command execution;
* repository-aware analysis.

The repository supplies Bob command and specialist instructions; Python preparation/finalization does not itself launch Bob agents. Bob IDE execution must be performed separately, and native Bob compatibility has not been verified in this environment.

The main Bob command is:

```text
/pr-guardian-review owner/repository#42
```

or:

```text
/pr-guardian-review https://github.com/owner/repository/pull/42
```

The workflow prepares the Pull Request, determines the relevant reviewers, executes specialist agents, validates their structured findings, verifies important findings, and generates the final review.

---

# Repository Structure

```text
pr-guardian/
├── AGENTS.md
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── run.py
│
├── .bob/
│   ├── commands/
│   │   └── pr-guardian-review.md
│   │
│   ├── custom_modes.yaml
│   │
│   ├── rules-agent/
│   │   └── 01-project-rules.md
│   │
│   ├── rules-plan/
│   │   └── 01-planning-rules.md
│   │
│   └── skills/
│       ├── pr-understanding/
│       ├── change-impact/
│       ├── code-review/
│       ├── security-review/
│       ├── test-impact/
│       ├── architecture-review/
│       ├── database-review/
│       ├── api-review/
│       ├── queue-review/
│       ├── finding-verification/
│       └── review-synthesis/
│
├── app/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
│
├── guardian/
│   ├── context_builder.py
│   ├── router.py
│   ├── finding_verifier.py
│   ├── review_synthesizer.py
│   ├── metrics.py
│   └── orchestrator.py
│
├── github/
│   ├── client.py
│   ├── pull_request.py
│   ├── reviews.py
│   ├── review_mapper.py
│   ├── diff_mapper.py
│   ├── webhooks.py
│   └── webhooks_service.py
│
├── repository/
│   ├── clone.py
│   ├── diff.py
│   ├── files.py
│   ├── dependencies.py
│   ├── call_graph.py
│   └── history.py
│
├── analyzers/
│   ├── static/
│   ├── tests/
│   └── security/
│
├── models/
│
├── schemas/
│   ├── finding.schema.json
│   └── verification.schema.json
│
├── scripts/
│   ├── prepare_review.py
│   ├── finalize_review.py
│   ├── validate_artifact.py
│   └── publish_review.py
│
├── reports/
│   ├── raw/
│   ├── findings/
│   ├── verification/
│   ├── reviews/
│   └── metrics/
│
├── benchmark/
│   ├── datasets/
│   ├── expected-findings/
│   └── README.md
│
├── workspace/
│   └── repositories/
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docs/
│
└── bob_sessions/
```

---

# Requirements

Recommended environment:

```text
Python 3.11+
IBM Bob IDE
Git
GitHub access token
```

Optional tools improve verification coverage:

```text
Ruff
Bandit
Semgrep
pip-audit
OWASP ZAP
```

The review should continue in degraded mode when optional analyzers are unavailable.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USER/pr-guardian.git
cd pr-guardian
```

Create a virtual environment:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For development dependencies using `pyproject.toml`:

```bash
pip install -e ".[dev]"
```

---

# Configuration

Copy:

```bash
cp .env.example .env
```

Configure:

```dotenv
FLASK_SECRET_KEY=replace-me

GITHUB_TOKEN=replace_with_your_github_token
GITHUB_WEBHOOK_SECRET=replace_with_random_secret

PR_GUARDIAN_WORKSPACE=workspace/repositories
PR_GUARDIAN_REPORTS=reports

PR_GUARDIAN_RUN_VERIFICATION=true

PR_GUARDIAN_HOST=127.0.0.1
PR_GUARDIAN_PORT=5000
PR_GUARDIAN_DEBUG=true
```

Never commit `.env` or real credentials.

---

# Running the Dashboard

Start the Flask application:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

The dashboard allows a Pull Request to be submitted using:

```text
GitHub owner
repository
Pull Request number
```

---

# Preparing a Review

A Pull Request can be prepared independently from the dashboard:

```bash
python scripts/prepare_review.py owner/repository#42 --compact
```

The script:

```text
retrieves the Pull Request
        ↓
checks out the exact HEAD
        ↓
builds repository context
        ↓
runs adaptive routing
        ↓
creates review-plan.json
```

Generated files include:

```text
reports/raw/<pr-id>/pr-context.json
reports/raw/<pr-id>/routing.json
reports/raw/<pr-id>/review-plan.json
```

---

# Running with IBM Bob

Inside IBM Bob IDE:

```text
/pr-guardian-review owner/repository#42
```

Bob reads the generated review plan and executes only the selected specialist reviewers.

Each reviewer produces:

```text
reports/findings/<pr-id>/<reviewer>.json
```

Example:

```text
reports/findings/example-project-pr-42/
├── code-review.json
├── security-review.json
├── test-impact.json
└── database-review.json
```

A reviewer is allowed to return:

```json
{
  "reviewer": "security-review",
  "findings": []
}
```

Zero findings is a valid outcome.

PR Guardian prefers no finding over an unsupported finding.

---

# Structured Finding Contract

A finding follows a canonical structure:

```json
{
  "id": "SEC-001",
  "category": "TENANT_ISOLATION",
  "severity": "HIGH",
  "confidence": "LIKELY",
  "title": "Report lookup is not scoped by organization",
  "description": "The repository query filters only by report_id.",
  "file": "app/repositories.py",
  "line": 24,
  "evidence": [
    "organization_id is available at the route",
    "repository lookup receives only report_id"
  ],
  "impact": "Cross-tenant access may be possible.",
  "recommendation": "Scope the lookup using the authenticated organization.",
  "verification_status": "UNVERIFIED",
  "origin": "INTRODUCED_BY_PR",
  "reviewer": "security-review"
}
```

Outputs are validated using:

```text
schemas/finding.schema.json
```

---

# Validating Bob Artifacts

Validate a reviewer result before finalization:

```bash
python scripts/validate_artifact.py \
  schemas/finding.schema.json \
  reports/findings/<pr-id>/security-review.json
```

Successful validation:

```json
{
  "valid": true,
  "errors": []
}
```

Invalid artifacts must be corrected before the reviewer task is considered complete.

---

# Finding Verification

Important findings can be independently verified.

Example:

```text
Security reviewer:

"Report lookup may allow cross-tenant access."

        ↓

Verifier generates regression test

        ↓

Organization A
requests
Organization B report

        ↓

expected:
403 or 404

actual:
200

        ↓

VERIFIED
```

Generated verification tests are stored under:

```text
reports/verification/<pr-id>/tests/
```

Verification results are written to:

```text
reports/verification/<pr-id>/verification-results.json
```

---

# Verification States

PR Guardian distinguishes uncertainty from proof.

```text
VERIFIED
Evidence reproduced or confirmed the finding.

REFUTED
Verification contradicted the finding.

UNVERIFIED
No sufficient deterministic evidence was obtained.

VERIFICATION_FAILED
Verification could not complete reliably.

NOT_APPLICABLE
Deterministic verification does not meaningfully apply.
```

A `REFUTED` finding must not reach the final published review.

---

# Finalizing a Review

After Bob specialist reviewers complete:

```bash
python scripts/finalize_review.py <pr-id>
```

Outputs include:

```text
reports/reviews/<pr-id>/review.json
reports/reviews/<pr-id>/review.md

reports/verification/<pr-id>/verification-results.json

reports/metrics/<pr-id>-finalize.json
```

---

# Review Synthesis

Multiple reviewers may identify the same underlying defect.

Example:

```text
security-review
SEC-001

code-review
CODE-004

test-impact
TEST-003
```

All may refer to:

```text
missing organization scope
```

PR Guardian consolidates these into one final finding while preserving:

```text
source findings
source reviewers
combined evidence
verification result
```

This reduces duplicate review noise.

---

# GitHub Publication

Publishing is a separate explicit step.

First perform a dry run:

```bash
python scripts/publish_review.py \
  owner/repository \
  42 \
  --review reports/reviews/<pr-id>/review.json \
  --dry-run
```

The dry run does not publish anything.

It shows the payload that would be submitted.

To publish:

```bash
python scripts/publish_review.py \
  owner/repository \
  42 \
  --review reports/reviews/<pr-id>/review.json
```

The default review event is:

```text
COMMENT
```

Other supported events require explicit selection:

```text
APPROVE
REQUEST_CHANGES
```

---

# Safe Inline Comments

A valid finding is not automatically eligible for an inline GitHub comment.

PR Guardian validates:

```text
finding file exists in PR
        ↓
finding line exists
        ↓
file has a patch
        ↓
line exists in the Pull Request diff
        ↓
inline comment
```

Otherwise the finding remains in the summary.

This prevents invalid GitHub review payloads and avoids attaching comments to unrelated lines.

---

# GitHub Webhooks

The Flask application exposes:

```text
POST /webhooks/github
```

The webhook validates:

```text
X-Hub-Signature-256
```

using HMAC-SHA256.

Relevant Pull Request actions include:

```text
opened
reopened
synchronize
ready_for_review
```

Unrelated events are ignored.

For the MVP, webhook processing may run synchronously.

---

# Benchmarks

PR Guardian currently includes two synthetic vulnerable application snapshots with known defects: PR-001 (cross-tenant authorization) and PR-002 (SQL injection), under `benchmark/`. These fixtures exercise defect reproduction; they do not yet provide paired base/head commits or measured baseline-versus-Bob review results.

The scenario catalog below includes the two existing cases; PR-003 through PR-007 are planned, not implemented:

```text
PR-001
Cross-tenant authorization regression

PR-002
SQL injection

PR-003
Breaking API contract

PR-004
Unsafe migration

PR-005
Queue idempotency

PR-006
N+1 query

PR-007
Clean Pull Request
```

Expected findings for the two existing fixtures are stored separately in `benchmark/expected-findings/`. No precision, recall, reviewer-quality, or time-saving claims have been measured by this repository.

This prevents changing the expected result after seeing the review output.

---

# Benchmark Example — Cross-Tenant Access

Synthetic Pull Request:

```python
report = repository.get_by_id(
    report_id
)
```

The previous implementation used:

```python
report = repository.get_by_id(
    report_id,
    organization_id,
)
```

Verification scenario:

```text
Organization A
    ↓
requests Report B
owned by Organization B
```

Correct behavior:

```text
403 / 404
```

Vulnerable behavior:

```text
200
```

A generated regression test can independently confirm the defect.

---

# Metrics

PR Guardian intentionally avoids opaque quality scores.

Instead, it records measurable engineering behavior.

Examples:

```text
available reviewers
selected reviewers
skipped reviewers

initial findings
verified findings
refuted findings
duplicates removed
suppressed findings
final findings

verification tests generated
reviewer execution time
total review duration
```

---

## Adaptive Routing Reduction

Example:

```text
Available reviewers: 7
Selected reviewers:  3
Skipped reviewers:   4
```

Routing reduction:

```text
4 / 7 = 57.14%
```

This measures avoided reviewer execution, not code quality.

---

## Finding Reduction

Example:

```text
Initial findings:        14
Refuted:                  3
Duplicates consolidated: 2
Weak findings suppressed:1
Final findings:           8
```

This demonstrates review noise reduction.

---

# Testing

Run all tests:

```bash
pytest -v
```

Run with coverage:

```bash
pytest --cov --cov-report=term-missing
```

Important test areas include:

```text
context builder
adaptive router
finding verifier
review synthesizer
artifact validation
GitHub webhook
diff mapper
GitHub review mapper
domain models
integration pipeline
synthetic benchmarks
```

---

# Static Analysis

Run Ruff:

```bash
ruff check .
```

Run Bandit:

```bash
bandit -c pyproject.toml -r .
```

Run dependency audit:

```bash
pip-audit
```

Optional analyzers such as Semgrep may be installed independently.

Missing optional analyzers should degrade verification coverage rather than crash the entire review.

---

# Design Decisions

## Findings Are Hypotheses

Reviewer output is not automatically considered truth.

---

## Severity Is Not Confidence

A finding may be:

```text
HIGH severity
+
POTENTIAL confidence
```

or:

```text
MEDIUM severity
+
CONFIRMED confidence
```

These are separate concepts.

---

## Verification Failure Is Not Confirmation

A failed generated test does not automatically prove a defect.

Examples that do **not** prove a product defect:

```text
SyntaxError
ImportError
ModuleNotFoundError
missing fixture
database unavailable
test collection failure
environment failure
```

PR Guardian attempts to distinguish product assertion failures from verification infrastructure failures.

---

## Zero Findings Is Valid

The system is not rewarded for maximizing comments.

A clean Pull Request may legitimately result in:

```text
0 publishable findings
```

---

## Raw Evidence Is Preserved

Intermediate reviewer outputs and verification evidence are retained for auditability.

---

# Security

Do not use PR Guardian to:

* scan systems without authorization;
* run destructive production database operations;
* expose credentials;
* commit GitHub tokens;
* perform active attacks against third-party systems;
* use confidential client repositories without permission.

Benchmark and demonstration data should be synthetic, public, or explicitly authorized.

---

# IBM Bob Hackathon Evidence

The repository includes:

```text
bob_sessions/
```

This directory should contain screenshots of real IBM Bob task sessions used during development and demonstration.

Suggested captures:

```text
01-pr-understanding.png
02-adaptive-routing.png
03-security-review.png
04-generated-regression-test.png
05-finding-verification.png
06-review-synthesis.png
```

These should represent actual Bob executions.

Do not fabricate task-session evidence.

---

# MVP Demo Flow

A concise demonstration can follow this sequence:

```text
1. Open synthetic vulnerable Pull Request

2. Run:
/pr-guardian-review owner/repository#42

3. Show repository-aware context

4. Show adaptive reviewer routing

5. Show specialist Bob subagents

6. Show security finding

7. Generate targeted regression test

8. Execute test

9. Show finding transition:
LIKELY
→ VERIFIED

10. Show duplicate findings consolidated

11. Show final review.md

12. Show metrics

13. Optionally perform GitHub publication dry-run
```

---

# Example Demo Story

```text
Pull Request looks small.

Only two files changed.

A traditional diff-only review sees a repository lookup change.

PR Guardian discovers that the affected resource is tenant-owned.

Security and test reviewers are activated.

The security reviewer identifies a possible authorization bypass.

The verifier generates a cross-tenant regression test.

The test expects 403 or 404.

The application returns 200.

The finding becomes VERIFIED.

Other agents reporting the same root cause are consolidated.

One evidence-backed finding reaches the final review.
```

---

# Current Status

PR Guardian is currently an MVP focused on demonstrating:

```text
repository-aware analysis
adaptive agent routing
specialized multi-agent review
deterministic verification
review noise reduction
structured review evidence
```

Future improvements may include:

* GitHub App authentication;
* asynchronous workers;
* persistent execution history;
* richer benchmark automation;
* organization-level configuration;
* policy profiles;
* additional language analyzers;
* richer dependency graphs;
* richer call graph analysis.

---

# Project Philosophy

PR Guardian is not designed to replace human code review.

It is designed to make AI-assisted review more useful by reducing unsupported noise and preserving engineering evidence.

The guiding principle is simple:

> **Don't just comment. Prove it.**