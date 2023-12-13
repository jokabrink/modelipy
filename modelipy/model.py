# Copyright (c) 2023 Jonas Kock am Brink

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Optional, TypeVar, Union
from warnings import warn

from .component import Component, ComponentFlags, Variability, set_placement, str2ComponentFlags
from .condition import IfEquation
from .misc import (
    Algorithm,
    Assign,
    Connect,
    Equation,
    Extends,
    Import,
    MultiImport,
    NamedImport,
    Primitive,
    QualifiedImport,
    StarImport,
    Text,
    Within,
)


class ModelFlags(enum.Flag):
    Final = enum.auto()
    Encapsulated = enum.auto()
    Partial = enum.auto()
    Replaceable = enum.auto()


@dataclass
class Model:
    ident: str
    description: Optional[str]
    within: Optional[Within]
    flags: Optional[ModelFlags]
    annotation: dict[str, Any]
    components: dict[str, Component]
    public_section: list
    protected_section: list
    initial_equations: list
    initial_algorithms: list
    equations: list
    algorithms: list

    # Model flags. Alternative: use flags="final partial" so separated str as flags
    final = ModelFlags.Final
    encapsulated = ModelFlags.Encapsulated
    partial = ModelFlags.Partial
    replaceable = ModelFlags.Replaceable

    def __init__(
        self,
        ident: str = "Unnamed",
        description: Optional[str] = None,
        within: Optional[str] = None,
        flags: Optional[ModelFlags] = None,
        annotation: Optional[dict[str, Any]] = None,
    ):
        self.ident = ident
        self.description = description
        self.within = None if within is None else Within.from_str(within)
        self.flags = flags
        self.annotation = {} if annotation is None else annotation
        self.components = {}

        self.public_section = []
        self.protected_section = []
        self.initial_equations = []
        self.initial_algorithms = []
        self.equations = []
        self.algorithms = []

    T = TypeVar("T")

    def add(self, some: T, where: str = "public") -> T:
        if where == "public":
            self.public_section.append(some)
        elif where == "protected":
            self.protected_section.append(some)
        elif where == "initial equation":
            self.initial_equations.append(some)
        elif where == "initial algorithm":
            self.initial_algorithms.append(some)
        elif where == "equation":
            self.equations.append(some)
        elif where == "algorithm":
            self.algorithms.append(some)
        else:
            raise ValueError(f"where={where} unknown")

        return some

    """TODO: Should Model() be able to do this?
    >>> "comp1" in model
    True
    >>> model["comp1"]
    Component()
    """


def add_algorithm(
    model: Model,
    left: Any,
    right: Any,
    *,
    initial: bool = False,
    description: Optional[str] = None,
    annotation: Optional[dict[str, Any]] = None,
) -> Algorithm:
    alg = Algorithm(left, right, description=description, annotation=annotation)

    if initial:
        model.initial_algorithms.append(alg)
    else:
        model.algorithms.append(alg)
    return alg


def add_annotation(
    model: Model,
    path: list[str],
    anno: dict[str, Any],
    replace: bool = True,
) -> None:
    annotation = model.annotation
    for p in path:
        if p not in annotation.keys():
            annotation[p] = {}
        else:
            if replace is True:
                annotation[p] = {}
            else:
                raise ValueError("Not allowed to replace '{p}'")


def add_comment(
    model: Model,
    *lines: str,
    indent: bool = False,
    type: str = "//",
    where: str = "public",
) -> Text:
    """
    types:
    - `//`
    - `///`
    - `/*`
    - `/**`
    """
    if type == "//":
        is_multi = False
        start_prefix = "// "
        prefix = "// "
    elif type == "///":
        is_multi = False
        start_prefix = "/// "
        prefix = "/// "
    elif type == "/*":
        is_multi = True
        start_prefix = "/* "
        prefix = " * "
    elif type == "/**":
        is_multi = True
        start_prefix = "/** "
        prefix = " * "
    elif type == "":
        is_multi = False
        start_prefix = ""
        prefix = ""
    else:
        raise ValueError(f"'{type}' is not a valid parameter for `type`")

    end_prefix = " */" if is_multi else ""

    parts = []

    # TODO: Should I add a newline here?
    if len(lines) == 1:
        parts.append(start_prefix + lines[0] + end_prefix + "")
    else:
        first, *rest, last = lines
        parts.append(start_prefix + first + "")
        for e in rest:
            parts.append(prefix + e + "")
        parts.append(prefix + last + " */")

    text = Text(parts, indent=indent)
    model.add(text, where=where)
    return text


