#!/usr/bin/env python3

from modelipy import Model, Component, add_component, add_equation, pprint

m = Model("LinearODE", "This is a linear ordinary differential equation")

add_component(
    m,
    "Real",
    "alpha",
    value=1,
    init={"min": 0},
    parameter=True,
    description="negative value results in blow up",
)

c = Component("Real", "x", init={"start": 1, "fixed": True})
m.add(c)

add_equation(m, "der(x)", "-alpha*x", description="linear ODE")

pprint(m)
