from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from .files import list_repository_files, read_text_file


@dataclass(slots=True)
class FunctionDefinition:
    name: str
    file: str
    line: int
    class_name: str | None = None


@dataclass(slots=True)
class FunctionCall:
    caller: str
    callee: str
    file: str
    line: int


@dataclass(slots=True)
class CallGraph:
    definitions: list[FunctionDefinition] = field(default_factory=list)
    calls: list[FunctionCall] = field(default_factory=list)

    def callers_of(
        self,
        function_name: str,
    ) -> list[FunctionCall]:
        return [
            call
            for call in self.calls
            if call.callee == function_name
        ]

    def calls_from(
        self,
        function_name: str,
    ) -> list[FunctionCall]:
        return [
            call
            for call in self.calls
            if call.caller == function_name
        ]


class PythonCallGraphVisitor(ast.NodeVisitor):
    def __init__(
        self,
        file_path: str,
    ) -> None:
        self.file_path = file_path

        self.current_function: str | None = None
        self.current_class: str | None = None

        self.definitions: list[FunctionDefinition] = []
        self.calls: list[FunctionCall] = []

    def visit_ClassDef(
        self,
        node: ast.ClassDef,
    ) -> None:
        previous_class = self.current_class
        self.current_class = node.name

        self.generic_visit(node)

        self.current_class = previous_class

    def visit_FunctionDef(
        self,
        node: ast.FunctionDef,
    ) -> None:
        previous_function = self.current_function

        qualified_name = (
            f"{self.current_class}.{node.name}"
            if self.current_class
            else node.name
        )

        self.current_function = qualified_name

        self.definitions.append(
            FunctionDefinition(
                name=node.name,
                file=self.file_path,
                line=node.lineno,
                class_name=self.current_class,
            )
        )

        self.generic_visit(node)

        self.current_function = previous_function

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self.visit_FunctionDef(node)

    def visit_Call(
        self,
        node: ast.Call,
    ) -> None:
        if self.current_function is None:
            self.generic_visit(node)
            return

        callee = self._extract_callee_name(
            node.func,
        )

        if callee is not None:
            self.calls.append(
                FunctionCall(
                    caller=self.current_function,
                    callee=callee,
                    file=self.file_path,
                    line=node.lineno,
                )
            )

        self.generic_visit(node)

    @staticmethod
    def _extract_callee_name(
        node: ast.AST,
    ) -> str | None:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            return node.attr

        return None


def analyze_python_file(
    relative_path: str,
    content: str,
) -> tuple[
    list[FunctionDefinition],
    list[FunctionCall],
]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [], []

    visitor = PythonCallGraphVisitor(
        relative_path,
    )

    visitor.visit(tree)

    return (
        visitor.definitions,
        visitor.calls,
    )


def build_python_call_graph(
    repository_path: Path,
) -> CallGraph:
    graph = CallGraph()

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

        definitions, calls = analyze_python_file(
            relative_path,
            repository_file.content,
        )

        graph.definitions.extend(
            definitions
        )

        graph.calls.extend(
            calls
        )

    return graph
