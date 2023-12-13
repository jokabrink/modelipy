#!/usr/bin/env python3

from itertools import pairwise

from modelipy import Model, add_component, add_connect, add_import, add_text, pprint, set_experiment
from modelipy.component import set_placement
from modelipy.output import draw_connections

hot_rod_element = """model RodElement
  SI.Temperature T annotation (Dialog(showStartAttribute=true));
  parameter SI.HeatCapacity C = 1 "Heat capacity";
  parameter SI.ThermalConductance G = 1 "Thermal conductivity";
public 
  Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_a port_a annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));
  Modelica.Thermal.HeatTransfer.Interfaces.HeatPort_b port_b annotation (Placement(transformation(extent={{90,-10},{110,10}})));
  Modelica.Thermal.HeatTransfer.Components.ThermalConductor thermalConductor(G=2*G) annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Thermal.HeatTransfer.Components.ThermalConductor thermalConductor1(G=2*G) annotation (Placement(transformation(extent={{40,-10},{60,10}})));
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor heatCapacitor(C=C) annotation (Placement(transformation(extent={{-10,20},{10,40}})));
equation 
  T = heatCapacitor.T;
  connect(thermalConductor.port_a, port_a) annotation (Line(points={{-60,0},{-100,0}}, color={191,0,0}));
  connect(thermalConductor.port_b, thermalConductor1.port_a) annotation (Line(points={{-40,0},{40,0}}, color={191,0,0}));
  connect(port_b, thermalConductor1.port_b) annotation (Line(points={{100,0},{60,0}}, color={191,0,0}));
  connect(thermalConductor.port_b, heatCapacitor.port) annotation (Line(points={{-40,0},{0,0},{0,20}}, color={191,0,0}));
  annotation (Icon(coordinateSystem(preserveAspectRatio=false)), Diagram(coordinateSystem(preserveAspectRatio=false)));
end RodElement;
"""

info = """<html>
<p>Simulation of a 1D rod that is kept at a fixed temperature at both sides. The initial temperature is zero. On simulation start the temperature of the left side is set to 150 °C.
</p>
<p>
The rod comprises of 15 elements which are adjacently connected. Each represent a small portion of the rod with itsheat equation dynamics.
</p>
</html>"""


m = Model("HotRod")
add_import(m, "Modelica.Thermal.HeatTransfer.Sources")
add_text(m, *hot_rod_element.split("\n"), indent=True)

add_component(m, "Sources.FixedTemperature", "fixedTemperature1", {"T": "423.15"}, pos=(-100, 0))
add_component(m, "Sources.FixedTemperature", "fixedTemperature2", {"T": "273.15"}, pos=(100, 0))

elements = []
for i in range(15):
    e = add_component(m, "RodElement", f"dx{i:02d}", {"T": {"start": "273.15", "fixed": True}})
    elements.append(e)

add_connect(m, "fixedTemperature1", "port", elements[0].ident, "port_a")
add_connect(m, elements[-1].ident, "port_b", "fixedTemperature2", "port")

for left, right in pairwise(elements):
    add_connect(m, left, "port_b", right, "port_a")

for i, element in enumerate(elements):
    set_placement(element, pos=(15 * i - 90, 20), size=5)

set_experiment(m, stop=30)

m.annotation["Documentation"] = {"info": f'"{info}"'}
draw_connections(m)

pprint(m, draw_connections=True)
