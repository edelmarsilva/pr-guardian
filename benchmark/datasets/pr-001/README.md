# PR-001 — Cross-Tenant Report Access

## Scenario

This benchmark simulates a multi-tenant Flask application where users belong to organizations.

Each report is owned by one organization.

The baseline implementation correctly scopes report retrieval by:

```text
report_id
+
organization_id
```

The Pull Request introduces a regression by changing the repository lookup to use only:

```text
report_id
```

This allows a user from one organization to retrieve a report belonging to another organization when the report ID is known.

---

# Expected Review Domains

The adaptive router should normally select:

```text
code-review
security-review
test-impact
database-review
api-review
```

The following reviewer is not required:

```text
queue-review
```

Architecture review may or may not be selected depending on routing heuristics.

---

# Expected Finding

Primary finding:

```text
Category:
TENANT_ISOLATION

Severity:
HIGH

Expected root cause:
Report lookup is not scoped by organization_id.
```

---

# Expected Impact

A user authenticated under Organization A may retrieve a report belonging to Organization B.

This represents a cross-tenant authorization failure.

---

# Expected Verification

The finding should be verifiable using a regression test.

Synthetic setup:

```text
Organization A
 └── User A

Organization B
 └── Report B
```

Request:

```text
User A
GET /reports/<Report B ID>
```

Expected secure behavior:

```text
403
or
404
```

Vulnerable PR behavior:

```text
200
```

---

# Verification Principle

The generated verification test should assert the secure behavior.

Example:

```python
assert response.status_code in {403, 404}
```

When executed against the vulnerable PR, this test should fail.

The failed regression test provides reproducible evidence that the finding is valid.

---

# Benchmark Goals

This dataset demonstrates:

```text
CONTEXTUAL
repository and tenant relationships are understood

ADAPTIVE
only relevant reviewers are selected

MULTI-AGENT
security, database and test reviewers analyze the change

EVIDENCE-BASED
a regression test reproduces the defect
```

---

# Ground Truth

This benchmark intentionally contains one primary defect:

```text
SEC-TENANT-001
```

Unexpected findings must be manually inspected before being classified as false positives.