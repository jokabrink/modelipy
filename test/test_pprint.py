from __future__ import annotations

from modelipy import Component, Model, pprint
from modelipy.misc import Assign

# mypy: allow-untyped-defs


def test_default_model():
    solution = """model Unnamed
end Unnamed;
"""
    assert pprint(Model(), stream=None) == solution


def test_model():
    solution = """within;
final encapsulated partial replaceable model TestModel "Test"
annotation (test=true);
end TestModel;
"""
    m = Model(
        "TestModel",
        description="Test",
        within="",
        flags=Model.final | Model.partial | Model.replaceable | Model.encapsulated,
        annotation={"test": True},
    )
    assert pprint(m, stream=None) == solution


def test_default_component():
    solution = "X x;\n"
    c = Component("X", "x")
    assert pprint(c, stream=None) == solution


def test_component():
    solution = 'final inner outer flow parameter input Real[4] x(min=0) = [1, 2, 3, 4] if True "" annotation (test=true);\n'
    c = Component(
        type="Real",
        ident="x",
        value=[1, 2, 3, 4],
        init={"min": 0},
        flags=Component.final | Component.inner | Component.outer | Component.replaceable,
        variability=Component.parameter,
        causality=Component.input,
        flux=Component.flow,
        subscripts=(4,),
        condition=True,
        # constraint=1,
        description="",
        annotation={"test": True},
    )
    assert pprint(c, stream=None) == solution


def test_nested_component():
    pass


def test_small_component():
    test = Component("X", "x", value=1)
    soln = "X x=1;\n"
    assert pprint(test, stream=None) == soln

    #

    test = Component("X", "x", init={"y": 1})
    soln = "X x(y=1);\n"
    assert pprint(test, stream=None) == soln

    #

    test = Component("X", "x", init={"y": 1, "z": 2})
    soln = """X x(y=1, z=2);
"""
    assert pprint(test, stream=None) == soln

    #

    test = Component("X", "x", init={"y": 1, "z": 2, "w": 3})
    soln = """X x(
  y=1,
  z=2,
  w=3);
"""
    assert pprint(test, stream=None) == soln


def test_assign():
    # TODO: Not implemented yet
    return
    solution = """
    """
    a = Assign(123, fmt=".2f", flags=Assign.each | Assign.final)
    s = pprint(a, stream=None)
    assert s == solution