def add_component(
    model: Model,
    typ: str,
    ident: str,
    # value: Optional[Primitive] = None,
    value: Union[None, Primitive, dict[str, Union[Primitive, dict[str, Any], Assign]]] = None,
    *,
    init: Optional[dict[str, Union[Primitive, dict[str, Any], Assign]]] = None,
    protected: bool = False,
    parameter: bool = False,
    flags: Union[None, str, ComponentFlags] = None,
    **kwargs: Any,
) -> Component:
    """Create and add a component to the model. Optionally set its position:
    - flags: Optional[ComponentFlags] = None,
    - variability: Optional[Variability] = None,
    - causality: Optional[Causality] = None,
    - flux: Optional[Flux] = None,
    - subscripts: Optional[list[str]] = None,
    - condition: Optional[Expression] = None,
    - constraint: Optional[Constraint] = None,
    - description: Optional[str] = None,
    - annotation: Optional[dict[str, Any]] = None,
    """

    if ident in model.components:
        raise KeyError(f"component with ident {ident} already exists")

    # Make it possible to pass initialization as value
    if isinstance(value, dict):
        assert not isinstance(init, dict), "cannot pass initialization twice"
        init = value
        value = None

    if isinstance(flags, str):
        parts = flags.split()
        if len(parts) > 0:
            flgs = str2ComponentFlags[parts[0]]
            for part in parts[1:]:
                flgs |= str2ComponentFlags[part]

            kwargs["flags"] = flgs
    elif isinstance(flags, ComponentFlags):
        kwargs["flags"] = flags
    else:
        assert flags is None, "'flags' must be of type str, ComponentFlags or None"

    valid_pos_keys = {"pos", "size", "rotation", "flip"}
    pos_keys = kwargs.keys() & valid_pos_keys

    component_kwargs = {k: kwargs[k] for k in kwargs.keys() - pos_keys}
    if parameter:
        component_kwargs["variability"] = Variability.Parameter

    if init is None:
        init = {}

    c = Component(typ, ident, value=value, init=init, **component_kwargs)

    if pos_keys:
        pos_dict = {k: kwargs[k] for k in pos_keys}
        set_placement(c, **pos_dict)

    if protected:
        model.protected_section.append(c)
    else:
        model.public_section.append(c)
    model.components[ident] = c

    return c


def add_connect(
    model: Model,
    ref1: Any,
    ref2: Any,
    *args: Any,
    description: None | str = None,
) -> Connect:
    """
    add_connect("bus1.port1", "bus2.port2")
    add_connect("bus1", "port1", "bus2", "port2")
    add_connect(component1, "port1", component2, "port2")
    """
    if len(args) == 0:
        c = Connect(ref1, ref2, description=description)
    elif len(args) == 2:
        if isinstance(ref1, Component):
            name1 = ref1.ident
        else:
            name1 = ref1

        arg1, port2 = args
        if isinstance(arg1, Component):
            name2 = arg1.ident
        else:
            name2 = arg1

        s1 = f"{name1}.{ref2}"
        s2 = f"{name2}.{port2}"
        c = Connect(s1, s2, description=description)

    else:
        # TODO: Improve the message. The number of args have to match the examples
        raise ValueError("Too many or too few args.")
    model.add(c, where="equation")
    return c


def add_equation(
    model: Model,
    left: Any,
    right: Any,
    *,
    initial: bool = False,
    description: Optional[str] = None,
    annotation: Optional[dict[str, Any]] = None,
) -> Equation:
    annotation = {} if annotation is None else annotation

    eq = Equation(
        left,
        right,
        description=description,
        annotation=annotation,
    )
    if initial:
        model.initial_equations.append(eq)
    else:
        model.equations.append(eq)
    return eq


def add_extends(
    model: Model,
    name: str,
) -> Extends:
    e = Extends(name)
    model.public_section.append(e)
    return e


def add_import(
    model: Model,
    name: str,
    arg: Union[None, str, list[str]] = None,
    *,
    comment: str = "",
    annotation: Optional[dict[str, Any]] = None,
) -> Import:
    """
    Examples:
    ---------
    - add_import("A.B.C")) -> 'import A.B.C;'
    - add_import("A.B.C.*")) -> 'import A.B.C.*;'
    - add_import("A.B", ["C", "E"])) -> 'import A.B.{C, E};'
    - add_import("A.B", "C")) -> 'import C=A.B;'
    """
    i: Union[QualifiedImport, MultiImport, NamedImport]
    if arg is None:
        i = QualifiedImport(name=name)
    elif isinstance(arg, list):
        i = MultiImport(name, arg)
    else:
        assert isinstance(arg, str)
        i = NamedImport(short=arg, long=name)
    return model.add(i)


def add_parameter(
    model: Model,
    typ: str,
    ident: str,
    value: Optional[Primitive] = None,
    *,
    init: Optional[dict[str, Union[Primitive, dict[str, Any], Assign]]] = None,
    protected: bool = False,
    **kwargs: Any,
) -> Component:
    kwargs["parameter"] = True
    kwargs["init"] = init
    kwargs["protected"] = protected
    return add_component(model, typ, ident, value=value, **kwargs)


def add_text(
    model: Model,
    *lines: str,
    indent: bool = False,
    where: str = "public",
) -> Text:
    text = Text(lines=list(lines), indent=indent)
    model.add(text, where=where)
    return text


def set_experiment(
    model: Model,
    start: int = 0,
    stop: int = 1,
    tolerance: Optional[float] = None,
    interval: Optional[float] = None,
    **kwargs: Any,
) -> None:
    """Given a `model`, set often used experiment parameters in its annotation."""
    experiment = model.annotation.setdefault("experiment", {})
    if start != 0:
        experiment["StartTime"] = start
    if stop != 1:
        experiment["StopTime"] = stop
    if tolerance is not None:
        experiment["Tolerance"] = tolerance
    if interval is not None:
        experiment["Interval"] = interval
    for key, value in kwargs.items():
        experiment[key] = value


def set_extent(
    m: Model,
    extent: tuple[tuple[float, float], tuple[float, float]] = ((-100, -100), (100, 100)),
    layer: str = "both",
) -> None:
    """Set the drawing size of a `model` to the given `extent`.

    If `layer` is "both", apply the drawing size for the Icon and Diagram
    layer of the model.
    """
    if layer == "both":
        coord_sys = m.annotation.setdefault("Diagram", {}).setdefault("coordinateSystem", {})
        coord_sys["extent"] = extent

        coord_sys = m.annotation.setdefault("Icon", {}).setdefault("coordinateSystem", {})
        coord_sys["extent"] = extent
    else:
        coord_sys = m.annotation.setdefault(layer, {}).setdefault("coordinateSystem", {})
        coord_sys["extent"] = extent
