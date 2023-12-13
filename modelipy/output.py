# Copyright (c) 2023, Jonas Kock am Brink

from __future__ import annotations

import sys
from abc import ABC
from io import StringIO
from numbers import Real
from pathlib import Path
from typing import Any, Optional, TextIO

from .component import Component, ComponentFlags
from .condition import IfEquation
from .misc import (
    Algorithm,
    Assign,
    AssignFlags,
    Connect,
    Description,
    Equation,
    Expression,
    Extends,
    MultiImport,
    NamedImport,
    QualifiedImport,
    Text,
    Within,
)
from .model import Model, ModelFlags


class Visitor(ABC):
    """Abstract visitor class. Subclass from this class and implement visiting
    functions as `visit_`+classname."""

    def visit_default(self, node: Any) -> Any:
        raise ValueError(f"no visit function for type {type(node)}")

    def visit(self, node: Any) -> Any:
        node_type = type(node)
        func = getattr(self, f"visit_{node_type.__name__}", None)
        if func is None:
            return self.visit_default(node)
        return func(node)


class PrettyPrinter(Visitor):
    def __init__(
        self,
        stream: TextIO,
        indentation: str = "  ",
        width: int = 80,
        start_indent: int = 0,
        draw_connections: bool = True,
    ):
        self.stream = stream
        self.indentation = indentation
        self.width = width
        self.charcount = 0
        self.curpos = 0
        self.indent = start_indent
        if draw_connections is True:
            print("WARNING: Does not support drawing connections yet")

    def _write(
        self,
        s: str = "",
        *,
        indent: bool = False,
    ) -> int:
        """Write contents of s with indentation to stream and return characters written."""
        # TODO: Find out if charcount is number of columns or number of bytes written! (UTF-8)
        if indent:
            nchars = self.stream.write(self.indent * self.indentation + s)
        else:
            nchars = self.stream.write(s)
        self.charcount += nchars
        return nchars

    def print(
        self,
        s: str = "",
        *,
        indent: bool = False,
    ) -> None:
        """Print a line and reset cursor column position to zero position."""
        self._write(s=s + "\n", indent=indent)
        self.curpos = 0

    def write(
        self,
        s: str = "",
        *,
        indent: bool = False,
    ) -> None:
        """Write contents of s to stream and move cursor column position."""
        nchars = self._write(s=s, indent=indent)
        self.curpos += nchars

    def write_key_value(self, key: str, value: Any) -> None:
        """Write out the key value pairs of a modification. Admittedly, this is a complicated
        function. Maybe refactor?"""
        if value is None:
            self.write(key)
        elif isinstance(value, dict):
            lst = list(value.items())
            self.write(key, indent=False)
            if len(lst) == 0:
                # self.write("()")
                pass
            elif len(lst) == 1:
                self.write("(")
                self.write_key_value(*lst[0])
                self.write(")", indent=False)
            elif len(lst) == 2:
                self.write("(")
                self.write_key_value(*lst[0])
                self.write(", ")
                self.write_key_value(*lst[1])
                self.write(")", indent=False)
            else:
                self.indent += 1
                first, *rest, last = lst
                # indent and print first modification on new line
                self.write("(\n")
                self.write("", indent=True)

                self.write_key_value(*first)
                self.print(",", indent=False)
                for k, v in rest:
                    self.write(indent=True)
                    self.write_key_value(k, v)
                    self.print(",", indent=False)

                self.write(indent=True)
                self.write_key_value(*last)

                self.indent -= 1
                if False:
                    self.print(indent=False)
                    self.write(")", indent=True)
                else:
                    self.write(")", indent=False)
        elif isinstance(value, Assign):
            if value.flags is not None:
                flags: list[str] = []
                if AssignFlags.Redeclare in value.flags:
                    flags.append("redeclare")
                if AssignFlags.Each in value.flags:
                    flags.append("each")
                if AssignFlags.Final in value.flags:
                    flags.append("final")
                if AssignFlags.Replaceable in value.flags:
                    flags.append("replaceable")
                self.write(" ".join(flags) + " ")

            if value.type:
                self.write(value.type + " ")

            # value.init is always a dict, if it were an optional[dict], 3 different options
            # could be implemented "a=1", "a", or "a()"
            if value.init:
                self.write_key_value(key, value.init)
            else:
                self.write(f"{key}", indent=False)
            if value.value is not None:
                if value.init:
                    self.write(f" = {value}", indent=False)
                else:
                    self.write(f"={value}", indent=False)
            if value.description is not None:
                self.write(f' "{value.description}"')
            if value.annotation:  # is not None or value.annotation != {}:
                self.write(" annotation", indent=False)
                self.write_annotation(value.annotation)
        elif isinstance(value, bool):
            if value is True:
                self.write(f"{key}=true", indent=False)
            else:
                self.write(f"{key}=false", indent=False)
        elif isinstance(value, Real):
            # self.write(f"{key}={value:.6g}", indent=True)
            # TODO: Decide how to print floating point numbers
            # self.write(f"{key}={value:.6g}", indent=False)
            self.write(f"{key}={value}", indent=False)
        elif isinstance(value, int):
            self.write(f"{key}={value}", indent=False)
        elif isinstance(value, tuple):
            # Format tuple as `{e0, e1, ...}`
            s = ", ".join(str(v) for v in value)
            self.write("%s={%s}" % (key, s), indent=False)
        else:
            assert isinstance(value, str), f"Expected str got `{type(value)}`"
            self.write(f"{key}={value}", indent=False)

    def visit_Algorithm(self, node: Algorithm) -> None:
        self.write(f"{node.left} := {node.right}", indent=True)
        if node.description is not None:
            self.write(f' "{node.description}"')
        if node.annotation is not None:
            self.write(" ")
            self.visit_Annotation(node.annotation)
        self.print(";", indent=False)

    def visit_Annotation(self, node: dict[str, Any]) -> None:
        self.write("annotation ")
        self.write_annotation(node)

    def visit_Assign(self, node: Assign) -> None:
        print(node)

    def write_annotation(self, anno: dict[str, Any]) -> None:
        # TODO: refactor me into a scheme similar to self.write_key_value. This
        # should also not print `(` and `)` at highest level as
        # `visit_Annotation` should do that
        if isinstance(anno, dict):
            if len(anno) == 0:
                return
            elif len(anno) == 1:
                self.write("(")
                k, v = next(iter(anno.items()))
                self.write(k)
                self.write_annotation(v)
                self.write(")")
            else:
                self.write("(")
                self.indent += 1

                first, *rest, last = list(anno.items())

                k, v = first
                self.write(k, indent=False)
                self.write_annotation(v)
                self.print(",", indent=False)

                for k, v in rest:
                    self.write(k, indent=True)
                    self.write_annotation(v)
                    self.print(",", indent=False)

                k, v = last
                self.write(k, indent=True)
                self.write_annotation(v)
                self.indent -= 1
                self.write(")", indent=False)

        elif isinstance(anno, (list, tuple)):
            if len(anno) == 0:
                # raise ValueError(anno)
                self.write("={}")
                return
            if isinstance(anno[0], dict):
                # TODO: provide a description when exactly this code is called
                self.print("={", indent=True)
                self.indent += 1
                *head, last = anno
                for e in head:
                    assert len(e) == 1, "only one object per array element allowed"
                    name, value = list(e.items())[0]
                    self.write(f"{name}", indent=True)
                    self.write_annotation(value)
                    self.print(",", indent=True)

                assert isinstance(last, dict)
                name, value = list(last.items())[0]
                self.write(f"{name}", indent=True)
                self.write_annotation(value)

                self.indent -= 1
                self.print(indent=False)
                self.write("}", indent=True)
            elif isinstance(anno[0], (list, tuple)):
                self.write("={")
                *head, last = anno
                for e in head:
                    elem_str = "{" + ",".join(str(x) for x in e) + "}"
                    self.write(elem_str)
                    self.write(",")
                elem_str = "{" + ",".join(str(x) for x in last) + "}"
                self.write(elem_str)

                self.write("}")
            else:
                # Its something like this: (0, "a", 3.14)
                elem_str = ",".join(str(e) for e in anno)
                self.write("={%s}" % elem_str)
        elif isinstance(anno, bool):
            if anno is True:
                self.write("=true")
            else:
                self.write("=false")
        else:
            # assert isinstance(anno, str), type(anno)
            # The rest should be primitive, i.e. int, float, str, etc.
            self.write(f"={anno}")

    def visit_Component(self, node: Component) -> None:
        self.write(indent=True)
        if node.flags is not None:
            if ComponentFlags.Final in node.flags:
                self.write("final ")
            if ComponentFlags.Inner in node.flags:
                self.write("inner ")
            if ComponentFlags.Outer in node.flags:
                self.write("outer ")

        if node.flux is not None:
            self.write(f"{node.flux.value} ")

        if node.variability is not None:
            self.write(f"{node.variability.value} ")

        if node.causality is not None:
            self.write(f"{node.causality.value} ")

        self.write(f"{node.type}")

        # NOTE: Currently subscripts in the component declaration (i.e. after the type) are not
        # supported
        if node.subscripts:
            s = ",".join(str(e) for e in node.subscripts)
            self.write(f"[{s}]")

        # Write modification and assignment
        self.write(f" {node.ident}")
        if node.init:
            # a bit hacky to pass ident="" maybe fix?
            self.write_key_value("", node.init)

        if node.value is not None:
            spacing = ""
            if node.init:
                spacing = " "
            self.write(f"{spacing}={spacing}")
            # TODO: Properly write value, especially for arrays!
            self.write(str(node.value))

        if node.condition is not None:
            self.write(f" if {node.condition}")

        if node.constraint is not None:
            raise NotImplementedError("constraints are not yet implemented")

        if node.description is not None:
            self.write(f' "{node.description}"')

        if node.annotation:
            self.write(" ")
            self.visit_Annotation(node.annotation)

        self.print(";", indent=False)

    def visit_Connect(self, node: Connect) -> None:
        self.write(f"connect({node.ref1}, {node.ref2})", indent=True)
        if node.description is not None:
            self.visit_Description(node.description)

        if node.annotation:
            self.write(" ")
            self.visit_Annotation(node.annotation)

        self.print(";", indent=False)

    def visit_Description(self, node: Description) -> None:
        self.write(f' "{node}"')

    def visit_Equation(self, node: Equation) -> None:
        self.write(f"{node.left} = {node.right}", indent=True)
        if node.description is not None:
            self.write(f' "{node.description}"')
        if node.annotation:
            self.write(" ")
            self.visit_Annotation(node.annotation)
        self.print(";", indent=False)

    def visit_Extends(self, node: Extends) -> None:
        self.print(f"extends {node.name};", indent=True)

    def visit_Expression(self, node: Expression) -> None:
        self.write(node.value)

    def visit_IfEquation(self, node: IfEquation) -> None:
        self.write("if ", indent=True)
        self.visit(node.test)
        self.print(" then", indent=False)
        self.indent += 1
        for eq in node.body:
            self.write(indent=True)
            self.visit(eq)
            self.print(";", indent=False)
        self.indent -= 1
        for expr, eqs in node.elseif:
            self.write("elseif ", indent=True)
            self.write(indent=True)
            self.visit(expr)
            self.write(" then")
            self.indent += 1
            for eq in eqs:
                self.write(indent=True)
                self.visit(eq)
                self.print(";", indent=False)
            self.indent -= 1
        if node.orelse is not None:
            self.print("else", indent=True)
            self.visit(node.orelse)
        self.print("end if;", indent=True)

    def visit_Model(self, node: Model) -> None:
        if node.within is not None:
            self.visit_Within(node.within)

        if node.flags is not None:
            if ModelFlags.Final in node.flags:
                self.write("final ")
            if ModelFlags.Encapsulated in node.flags:
                self.write("encapsulated ")
            if ModelFlags.Partial in node.flags:
                self.write("partial ")
            if ModelFlags.Replaceable in node.flags:
                self.write("replaceable ")

        if node.description is not None:
            self.print(f'model {node.ident} "{node.description}"', indent=True)
        else:
            self.print(f"model {node.ident}", indent=True)
        self.indent += 1

        for e in node.public_section:
            self.visit(e)

        if len(node.protected_section) > 0:
            self.indent -= 1
            self.print("protected", indent=True)
            self.indent += 1
            for e in node.protected_section:
                self.visit(e)

        if len(node.initial_equations) > 0:
            self.indent -= 1
            self.print("initial equation", indent=True)
            self.indent += 1
            for e in node.initial_equations:
                self.visit(e)
        if len(node.initial_algorithms) > 0:
            self.indent -= 1
            self.print("initial algorithm", indent=True)
            self.indent += 1
            for e in node.initial_algorithms:
                self.visit(e)

        if len(node.equations) > 0:
            self.indent -= 1
            self.print("equation", indent=True)
            self.indent += 1
            for e in node.equations:
                self.visit(e)
        if len(node.algorithms) > 0:
            self.indent -= 1
            self.print("algorithm", indent=True)
            self.indent += 1
            for e in node.algorithms:
                self.visit(e)

        if node.annotation:
            self.visit_Annotation(node.annotation)
            self.print(";", indent=False)

        self.indent -= 1
        self.print(f"end {node.ident};", indent=True)

    def visit_MultiImport(self, node: MultiImport) -> None:
        self.print("import %s.{%s};" % (node.path, ", ".join(node.names)), indent=True)

    def visit_NamedImport(self, node: NamedImport) -> None:
        self.print(f"import {node.short} = {node.long};", indent=True)

    def visit_QualifiedImport(self, node: QualifiedImport) -> None:
        self.print(f"import {node.name};", indent=True)

    def visit_str(self, node: str) -> None:
        self.write(node)

    def visit_Text(self, node: Text) -> None:
        for e in node:
            self.print(e, indent=node.indent)

    def visit_Within(self, node: Within) -> None:
        if node.name is None:
            self.print("within;", indent=True)
        else:
            self.print(f"within {node.name};", indent=True)


