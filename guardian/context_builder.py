from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from models import PullRequest
from repository import (
    build_python_call_graph,
    build_python_dependency_graph,
    find_files_depending_on,
    get_file_history,
    list_repository_files,
)


@dataclass(slots=True)
class ChangedSymbolContext:
    name: str
    filename: str

    direct_callers: list[str] = field(
        default_factory=list
    )

    calls: list[str] = field(
        default_factory=list
    )

@dataclass(slots=True)
class ChangedFileContext:
    filename: str
    status: str

    additions: int
    deletions: int

    extension: str

    direct_dependents: list[str] = field(
        default_factory=list
    )

    recent_history: list[dict[str, Any]] = field(
        default_factory=list
    )

    changed_symbols: list[ChangedSymbolContext] = field(
        default_factory=list
    )

@dataclass(slots=True)
class RepositoryContext:
    repository_files: int

    python_files: int = 0
    test_files: int = 0

    configuration_files: list[str] = field(
        default_factory=list
    )

    dependency_files: list[str] = field(
        default_factory=list
    )

    api_specs: list[str] = field(
        default_factory=list
    )

    migrations: list[str] = field(
        default_factory=list
    )

@dataclass(slots=True)
class PullRequestContext:
    pr_id: str

    title: str
    description: str | None

    base_sha: str
    head_sha: str

    files_changed: int

    changed_files: list[ChangedFileContext]

    repository: RepositoryContext

    potentially_affected_files: list[str]

    risk_signals: list[str]

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "pr_id": self.pr_id,
            "title": self.title,
            "description": self.description,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "files_changed": self.files_changed,
            "changed_files": [
                {
                    "file": item.filename,
                    "status": item.status,
                    "additions": item.additions,
                    "deletions": item.deletions,
                    "extension": item.extension,
                    "direct_dependents": item.direct_dependents,
                    "recent_history": item.recent_history,
                    "symbols": [
                        {
                            "name": symbol.name,
                            "file": symbol.filename,
                            "direct_callers": symbol.direct_callers,
                            "calls": symbol.calls,
                        }
                        for symbol in item.changed_symbols
                    ],
                }
                for item in self.changed_files
            ],
            "repository": {
                "repository_files": (
                    self.repository.repository_files
                ),
                "python_files": (
                    self.repository.python_files
                ),
                "test_files": (
                    self.repository.test_files
                ),
                "configuration_files": (
                    self.repository.configuration_files
                ),
                "dependency_files": (
                    self.repository.dependency_files
                ),
                "api_specs": (
                    self.repository.api_specs
                ),
                "migrations": (
                    self.repository.migrations
                ),
            },
            "potentially_affected_files": (
                self.potentially_affected_files
            ),
            "risk_signals": self.risk_signals,
            "metadata": self.metadata,
        }

