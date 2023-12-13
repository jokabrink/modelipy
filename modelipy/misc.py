# Copyright (c) 2023, Jonas Kock am Brink

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional, Union

Primitive = Union[str, int, float]
Description = str


class AssignFlags(enum.Flag):
    Each = enum.auto()
    Final = enum.auto()
    Redeclare = enum.auto()
    Replaceable = enum.auto()


class Text(list[str]):
    def __init__(
        self,
        lines: list[str],
        indent: bool = False,
    ):
        self.indent = indent
        return super().__init__(lines)


class Assign:
    each = AssignFlags.Each
    final = AssignFlags.Final
    redeclare = AssignFlags.Redeclare
    replaceable = AssignFlags.Replaceable

    def __init__(
        self,
        value: Optional[Primitive] = None,
        init: Optional[dict[str, Any]] = None,
        fmt: str = "",
        flags: Optional[AssignFlags] = None,
        description: Optional[str] = None,
        annotation: Optional[dict[str, Any]] = None,
        type: Optional[str] = None,
    ):
        if type is not None:
            assert flags is not None
            assert AssignFlags.Redeclare in flags, "component type must be known when redeclaring"
        self.value = value
        self.init = {} if init is None else init
        self.fmt = fmt
        self.flags = flags
        self.description = description
        self.annotation = {} if annotation is None else annotation
        self.type = type

    def __format__(self, fmt: str) -> str:
        if fmt:
            return format(self.value, fmt)
        return format(self.value, self.fmt)

    def __str__(self) -> str:
        return format(self.value, self.fmt)


@dataclass
class Equation:
    left: str
    right: str
    description: Optional[str] = None
    annotation: dict[str, Any] = field(default_factory=dict)


@dataclass
class Algorithm:
    left: str
    right: str
    description: Optional[str]
    annotation: Optional[dict[str, Any]]


@dataclass
class Statement:
    value: str


@dataclass
class Expression:
    value: str


@dataclass
class Extends:
    name: str


class Constraint:
    pass


@dataclass
class Connect:
    """
    Connect is now just two names. The resolution to the actual ident and port is deferred
    """

    ref1: str
    ref2: str
    description: Optional[str] = None
    annotation: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForIndex:
    ident: Ident
    expr: Expression


class Ident(str):
    def In(self, expr: Expression) -> ForIndex:
        return ForIndex(self, expr)


class Import:
    pass


@dataclass
class QualifiedImport(Import):
    name: str


@dataclass
class StarImport(Import):
    path: str


@dataclass
class MultiImport(Import):
    path: str
    names: list[str]


@dataclass
class NamedImport(Import):
    short: str
    long: str


@dataclass
class Within:
    """Marks a `within` statement."""

    # TODO: use name: Optional[Name] = None to provide a sane within

    name: Optional[str] = None

    @classmethod
    def from_str(cls, s: str) -> "Within":
        """
        >>> Within.from_str("Name.Space")
        Within(name='Name.Space')

        Within(name=Name('Name', 'Space'))

        >>> Within.from_str("")
        Within(name=None)
        """
        if s == "":
            return cls()
        else:
            return cls(s)