def get_component_origin(c: Component) -> Optional[tuple[float, float]]:
    placement = c.annotation.get("Placement")
    if placement is None:
        return None

    transformation = placement.get("transformation")
    if transformation is None:
        return None

    value: Optional[tuple[float, float]] = transformation.get("origin")
    return value


def draw_connect(
    c: Connect,
    idents: dict[str, Any],
) -> None:
    parts = c.ref1.rsplit(".", 1)
    comp1 = idents.get(parts[0])
    if comp1 is None:
        return
    pos1 = get_component_origin(comp1)
    if pos1 is None:
        return

    parts = c.ref2.rsplit(".", 1)
    comp2 = idents.get(parts[0])
    if comp2 is None:
        return
    pos2 = get_component_origin(comp2)
    if pos2 is None:
        return

    line = c.annotation.setdefault("Line", {})
    # NOTE: No need to give specific points of the line, Dymola autoroutes this
    line["points"] = ((0, 0), (10, 10))  # =(pos1, pos2)
    line["color"] = (0, 0, 255)


def draw_connections(m: Model) -> None:
    idents = {}
    for e in m.public_section:
        if isinstance(e, Component):
            idents[e.ident] = e
    for e in m.protected_section:
        if isinstance(e, Component):
            idents[e.ident] = e

    for e in m.equations:
        if isinstance(e, Connect):
            draw_connect(e, idents)


