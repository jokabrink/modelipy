#!/usr/bin/env python3
import modelipy.units as u
from modelipy import (
    Component,
    Model,
    add_comment,
    add_component,
    add_connect,
    add_import,
    add_text,
    draw_connections,
    pprint,
)

m = Model("SimpleCircuit")
text = """// This file was automatically generated
// by modelipy

"""
add_text(m, text)

add_import(m, "Modelica.Electrical.Analog.Basic", ["Ground", "Resistor"])
add_import(m, "Modelica.Electrical.Analog.Sources.ConstantVoltage")

add_comment(m, "The needed components", indent=True, type="/*")
add_component(m, "ConstantVoltage", "source", value={"V": 1 * u.kV}, pos=(0, 0), flip="horiz")
ground = add_component(m, "Ground", "ground", pos=(10, -70))
resistor = add_component(m, "Resistor", "resistor", value={"R": 10}, pos=(0, -40))

add_connect(m, resistor, "p", "source", "n")
add_connect(m, resistor, "n", "source", "p")
add_connect(m, ground, "p", resistor, "n")

draw_connections(m)
pprint(m)