class ContextBuilder:
    """
    Build repository-aware context for Pull Request analysis.

    The context extends beyond the diff by including:
    - repository structure
    - import dependencies
    - call relationships
    - recent file history
    """

    CONFIGURATION_NAMES = {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "tox.ini",
        ".env.example",
        "docker-compose.yml",
        "docker-compose.yaml",
        "Dockerfile",
    }

    DEPENDENCY_NAMES = {
        "requirements.txt",
        "requirements-dev.txt",
        "poetry.lock",
        "Pipfile",
        "Pipfile.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
    }

    API_SPEC_NAMES = {
        "openapi.yaml",
        "openapi.yml",
        "openapi.json",
        "swagger.yaml",
        "swagger.yml",
        "swagger.json",
    }

    RISK_SIGNALS = {
        "authorization": "AUTHORIZATION",
        "permission": "AUTHORIZATION",
        "tenant": "TENANT_ISOLATION",
        "organization_id": "TENANT_ISOLATION",
        "password": "AUTHENTICATION",
        "token": "TOKEN_SECURITY",
        "jwt": "TOKEN_SECURITY",
        "api_key": "API_KEY",
        "secret": "SECRET_HANDLING",
        "execute(": "DATABASE",
        "session.commit": "DATABASE_TRANSACTION",
        "migration": "MIGRATION",
        "enqueue": "QUEUE",
        "retry": "RETRY",
        "apply_async": "QUEUE",
        "publish(": "MESSAGING",
        "@app.route": "API",
        "@bp.route": "API",
        "@router.": "API",
        "openapi": "API_CONTRACT",
        "select ": "DATABASE",
        "select *": "DATABASE",
        "insert into": "DATABASE",
        "update ": "DATABASE",
        "delete from": "DATABASE",
        "from users": "DATABASE",
        "from reports": "DATABASE",
    }

    def build(
        self,
        pull_request: PullRequest,
        repository_path: Path,
        *,
        history_limit: int = 5,
    ) -> PullRequestContext:
        repository_files = list_repository_files(
            repository_path
        )

        repository_context = (
            self._build_repository_context(
                repository_files
            )
        )

        dependency_graph = (
            build_python_dependency_graph(
                repository_path
            )
        )

        call_graph = (
            build_python_call_graph(
                repository_path
            )
        )

        changed_file_contexts: list[
            ChangedFileContext
        ] = []

        affected_files: set[str] = set()

        for changed_file in pull_request.changed_files:
            relative_path = changed_file.filename

            direct_dependents: list[str] = []

            if relative_path.endswith(".py"):
                direct_dependents = (
                    find_files_depending_on(
                        repository_path,
                        relative_path,
                    )
                )

                affected_files.update(
                    direct_dependents
                )

            history = self._safe_history(
                repository_path,
                relative_path,
                limit=history_limit,
            )

            symbols = self._symbols_for_file(
                relative_path,
                call_graph,
            )

            changed_file_contexts.append(
                ChangedFileContext(
                    filename=relative_path,
                    status=changed_file.status,
                    additions=changed_file.additions,
                    deletions=changed_file.deletions,
                    extension=Path(
                        relative_path
                    ).suffix.lower(),
                    direct_dependents=(
                        direct_dependents
                    ),
                    recent_history=history,
                    changed_symbols=symbols,
                )
            )

        changed_names = {
            changed_file.filename
            for changed_file
            in pull_request.changed_files
        }

        affected_files.difference_update(
            changed_names
        )

        risk_signals = self._detect_risk_signals(
            pull_request
        )

        return PullRequestContext(
            pr_id=pull_request.identifier,
            title=pull_request.title,
            description=pull_request.description,
            base_sha=pull_request.base_sha,
            head_sha=pull_request.head_sha,
            files_changed=len(
                pull_request.changed_files
            ),
            changed_files=changed_file_contexts,
            repository=repository_context,
            potentially_affected_files=sorted(
                affected_files
            ),
            risk_signals=risk_signals,
            metadata={
                "dependency_edges": len(
                    dependency_graph.imports
                ),
                "call_definitions": len(
                    call_graph.definitions
                ),
                "call_edges": len(
                    call_graph.calls
                ),
            },
        )

    def _build_repository_context(
        self,
        files: list[str],
    ) -> RepositoryContext:
        configuration_files: list[str] = []
        dependency_files: list[str] = []
        api_specs: list[str] = []
        migrations: list[str] = []

        python_files = 0
        test_files = 0

        for filename in files:
            path = Path(filename)

            if path.suffix.lower() == ".py":
                python_files += 1

            if self._is_test_file(
                filename
            ):
                test_files += 1

            if (
                path.name
                in self.CONFIGURATION_NAMES
            ):
                configuration_files.append(
                    filename
                )

            if (
                path.name
                in self.DEPENDENCY_NAMES
            ):
                dependency_files.append(
                    filename
                )

            if (
                path.name
                in self.API_SPEC_NAMES
            ):
                api_specs.append(
                    filename
                )

            if self._is_migration_file(
                filename
            ):
                migrations.append(
                    filename
                )

        return RepositoryContext(
            repository_files=len(files),
            python_files=python_files,
            test_files=test_files,
            configuration_files=sorted(
                configuration_files
            ),
            dependency_files=sorted(
                dependency_files
            ),
            api_specs=sorted(
                api_specs
            ),
            migrations=sorted(
                migrations
            ),
        )

    def _symbols_for_file(
        self,
        relative_path: str,
        call_graph,
    ) -> list[ChangedSymbolContext]:
        definitions = [
            definition
            for definition
            in call_graph.definitions
            if definition.file == relative_path
        ]

        results: list[
            ChangedSymbolContext
        ] = []

        for definition in definitions:
            symbol_name = (
                f"{definition.class_name}."
                f"{definition.name}"
                if definition.class_name
                else definition.name
            )

            callers = sorted(
                {
                    call.caller
                    for call
                    in call_graph.calls
                    if call.callee
                    == definition.name
                }
            )

            calls = sorted(
                {
                    call.callee
                    for call
                    in call_graph.calls
                    if call.caller
                    == symbol_name
                }
            )

            results.append(
                ChangedSymbolContext(
                    name=symbol_name,
                    filename=relative_path,
                    direct_callers=callers,
                    calls=calls,
                )
            )

        return results

    @staticmethod
    def _safe_history(
        repository_path: Path,
        relative_path: str,
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        try:
            commits = get_file_history(
                repository_path,
                relative_path,
                limit=limit,
            )
        except Exception:
            return []

        return [
            {
                "sha": commit.sha,
                "date": commit.date,
                "subject": commit.subject,
            }
            for commit in commits
        ]

    def _detect_risk_signals(
        self,
        pull_request: PullRequest,
    ) -> list[str]:
        patch = "\n".join(
            changed_file.patch or ""
            for changed_file
            in pull_request.changed_files
        ).lower()

        signals = {
            label
            for token, label
            in self.RISK_SIGNALS.items()
            if token in patch
        }

        for changed_file in (
            pull_request.changed_files
        ):
            path = (
                changed_file.filename.lower()
            )

            if "migration" in path:
                signals.add(
                    "MIGRATION"
                )

            if any(
                item in path
                for item in (
                    "repositor",
                    "database",
                    "/db/",
                    "/models/",
                    "/migrations/",
                )
            ):
                signals.add(
                    "DATABASE"
                )

            if any(
                item in path
                for item in (
                    "/auth/",
                    "authentication",
                    "authorization",
                    "permissions",
                )
            ):
                signals.add(
                    "AUTHORIZATION"
                )

            if any(
                item in path
                for item in (
                    "/queue/",
                    "/jobs/",
                    "/tasks/",
                    "/workers/",
                )
            ):
                signals.add(
                    "QUEUE"
                )

        return sorted(
            signals
        )

    @staticmethod
    def _is_test_file(
        filename: str,
    ) -> bool:
        path = Path(filename)

        parts = {
            part.lower()
            for part in path.parts
        }

        name = path.name.lower()

        return (
            "tests" in parts
            or "test" in parts
            or name.startswith(
                "test_"
            )
            or name.endswith(
                "_test.py"
            )
        )

    @staticmethod
    def _is_migration_file(
        filename: str,
    ) -> bool:
        parts = {
            part.lower()
            for part
            in Path(filename).parts
        }

        return bool(
            {
                "migration",
                "migrations",
                "alembic",
                "versions",
            }
            & parts
        )
