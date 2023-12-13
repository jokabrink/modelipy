# Copyright (c) 2023, Jonas Kock am Brink

from __future__ import annotations

import enum
import sys
from dataclasses import dataclass
from math import pi
from typing import Any, Optional, Union

from .misc import Assign, Constraint, Expression, Primitive


class ComponentFlags(enum.Flag):
    """Do not include a default case because this is handled by None. The advantage is that None and
    Flags are exclusive while a default case flag and other flags can be combined."""

    Final = enum.auto()
    Inner = enum.auto()
    Outer = enum.auto()
    Replaceable = enum.auto()


str2ComponentFlags = {
    "final": ComponentFlags.Final,
    "inner": ComponentFlags.Inner,
    "outer": ComponentFlags.Outer,
    "replaceable": ComponentFlags.Replaceable,
}


class Flux(enum.Enum):
    Flow = "flow"
    Stream = "stream"


class Causality(enum.Enum):
    Input = "input"
    Output = "output"


class Variability(enum.Enum):
    Constant = "constant"
    Parameter = "parameter"
    Discrete = "discrete"


@dataclass
class Component:
    # TODO: There are two types of subscripts, one in the component declaration, and one in the
    # component definition
    """
    type: str
    ident: str
    value: Optional[Primitive]
    init: dict[str, Union[Primitive, Assign, dict[str, Any]]]
    condition: Optional[Expression]
    constraint: Optional[Constraint]
    description: Optional[str]
    annotation: dict[str, Any]
    subscripts: list[str]
    variability: Optional[Variability]
    causality: Optional[Causality]
    flow: Optional[Flux]
    flags: Optional[ComponentFlags]
    """

    # Shortcut for flags
    final = ComponentFlags.Final
    inner = ComponentFlags.Inner
    outer = ComponentFlags.Outer
    replaceable = ComponentFlags.Replaceable

    flow = Flux.Flow
    stream = Flux.Stream

    constant = Variability.Constant
    parameter = Variability.Parameter
    discrete = Variability.Discrete

    input = Causality.Input
    output = Causality.Output

    def __init__(
        self,
        type: str,
        ident: str,
        value: Optional[Primitive] = None,
        init: Optional[dict[str, Union[Primitive, Assign, dict[str, Any]]]] = None,
        *,
        flags: Optional[ComponentFlags] = None,
        variability: Optional[Variability] = None,
        causality: Optional[Causality] = None,
        flux: Optional[Flux] = None,
        subscripts: Optional[list[str]] = None,
        condition: Optional[Expression] = None,
        constraint: Optional[Constraint] = None,
        description: Optional[str] = None,
        annotation: Optional[dict[str, Any]] = None,
    ):
        self.type = type
        self.ident = ident
        self.value = value
        self.init = {} if init is None else init
        self.flags = flags
        self.variability = variability
        self.causality = causality
        self.flux = flux
        self.subscripts = [] if subscripts is None else subscripts
        self.condition = condition
        self.constraint = constraint
        self.description = description
        self.annotation = {} if annotation is None else annotation

    def __setitem__(
        self,
        key: str,
        value: Union[Primitive, Assign, dict],
    ) -> None:
        self.init[key] = value

    def __getitem__(self, key: str) -> Union[Primitive, Assign, dict]:
        return self.init[key]


def set_placement(
    component: Component,
    pos: tuple[float, float],
    flip: Optional[str] = None,
    rotation: Optional[float] = None,
    size: int = 10,
    visible: Optional[bool] = None,
) -> None:
    """Set the position of a `component` to the `pos`-ition. Flip `horiz` or
    `vert`, or rotate by `rotation` degreees if the values are given."""
    placement = component.annotation.setdefault("Placement", {})
    # record Placement: visible, transformation, iconVisible, iconTransformation
    if visible is not None:
        placement["visible"] = visible
    transf = placement.setdefault("transformation", {})
    if transf:
        print(
            "WARNING: Overwriting placement transformation for component {component.ident}",
            file=sys.stderr,
        )

    # record Transformation: origin, extent, rotation
    if flip == "horiz":
        transf["extent"] = [[size, -size], [-size, size]]
    elif flip == "vert":
        transf["extent"] = [[-size, size], [size, -size]]
    else:
        transf["extent"] = [[-size, -size], [size, size]]

    if rotation is not None:
        transf["rotation"] = rotation

    transf["origin"] = pos
