# PR-002 — SQL Injection in User Lookup

## Scenario

This benchmark simulates a Flask application that retrieves users from a relational database.

The baseline implementation uses parameterized SQL.

The Pull Request introduces a regression by interpolating user-controlled input directly into a SQL query.

Unsafe behavior:

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

The `email` value originates from an HTTP request.

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

---

# Expected Finding

Primary finding:

```text
Category:
SQL_INJECTION

Severity:
HIGH

Expected root cause:
Untrusted request input is concatenated into a SQL statement.
```

---

# Expected Impact

An attacker may alter the intended SQL query by submitting crafted input.

Depending on the database driver and permissions, this can result in:

```text
unauthorized reads
authentication bypass
data modification
data disclosure
```

---

# Expected Verification

This finding should support more than one evidence source.

Preferred evidence:

```text
direct source-to-sink inspection
+
Semgrep
or
Bandit
```

A targeted regression test may also be generated when the database test environment allows it.

---

# Benchmark Goals

This dataset demonstrates:

```text
CONTEXTUAL
request input is traced to database execution

ADAPTIVE
security and database reviewers are selected

MULTI-AGENT
code, security, test, API and database perspectives cooperate

EVIDENCE-BASED
independent static analysis can support the finding
```

---

# Ground Truth

This benchmark intentionally contains one primary defect:

```text
SEC-SQL-001
```

Unexpected findings must be manually inspected before being classified as false positives.