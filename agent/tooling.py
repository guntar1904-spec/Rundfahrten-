"""Kleiner @tool-Decorator: erzeugt aus Funktionssignatur + Docstring ein Tool-Schema für die Claude-API.

Docstring-Format: erste Absätze = Beschreibung, danach ein Abschnitt "Args:" mit "name: Beschreibung".
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Callable, get_type_hints

_JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


class Tool:
    def __init__(self, func: Callable[..., str]):
        self.func = func
        self.name = func.__name__
        doc = inspect.getdoc(func) or ""
        description, _, args_block = doc.partition("\nArgs:")
        self.description = description.strip()
        arg_docs = dict(re.findall(r"^\s*(\w+):\s*(.+)$", args_block, flags=re.M))

        hints = get_type_hints(func)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for pname, param in inspect.signature(func).parameters.items():
            prop: dict[str, Any] = {"type": _JSON_TYPES.get(hints.get(pname, str), "string")}
            if pname in arg_docs:
                prop["description"] = arg_docs[pname].strip()
            if param.default is inspect.Parameter.empty:
                required.append(pname)
            properties[pname] = prop
        self.input_schema = {"type": "object", "properties": properties, "required": required}

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}

    def call(self, arguments: dict[str, Any]) -> str:
        allowed = self.input_schema["properties"]
        unknown = set(arguments) - set(allowed)
        if unknown:
            raise ValueError(f"Unbekannte Parameter: {', '.join(sorted(unknown))}")
        missing = [p for p in self.input_schema["required"] if p not in arguments]
        if missing:
            raise ValueError(f"Fehlende Parameter: {', '.join(missing)}")
        return str(self.func(**arguments))


def tool(func: Callable[..., str]) -> Tool:
    return Tool(func)
