from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from .files import list_repository_files, read_text_file

@dataclass(slots=True)
class ImportReference:
    source_file: str
    imported_module: str
    imported_names: list[str] = field(default_factory=list)

@dataclass(slots=True)
class DependencyGraph:
    imports: list[ImportReference] = field(default_factory=list)

    def dependents_of(
        self,
        module_name: str,
    ) -> list[ImportReference]:
        return [
            item
            for item in self.imports
            if item.imported_module == module_name
            or item.imported_module.startswith(f"{module_name}.")
        ]

def _module_name_from_path(
    relative_path: str,
    ) -> str:
    path = Path(relative_path)

    parts = list(path.with_suffix("").parts)

    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)

def extract_python_imports(
    source_file: str,
    content: str,
) -> list[ImportReference]:
    import textwrap
    try:
        tree = ast.parse(content)
    except SyntaxError:
        try:
            tree = ast.parse(textwrap.dedent(content))
        except SyntaxError:
            return []

    imports: list[ImportReference] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportReference(
                        source_file=source_file,
                        imported_module=alias.name,
                        imported_names=[],
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            imports.append(
                ImportReference(
                    source_file=source_file,
                    imported_module=module,
                    imported_names=[
                        alias.name
                        for alias in node.names
                    ],
                )
            )

    return imports

def build_python_dependency_graph(
    repository_path: Path,
    ) -> DependencyGraph:
    graph = DependencyGraph()

    python_files = [
        path
        for path in list_repository_files(repository_path)
        if path.endswith(".py")
    ]

    for relative_path in python_files:
        repository_file = read_text_file(
            repository_path,
            relative_path,
        )

        if repository_file.content is None:
            continue

        graph.imports.extend(
            extract_python_imports(
                relative_path,
                repository_file.content,
            )
        )

    return graph

def find_files_depending_on(
    repository_path: Path,
    target_file: str,
    ) -> list[str]:
    graph = build_python_dependency_graph(
    repository_path,
    )

    target_module = _module_name_from_path(
        target_file,
    )

    dependents = graph.dependents_of(
        target_module,
    )

    return sorted(
        {
            item.source_file
            for item in dependents
        }
    )
