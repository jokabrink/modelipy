# Copyright (c) 2023, Jonas Kock am Brink

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Optional, Union

from .misc import Assign

# Similar to astropy: Units and Quanitites


@dataclass
class Unit:
    s: str
    factor: float
    fmt: Optional[str] = None

    def __rmul__(self, value: Union[int, float]) -> Assign:
        i = {"displayUnit": '"%s"' % self.s}
        fmt = ".9g" if self.fmt is None else self.fmt
        a = Assign(value=value * self.factor, init=i, fmt=fmt)
        return a

    # TODO: def __mul__(self, value) -> Assign:

    def __call__(self, fmt: str) -> Unit:
        self.fmt = fmt
        return self


km = Unit("km", 1000)
kV = Unit("kV", 1000)
kW = Unit("kW", 1000)
kvar = Unit("kvar", 1000)
kVA = Unit("kVA", 1000)
kA = Unit("kA", 1000)
kWh = Unit("kWh", 1000)

MV = Unit("MV", 1000000)
MW = Unit("MW", 1000000)
Mvar = Unit("Mvar", 1000000)
MVA = Unit("MVA", 1000000)
MWh = Unit("MWh", 1000000)

degrees = Unit("deg", pi / 180.0)