def pprint(
    o: Any,
    stream: None | TextIO = sys.stdout,
    *,
    draw_connections: bool = False,
    indentation: str = "  ",
    width: int = 80,
    start_indent: int = 0,
) -> Optional[str]:
    if stream is None:
        stream = StringIO()
        printer = PrettyPrinter(
            stream,
            indentation=indentation,
            width=width,
            start_indent=start_indent,
            draw_connections=draw_connections,
        )
        printer.visit(o)

        val: str = stream.getvalue()
        return val

    printer = PrettyPrinter(
        stream,
        indentation=indentation,
        width=width,
        start_indent=start_indent,
        draw_connections=draw_connections,
    )
    printer.visit(o)
    return None


def save(
    model: Model,
    folder: Path,
    draw_connections: bool = True,
) -> None:
    """Save a modelipy model to folder/<model.ident>."""
    assert folder.is_dir(), f"folder `{folder}` is not a directory"
    package_order_file = folder / "package.order"
    assert package_order_file.exists(), f"package order file {package_order_file} does not exist"

    fn = folder / f"{model.ident}.mo"
    with open(fn, "w") as f:
        pprint(model, f, draw_connections=draw_connections)

    # Add saved model to package.order
    elements = [line.strip() for line in open(package_order_file)]
    if model.ident not in elements:
        elements.append(model.ident)
    with open(folder / "package.order", "w") as f:
        for e in elements:
            print(e, file=f)
