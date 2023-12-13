# Copyright (c) 2023, Jonas Kock am Brink

from __future__ import annotations

from math import floor
from pathlib import Path
from typing import Any, Callable, Optional


def position_between(
    p1: tuple[float, float],
    p2: tuple[float, float],
) -> dict[str, Any]:
    """Position object between two point `p1` and `p2`.
    Returns a dictionary with the necessary annotations.
    Example
    -------
    >>> position_between((0,0), (2,0))
    {'pos': (1.0, 0.0)}
    >>> position_between((0,0), (0,2))
    {'pos': (0.0, 1.0), 'rotation': 90}
    """
    px = (p2[0] + p1[0]) / 2
    py = (p2[1] + p1[1]) / 2

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    # TODO: rename dct["pos"] to "origin", do this in model.py also

    dct: dict[str, Any] = {"pos": (px, py)}

    if abs(dy) > abs(dx):
        if dy > 0:
            dct["rotation"] = 90
        else:
            dct["rotation"] = 270
    else:
        if dx < 0:
            dct.update(flip="horiz")

    return dct


def round_even(f: float) -> int:
    """Round a floating point number `f` to an even integer value and return it.
    From: https://stackoverflow.com/a/25361807

    Example:
    --------
    >>> round_even(0.9)
    0
    >>> round_even(1.1)
    2
    >>> round_even(-2.9)
    -2
    >>> round_even(-2.5)
    -2
    """
    return round(f / 2.0) * 2


def round_odd(f: float) -> int:
    """Round a floating point number `f` to an odd integer value and return it.

    Example:
    --------
    >>> round_odd(0.0)
    1
    >>> round_odd(1.9)
    1
    >>> round_odd(2.0)
    3
    >>> round_odd(-2.9)
    -3
    """
    return floor(f / 2) * 2 + 1


def map2d(
    src: tuple[tuple[float, float], tuple[float, float]],
    dst: tuple[tuple[float, float], tuple[float, float]],
    rounding: Optional[str] = None,
) -> Callable[[tuple[float, float]], Any]:
    """Creates functor that maps from `src` to `dst`
    >>> mapper = map2d(((0,0), (1,1)), ((-10,-10), (10,10)))
    >>> mapper((0.346, 0.951))
    (-3.08, 9.02)

    >>> mapper = map2d(((0,0), (1,1)), ((-10,-10), (10,10)), rounding="even")
    >>> mapper((0.346, 0.951))
    (-4, 10)

    bounding boxes are ((left,down), (right,up)) border tuples
    """
    # horizontal: x_new = m_x * x + b_x
    # vertical:   y_new = m_y * y + b_y

    m_x = (dst[0][0] - dst[1][0]) / (src[0][0] - src[1][0])
    b_x = dst[0][0] - m_x * src[0][0]

    m_y = (dst[0][1] - dst[1][1]) / (src[0][1] - src[1][1])
    b_y = dst[0][1] - m_y * src[0][1]

    if rounding == "even":
        return lambda pos: (round_even(m_x * pos[0] + b_x), round_even(m_y * pos[1] + b_y))
    elif rounding == "odd":
        return lambda pos: (round_odd(m_x * pos[0] + b_x), round_odd(m_y * pos[1] + b_y))
    else:
        return lambda pos: (m_x * pos[0] + b_x, m_y * pos[1] + b_y)


"""
# TODO:
@dataclass
class Transformation:
    origin: tuple[float,float]
    extent: tuple[tuple[float,float],tuple[float,float]]
    rotation: float

@dataclass
class Placement:
    visible: bool
    transformation: Transformation
    icon_visible: bool
    icon_transformation: Transformation
"""


def create_dict(
    root: dict[str, Any],
    path: list[str],
) -> dict[str, Any]:
    """Given a tree-like dictionary, traverse along path and create necessary
    dict items if necessary.
    Examples:
    ---------
    >>> d = {}
    >>> res = create_dict(d, ["Layer", "Diagram"])
    >>> res["is_diagram"] = True
    >>> d
    {'Layer': {'Diagram': {'is_diagram': True}}}
    """
    node = root
    for i, p in enumerate(path):
        node = node.setdefault(p, {})
        if type(node) is not dict:
            raise ValueError(f"node at `{path[:i]}` already exists and is not a dictionary")
    return node


def get_dict(
    dct: dict[str, Any],
    path: list[str],
) -> Optional[dict[str, Any]]:
    """Given a tree-like dictionary, traverse along path and return dictionary
    if found.

    Examples:
    ---------
    >>> d = {"Layer": {"Diagram": {}}}
    >>> res = get_dict(d, ["Layer", "Diagram"])
    >>> res["is_diagram"] = True
    >>> d
    {'Layer': {'Diagram': {'is_diagram': True}}}
    >>> get_dict(d, ["Diagram"])
    None
    """
    node = dct
    for i, p in enumerate(path):
        if p not in node:
            return None
        node = node[p]
        if type(node) is not dict:
            raise ValueError(f"node at `{path[:i]}` already exists and is not a dictionary")
    return node
