#!/usr/bin/env python3
from modelipy import Model, add_component, add_equation, pprint, set_experiment

m = Model(
    "LorenzAttractor",
    description="This model represents the chaotic Lorenz attractor",
)
add_component(m, "Real", "rho", value=28, parameter=True)
add_component(m, "Real", "sigma", value=10, parameter=True)
add_component(m, "Real", "beta", value="8/3", parameter=True)

add_component(m, "Real", "x")
add_component(m, "Real", "y")
add_component(m, "Real", "z")

add_equation(m, "x", 0, initial=True)
add_equation(m, "y", 2, initial=True)
add_equation(m, "z", 20, initial=True)

add_equation(m, "der(x)", "sigma*(y-x)")
add_equation(m, "der(y)", "x*(rho-z)-y")
add_equation(m, "der(z)", "x*y - beta*z")

set_experiment(m, stop=100, interval=0.01)

pprint(m)
