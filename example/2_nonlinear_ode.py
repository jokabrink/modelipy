#!/usr/bin/env python3
from modelipy import Component, Model, add_comment, add_component, add_equation, add_import, pprint
from modelipy.condition import If

m = Model("NonlinearODE", description="This model represents the non-linear damped pendulum")
add_import(m, "Modelica.Units.SI")
add_component(m, "SI.Acceleration", "g", "9.81", parameter=True)
add_component(m, "SI.Length", "l", 1, parameter=True)
add_component(m, "Real", "d", 1, description="Friction coefficient", parameter=True)

add_component(m, "SI.Angle", "theta", {"start": 1, "fixed": True})
add_component(m, "SI.AngularVelocity", "d_theta")

add_comment(m, "The set of equations", where="initial equation", indent=True)
add_equation(m, "der(theta)", "0", initial=True)
add_equation(m, "der(d_theta) + d*d_theta + g/l * sin(theta)", "0")
add_equation(m, "der(theta)", "d_theta")

pprint(m)
