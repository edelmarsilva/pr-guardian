from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from models import PullRequest


class ReviewDomain(str, Enum):
    CODE = "code-review"
    SECURITY = "security-review"
    TEST = "test-impact"
    ARCHITECTURE = "architecture-review"
    DATABASE = "database-review"
    API = "api-review"
    QUEUE = "queue-review"

@dataclass(slots=True)
class ReviewerDecision:
    reviewer: ReviewDomain
    selected: bool

    reasons: list[str] = field(
        default_factory=list
    )

    matched_files: list[str] = field(
        default_factory=list
    )

    matched_signals: list[str] = field(
        default_factory=list
    )

@dataclass(slots=True)
class RoutingResult:
    selected_reviewers: list[ReviewDomain]
    decisions: list[ReviewerDecision]

    @property
    def selected_count(self) -> int:
        return len(
            self.selected_reviewers
        )

    def is_selected(
        self,
        reviewer: ReviewDomain,
    ) -> bool:
        return reviewer in self.selected_reviewers

    def reasons_for(
        self,
        reviewer: ReviewDomain,
    ) -> list[str]:
        for decision in self.decisions:
            if decision.reviewer == reviewer:
                return decision.reasons

        return []

class ReviewerRouter:
    """
    Adaptive reviewer selector.

    Routing is based on observable PR signals such as changed files,
    extensions, paths, and keywords.

    This component does not perform defect analysis.
    """

    DATABASE_FILENAMES = {
        "models.py",
        "model.py",
        "database.py",
        "db.py",
        "schema.sql",
    }

    DATABASE_PATH_PARTS = {
        "migration",
        "migrations",
        "models",
        "repositories",
        "repository",
        "database",
        "db",
        "sql",
        "alembic",
        "versions",
    }

    API_PATH_PARTS = {
        "api",
        "routes",
        "controllers",
        "views",
        "endpoints",
        "schemas",
        "serializers",
    }

    API_FILENAMES = {
        "openapi.yaml",
        "openapi.yml",
        "openapi.json",
        "swagger.yaml",
        "swagger.yml",
        "swagger.json",
    }

    SECURITY_PATH_PARTS = {
        "auth",
        "authentication",
        "authorization",
        "security",
        "permissions",
        "rbac",
        "oauth",
        "jwt",
        "tokens",
        "credentials",
        "admin",
    }

    QUEUE_PATH_PARTS = {
        "queue",
        "queues",
        "worker",
        "workers",
        "jobs",
        "tasks",
        "celery",
        "rq",
        "kafka",
        "rabbitmq",
        "consumers",
        "producers",
    }

    TEST_PATH_PARTS = {
        "test",
        "tests",
        "testing",
    }

    CONFIG_FILENAMES = {
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "setup.py",
        "setup.cfg",
        "tox.ini",
        "docker-compose.yml",
        "docker-compose.yaml",
        "Dockerfile",
    }

    SECURITY_SIGNALS = {
        "authorization",
        "authenticate",
        "authentication",
        "permission",
        "permissions",
        "jwt",
        "oauth",
        "api_key",
        "apikey",
        "password",
        "secret",
        "token",
        "tenant",
        "organization_id",
        "user_id",
        "role",
        "current_user",
        "sensitive_data",
    }

    QUEUE_SIGNALS = {
        "enqueue",
        "delay(",
        "apply_async",
        "retry",
        "worker",
        "queue",
        "celery",
        "rq.",
        "kafka",
        "rabbitmq",
        "publish(",
        "consume(",
    }

    DATABASE_SIGNALS = {
        "session.commit",
        "session.rollback",
        "transaction",
        "select(",
        "insert(",
        "update(",
        "delete(",
        "execute(",
        "foreignkey",
        "nullable=",
        "unique=",
    }

    API_SIGNALS = {
        "@app.route",
        "@bp.route",
        "@router.",
        "request.json",
        "jsonify(",
        "status_code",
        "response_model",
        "openapi",
        "swagger",
    }

    ARCHITECTURE_SIGNALS = {
        "service",
        "repository",
        "adapter",
        "factory",
        "interface",
        "protocol",
        "dependency",
    }

    def route(
        self,
        pull_request: PullRequest,
    ) -> RoutingResult:
        files = [
            changed_file.filename
            for changed_file
            in pull_request.changed_files
        ]

        normalized_files = [
            filename.lower()
            for filename in files
        ]

        patch_text = self._collect_patch_text(
            pull_request
        )

        decisions = [
            self._select_code_review(
                normalized_files
            ),
            self._select_security_review(
                normalized_files,
                patch_text,
            ),
            self._select_test_review(
                normalized_files
            ),
            self._select_architecture_review(
                normalized_files,
                patch_text,
            ),
            self._select_database_review(
                normalized_files,
                patch_text,
            ),
            self._select_api_review(
                normalized_files,
                patch_text,
            ),
            self._select_queue_review(
                normalized_files,
                patch_text,
            ),
        ]

        selected = [
            decision.reviewer
            for decision in decisions
            if decision.selected
        ]

        return RoutingResult(
            selected_reviewers=selected,
            decisions=decisions,
        )

    def _select_code_review(
        self,
        files: list[str],
    ) -> ReviewerDecision:
        source_files = [
            filename
            for filename in files
            if self._is_source_file(
                filename
            )
            and not self._is_test_file(
                filename
            )
        ]

        return ReviewerDecision(
            reviewer=ReviewDomain.CODE,
            selected=bool(
                source_files
            ),
            reasons=(
                [
                    "Application source code changed."
                ]
                if source_files
                else []
            ),
            matched_files=source_files,
        )

    def _select_security_review(
        self,
        files: list[str],
        patch_text: str,
    ) -> ReviewerDecision:
        path_matches = self._files_matching_parts(
            files,
            self.SECURITY_PATH_PARTS,
        )

        signal_matches = self._find_signals(
            patch_text,
            self.SECURITY_SIGNALS,
        )

        selected = bool(
            path_matches
            or signal_matches
        )

        reasons: list[str] = []

        if path_matches:
            reasons.append(
                "Security-sensitive files changed."
            )

        if signal_matches:
            reasons.append(
                "Security-sensitive code signals detected."
            )

        return ReviewerDecision(
            reviewer=ReviewDomain.SECURITY,
            selected=selected,
            reasons=reasons,
            matched_files=path_matches,
            matched_signals=signal_matches,
        )

    def _select_test_review(
        self,
        files: list[str],
    ) -> ReviewerDecision:
        production_files = [
            filename
            for filename in files
            if self._is_source_file(
                filename
            )
            and not self._is_test_file(
                filename
            )
        ]

        test_files = [
            filename
            for filename in files
            if self._is_test_file(
                filename
            )
        ]

        selected = bool(
            production_files
        )

        reasons: list[str] = []

        if production_files:
            reasons.append(
                "Production behavior changed and test impact should be evaluated."
            )

        if production_files and not test_files:
            reasons.append(
                "Production code changed without test files in the PR."
            )

        return ReviewerDecision(
            reviewer=ReviewDomain.TEST,
            selected=selected,
            reasons=reasons,
            matched_files=(
                production_files
                + test_files
            ),
        )

    def _select_architecture_review(
        self,
        files: list[str],
        patch_text: str,
    ) -> ReviewerDecision:
        source_files = [
            filename
            for filename in files
            if self._is_source_file(
                filename
            )
        ]

        signal_matches = self._find_signals(
            patch_text,
            self.ARCHITECTURE_SIGNALS,
        )

        large_change = (
            len(source_files) >= 5
        )

        selected = bool(
            large_change
            or (
                len(source_files) >= 2
                and signal_matches
            )
        )

        reasons: list[str] = []

        if large_change:
            reasons.append(
                "PR changes several source files and may affect architectural boundaries."
            )

        if signal_matches:
            reasons.append(
                "Architecture-related abstractions detected in the changed code."
            )

        return ReviewerDecision(
            reviewer=ReviewDomain.ARCHITECTURE,
            selected=selected,
            reasons=reasons,
            matched_files=source_files,
            matched_signals=signal_matches,
        )

    def _select_database_review(
        self,
        files: list[str],
        patch_text: str,
    ) -> ReviewerDecision:
        path_matches = self._files_matching_parts(
            files,
            self.DATABASE_PATH_PARTS,
        )

        filename_matches = [
            filename
            for filename in files
            if Path(filename).name
            in self.DATABASE_FILENAMES
        ]

        sql_files = [
            filename
            for filename in files
            if Path(filename).suffix
            in {
                ".sql",
            }
        ]

        signal_matches = self._find_signals(
            patch_text,
            self.DATABASE_SIGNALS,
        )

        matched_files = sorted(
            set(
                path_matches
                + filename_matches
                + sql_files
            )
        )

        selected = bool(
            matched_files
            or signal_matches
        )

        reasons: list[str] = []

        if matched_files:
            reasons.append(
                "Persistence, schema, or database-related files changed."
            )

        if signal_matches:
            reasons.append(
                "Database interaction signals detected in the patch."
            )

        return ReviewerDecision(
            reviewer=ReviewDomain.DATABASE,
            selected=selected,
            reasons=reasons,
            matched_files=matched_files,
            matched_signals=signal_matches,
        )

    def _select_api_review(
        self,
        files: list[str],
        patch_text: str,
    ) -> ReviewerDecision:
        path_matches = self._files_matching_parts(
            files,
            self.API_PATH_PARTS,
        )

        specification_files = [
            filename
            for filename in files
            if Path(filename).name
            in self.API_FILENAMES
        ]

        signal_matches = self._find_signals(
            patch_text,
            self.API_SIGNALS,
        )

        matched_files = sorted(
            set(
                path_matches
                + specification_files
            )
        )

        selected = bool(
            matched_files
            or signal_matches
        )

        reasons: list[str] = []

        if matched_files:
            reasons.append(
                "API route, schema, or specification files changed."
            )

        if signal_matches:
            reasons.append(
                "HTTP/API behavior signals detected in the patch."
            )

        return ReviewerDecision(
            reviewer=ReviewDomain.API,
            selected=selected,
            reasons=reasons,
            matched_files=matched_files,
            matched_signals=signal_matches,
        )

    def _select_queue_review(
        self,
        files: list[str],
        patch_text: str,
    ) -> ReviewerDecision:
        path_matches = self._files_matching_parts(
            files,
            self.QUEUE_PATH_PARTS,
        )

        signal_matches = self._find_signals(
            patch_text,
            self.QUEUE_SIGNALS,
        )

        selected = bool(
            path_matches
            or signal_matches
        )

        reasons: list[str] = []

        if path_matches:
            reasons.append(
                "Queue, worker, or background-job files changed."
            )

        if signal_matches:
            reasons.append(
                "Asynchronous processing signals detected in the patch."
            )

        return ReviewerDecision(
            reviewer=ReviewDomain.QUEUE,
            selected=selected,
            reasons=reasons,
            matched_files=path_matches,
            matched_signals=signal_matches,
        )

    @staticmethod
    def _collect_patch_text(
        pull_request: PullRequest,
    ) -> str:
        return "\n".join(
            changed_file.patch or ""
            for changed_file
            in pull_request.changed_files
        ).lower()

    @staticmethod
    def _files_matching_parts(
        files: Iterable[str],
        parts: set[str],
    ) -> list[str]:
        matches: list[str] = []

        for filename in files:
            path_parts = {
                part.lower()
                for part
                in Path(filename).parts
            }

            if path_parts & parts:
                matches.append(
                    filename
                )

        return matches

    @staticmethod
    def _find_signals(
        text: str,
        signals: set[str],
    ) -> list[str]:
        return sorted(
            signal
            for signal in signals
            if signal in text
        )

    @classmethod
    def _is_test_file(
        cls,
        filename: str,
    ) -> bool:
        path = Path(filename)

        parts = {
            part.lower()
            for part in path.parts
        }

        name = path.name.lower()

        return (
            bool(
                parts
                & cls.TEST_PATH_PARTS
            )
            or name.startswith(
                "test_"
            )
            or name.endswith(
                "_test.py"
            )
        )

    @staticmethod
    def _is_source_file(
        filename: str,
    ) -> bool:
        return (
            Path(filename)
            .suffix
            .lower()
            in {
                ".py",
                ".js",
                ".ts",
                ".tsx",
                ".jsx",
                ".java",
                ".go",
                ".rs",
                ".cs",
                ".php",
                ".sql",
            }
        )
