#!/usr/bin/env python3
from modelipy import Assign, Component, Model, add_component, add_equation, pprint, set_experiment

m = Model(
    "LotkaVolterra",
    description="This model represents the Lotka-Volterra population dynamics system",
)
add_component(m, "Real", "alpha", value="2/3", parameter=True)
add_component(m, "Real", "beta", value="4/3", parameter=True)
add_component(m, "Real", "gamma", value=1, parameter=True)
add_component(m, "Real", "delta", value=1, parameter=True)

c = Component(
    "Real",
    "value",
    init={"start": Assign(1, flags=Assign.each), "fixed": True},
    subscripts=["2"],
)
m.add(c, where="public")
add_equation(m, "der(value)", "[alpha, -beta*value[1]; delta*value[2], -gamma] * value")

set_experiment(m, stop=2000, interval=0.1)

pprint(m)
