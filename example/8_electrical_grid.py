#!/usr/bin/env python3
# Copyright (c) 2023, Jonas Kock am Brink
import math
import sys
from typing import Callable

import modelipy.units as u
from modelipy import Model, add_comment, add_component, add_connect, add_import, add_text, pprint

try:
    import pandapower as pp  # type: ignore
    import pandapower.networks  # type: ignore
except ModuleNotFoundError:
    print("To run this example, please install 'pandapower'.", file=sys.stderr)
    sys.exit(1)


# fmt: off
### COMMENT OUT A DESIRED NETWORK
net = pp.networks.create_synthetic_voltage_control_lv_network()     # 0.4 kV, 26 nodes
# net = pp.networks.create_cigre_network_mv(with_der=True)          # 20 kV, 15 nodes
# net = pp.networks.create_cigre_network_hv(length_km_6a_6b=0.1)    # 220/380 kV, 13 nodes
# net = pp.networks.case1354pegase()                                # 220/380 kV, 1354 nodes
# fmt: on

net.bus["name"] = "bus_" + net.bus.index.astype(str)
net.load["name"] = "load_" + net.load.index.astype(str)
net.line["name"] = "line_" + net.line.index.astype(str)
net.gen["name"] = "gen_" + net.gen.index.astype(str)
net.shunt["name"] = "shunt_" + net.shunt.index.astype(str)
net.ext_grid["name"] = "ext_grid_" + net.ext_grid.index.astype(str)
net.sgen["name"] = "sgen_" + net.sgen.index.astype(str)
net.trafo["name"] = "trafo_" + net.trafo.index.astype(str)


pp.runpp(net, trafo_model="pi")
busses = net.bus.join(net.res_bus).join(net.bus_geodata)


def mapper_factory(
    from_bbox: tuple[float, float, float, float],
    to_bbox: tuple[float, float, float, float],
) -> Callable[[tuple[float, float]], tuple[float, float]]:
    def mapper(p: tuple[float, float]) -> tuple[float, float]:
        x, y = p
        m_x = (to_bbox[1] - to_bbox[0]) / (from_bbox[1] - from_bbox[0])
        b_x = to_bbox[0] - m_x * from_bbox[0]
        m_y = (to_bbox[3] - to_bbox[2]) / (from_bbox[3] - from_bbox[2])
        b_y = to_bbox[2] - m_y * from_bbox[2]
        return m_x * x + b_x, m_y * y + b_y

    return mapper


from_bbox = (
    net.bus_geodata["x"].min(),
    net.bus_geodata["x"].max(),
    net.bus_geodata["y"].min(),
    net.bus_geodata["y"].max(),
)
to_bbox = (-100, 100, -100, 100)  # (left, right, up, down)

mapper = mapper_factory(from_bbox, to_bbox)


#
# Generate the model
#

node_model = """\
model Node "Single bus node"
  outer TransiEnt.SimCenter simCenter;

  final SI.PerUnit v_pu=v/v_n;
  final SI.Voltage v(displayUnit="kV") = epp.v;
  final SI.Angle delta(displayUnit="deg") = epp.delta;
  final SI.Frequency f=epp.f;

  parameter SI.Voltage v_n(displayUnit="kV") = simCenter.v_n "Nominal bus voltage";
  parameter SI.PerUnit v_pu_start=1 annotation (Dialog(group="Initialization"));
  parameter SI.Angle delta_start=0 annotation (Dialog(group="Initialization"));

  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp(v(start=v_pu_start*v_n), delta(start=
          delta_start)) annotation (Placement(transformation(extent={{-30,-30},{30,30}}),
        iconTransformation(
        extent={{-30,-30},{30,30}},
        rotation=0,
        origin={0,0})));

equation 
  epp.P = 0;
  epp.Q = 0;
  annotation (Icon(graphics={Text(
          extent={{-100,30},{100,-30}},
          lineColor={0,134,134},
          textString="%name",
          origin={0,50},
          rotation=180)}));
end Node;
"""


admittance_model = """\
model AdmittanceTwoPort "2-Port from admittance matrix"
  SI.ActivePower P_loss(displayUnit="MW") = epp_1.P + epp_2.P;
  SI.ReactivePower Q_loss(displayUnit="Mvar") = epp_1.Q + epp_2.Q;

  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp_1 annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-100,0}), iconTransformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-100,0})));
  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp_2 annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={100,0}), iconTransformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={100,0})));

  Complex Y_11=Complex(0);
  Complex Y_12=Complex(0);
  Complex Y_21=Y_12;
  Complex Y_22=Y_11;

  Complex V_1=ComplexMath.fromPolar(epp_1.v, epp_1.delta);
  Complex V_2=ComplexMath.fromPolar(epp_2.v, epp_2.delta);

equation 

  epp_1.f = epp_2.f;
  Connections.branch(epp_1.f, epp_2.f);

  Complex(epp_1.P, epp_1.Q) = ComplexMath.fromPolar(epp_1.v, epp_1.delta)*ComplexMath.conj(Y_11*
    ComplexMath.fromPolar(epp_1.v, epp_1.delta) + Y_12*ComplexMath.fromPolar(epp_2.v, epp_2.delta));
  Complex(epp_2.P, epp_2.Q) = ComplexMath.fromPolar(epp_2.v, epp_2.delta)*ComplexMath.conj(Y_12*
    ComplexMath.fromPolar(epp_1.v, epp_1.delta) + Y_22*ComplexMath.fromPolar(epp_2.v, epp_2.delta));
end AdmittanceTwoPort;
"""


line_model = """\
model Line "Transmission line given r,x,b"
  extends AdmittanceTwoPort(
    final Y_11=1/Complex(R, X) + Complex(0, B)/2,
    final Y_12=-1/Complex(R, X),
    final Y_21=Y_12,
    final Y_22=Y_11);

  final SI.Current i_loading=sqrt(max((epp_1.P^2 + epp_1.Q^2)/epp_1.v^2, (epp_2.P^2 + epp_2.Q^2)/
      epp_2.v^2)/3) "Overall current flow";
  final SI.PerUnit loading(displayUnit="%") = i_loading/(i_n*parallel) "Line current [pu]";

  parameter SI.Length length(displayUnit="km") "Line length";
  parameter Integer parallel=1 "Number of parallel lines";

  parameter Real r(displayUnit="Ohm/km") = 0.06e-3 "series resistance per m";
  parameter Real x(displayUnit="Ohm/km") = 0.301e-3 "series reactance per m";
  parameter Real b(displayUnit="uS/km") = 3.927e-9 "shunt susceptance per m";
  parameter SI.Current i_n(displayUnit="kA") = 1150 "Nominal current";

  final parameter SI.Impedance R=r*length/parallel;
  final parameter SI.Impedance X=x*length/parallel;
  final parameter SI.Conductance B=b*length*parallel;
end Line;
"""


simple_trafo_model = """\
model SimpleTransformer ""
  import Modelica.ComplexMath;

  SI.ActivePower P_loss(displayUnit="MW") = epp_1.P + epp_2.P;
  SI.ReactivePower Q_loss(displayUnit="Mvar") = epp_1.Q + epp_2.Q;

  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp_1 annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-100,0}), iconTransformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-100,0})));
  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp_2 annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={100,0}), iconTransformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={100,0})));

  parameter Boolean useInputRatio=false "Use voltage ratio input connector"
    annotation (choices(__Dymola_checkBox=true));
  parameter Boolean useInputAngle=false "Use voltage angle input connector"
    annotation (choices(__Dymola_checkBox=true));
  parameter Real ratio(min=0) = 1 "v_1/v_2 (Port-1 is HV)"
    annotation (Dialog(enable=not useInputRatio));
  parameter SI.Angle angle=0 "delta_1 - delta_2" annotation (Dialog(enable=not useInputAngle));
  parameter Real eta(
    min=0,
    max=1) = 1 "Transformer active power efficiency";

  Modelica.Blocks.Interfaces.RealInput inputRatio if useInputRatio "External voltage ratio" 
    annotation (Placement(transformation(
        extent={{-15,-15},{15,15}},
        rotation=270,
        origin={-40,115}), iconTransformation(
        extent={{-15,-15},{15,15}},
        rotation=270,
        origin={-40,115})));
  Modelica.Blocks.Interfaces.RealInput inputAngle if useInputAngle "External phase angle" 
    annotation (Placement(transformation(
        extent={{-15,-15},{15,15}},
        rotation=270,
        origin={40,115}), iconTransformation(
        extent={{-15,-15},{15,15}},
        rotation=270,
        origin={40,115})));

protected 
  Modelica.Blocks.Interfaces.RealInput ratio_internal;
  Modelica.Blocks.Interfaces.RealInput angle_internal;

equation 
  epp_1.f = epp_2.f;
  Connections.branch(epp_1.f, epp_2.f);

  if not useInputRatio then
    ratio_internal = ratio;
  else
    connect(ratio_internal, inputRatio);
  end if;

  if not useInputAngle then
    angle_internal = angle;
  else
    connect(angle_internal, inputAngle);
  end if;

  epp_1.v = epp_2.v*ratio_internal;
  epp_1.delta = epp_2.delta + angle_internal;

  P_loss = (1 - eta)*abs(epp_1.P);
  Q_loss = 0;
end SimpleTransformer;
"""


trafoloss_model = """\
model TransformerLoss
  extends AdmittanceTwoPort(
    final Y_11=1/Complex(R, X) + Complex(G, B)/2,
    final Y_12=-1/Complex(R, X),
    final Y_21=Y_12,
    final Y_22=Y_11);

  final SI.Current i_loading=sqrt(max((epp_1.P^2 + epp_1.Q^2)/epp_1.v^2, (epp_2.P^2 + epp_2.Q^2)/
      epp_2.v^2)/3) "Overall current flow";

  parameter SI.ApparentPower S_n(displayUnit="MVA") = 63e6 "Rated apparent power";
  parameter SI.Voltage v_n(displayUnit="kV") = 110000 "Rated voltage for loss side";
  parameter SI.PerUnit vk(displayUnit="%") = 0.18 "Relative short circuit voltage";
  parameter SI.PerUnit vk_r(displayUnit="%") = 0 "Real part of relative short circuit";
  parameter SI.PerUnit i_0(displayUnit="%") = 0 "Open circuit relative current";
  parameter SI.ActivePower P_Fe(displayUnit="kW") = 0 "Iron loss";
  parameter Boolean isTapped=false "=true, loss depends on tap ratio"
    annotation (choices(checkBox=true));
  parameter Integer parallel(min=1) = 1 "Number of parallel transformers";

  Modelica.Blocks.Interfaces.RealInput inputRatio if isTapped annotation (Placement(transformation(
        visible=isTapped,
        extent={{-20,-20},{20,20}},
        rotation=270,
        origin={-60,120})));

protected 
  final parameter Real Z_n=v_n^2/S_n;

  final parameter SI.Resistance r_k=vk_r*Z_n;
  final parameter SI.Reactance z_k=vk*Z_n;
  final parameter SI.Conductance y_m=i_0/Z_n;
  final parameter SI.Susceptance g_m=P_Fe/v_n^2;

  // Calculation of the values taken from pandapower
  final SI.Resistance R=r_k/parallel/ratioInternal^2;
  final SI.Reactance X=sqrt(max(z_k^2 - r_k^2, 0))/parallel/ratioInternal^2;
  final SI.Conductance G=g_m*parallel*ratioInternal^2;
  final SI.Susceptance B=-sign(i_0)*sqrt(max(y_m^2 - g_m^2, 0))*parallel*ratioInternal^2;

protected 
  final Modelica.Blocks.Interfaces.RealInput ratioInternal;

equation 
  if isTapped then
    connect(ratioInternal, inputRatio);
  else
    ratioInternal = 1;
  end if;
end TransformerLoss;
"""


trafo_model = """\
model Transformer "OLTC Transformer modeled after PandaPower"
  import Modelica.ComplexMath;

  SI.ActivePower P_loss(displayUnit="MW") = epp_1.P + epp_2.P;
  SI.ReactivePower Q_loss(displayUnit="Mvar") = epp_1.Q + epp_2.Q;

  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp_1 annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-100,0}), iconTransformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={-100,0})));
  TransiEnt.Basics.Interfaces.Electrical.ComplexPowerPort epp_2 annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={100,0}), iconTransformation(
        extent={{-10,-10},{10,10}},
        rotation=0,
        origin={100,0})));

  outer TransiEnt.SimCenter simCenter;

  final SI.PerUnit s_loading(displayUnit="%") "Loading w.r.t. nominal power";

  parameter SI.ApparentPower S_n(displayUnit="Mva") = 63e6;
  parameter SI.Voltage vn_hv(displayUnit="kV") = simCenter.v_n "Nominal HV voltage";
  parameter SI.Voltage vn_lv(displayUnit="kV") = 10000 "Nominal LV voltage";
  parameter SI.PerUnit vk(displayUnit="%") = 0.18 "Relative short circuit voltage";
  parameter SI.PerUnit vk_r(displayUnit="%") = 0 "Real part of relative short circuit";
  parameter SI.ActivePower P_Fe(displayUnit="kW") = 0 "Iron loss";
  parameter SI.PerUnit i_0(displayUnit="%") = 0 "Open circuit relative current";
  parameter Integer parallel(min=1) = 1 "Number of parallel transformers";
  parameter Real ratio=1.0 "Transformer ratio [pu/pu]";
  parameter Boolean isTapped=false "" annotation (choices(checkBox=true));
  parameter Boolean tapLV=false "" annotation (choices(checkBox=true), Dialog(enable=isTapped));

  TransformerLoss loss(
    S_n=S_n,
    v_n=vn_lv,
    vk=vk,
    vk_r=vk_r,
    i_0=i_0,
    P_Fe=P_Fe,
    isTapped=isTapped and tapLV,
    parallel=parallel,
    inputRatio=ratio) annotation (Placement(transformation(extent={{30,-10},{50,10}})));
  Node hv(final v_n=vn_hv) annotation (Placement(transformation(extent={{-60,20},{-40,40}})));
  Node lv(final v_n=vn_lv) annotation (Placement(transformation(extent={{0,20},{20,40}})));
  SimpleTransformer transformer(
    final useInputRatio=false,
    final useInputAngle=false,
    final eta=1,
    final ratio=ratio*vn_hv/vn_lv)
    annotation (Placement(transformation(extent={{-30,-10},{-10,10}})));

equation 
  s_loading = sqrt(max(epp_1.P^2 + epp_1.Q^2, epp_2.P^2 + epp_2.Q^2))/S_n/parallel;

  connect(transformer.epp_1, hv.epp)
    annotation (Line(points={{-30,0},{-50,0},{-50,30}}, color={0,0,0}));
  connect(transformer.epp_2, lv.epp)
    annotation (Line(points={{-10,0},{10,0},{10,30}}, color={0,0,0}));
  connect(loss.epp_1, lv.epp) annotation (Line(points={{30,0},{10,0},{10,30}}, color={0,0,0}));
  connect(loss.epp_2, epp_2) annotation (Line(points={{50,0},{100,0}}, color={0,0,0}));
  connect(epp_1, hv.epp) annotation (Line(points={{-100,0},{-50,0},{-50,30}}, color={0,0,0}));
end Transformer;
"""

#
# Components
#

m = Model("ElectricalGrid", "An electric grid")

add_import(m, "Modelica.Units.SI")
add_import(m, "Modelica.ComplexMath")
# add_import(m, "TransiEnt.Components.Electrical.Grid.PiModelComplex")
add_import(
    m,
    "TransiEnt.Components.Boundaries.Electrical.ComplexPower",
    ["SlackBoundary", "PVBoundary", "PQBoundary"],
)
add_import(m, "TransiEnt.Components.Electrical.PowerTransformation.TransformerPiModelComplex")
add_import(m, "TransiEnt.Consumer.Electrical.SimpleExponentialElectricConsumerComplex")

add_component(m, "TransiEnt.SimCenter", "simCenter", pos=(-80, 0), flags="inner")
add_component(m, "TransiEnt.ModelStatistics", "modelStatistics", pos=(-90, 0), flags="inner")

add_text(m, *node_model.splitlines(), indent=True)
add_text(m, *admittance_model.splitlines(), indent=True)
add_text(m, *line_model.splitlines(), indent=True)
add_text(m, *simple_trafo_model.splitlines(), indent=True)
add_text(m, *trafoloss_model.splitlines(), indent=True)
add_text(m, *trafo_model.splitlines(), indent=True)

add_comment(m, "Bus", type="///")
for _, bus in busses.iterrows():
    init = {
        "v_n": bus["vn_kv"] * u.kV,
        "v_pu_start": bus["vm_pu"],
        "delta_start": math.radians(bus["va_degree"]),
    }
    pos = mapper(bus[["x", "y"]].to_list())
    add_component(m, "Node", bus["name"], init=init, pos=pos)

add_comment(m, "", "Load", type="///")
for _, load in net.load.iterrows():
    bus = busses.loc[load["bus"]]

    init = {
        "useInputConnectorP": False,
        "P_el_set_const": load["p_mw"] * u.MW,
        "useInputConnectorQ": False,
        "Q_el_set_const": load["q_mvar"] * u.Mvar,
        "useCosPhi": False,
        "v_n": bus["vn_kv"] * u.kV,
    }
    add_component(m, "PQBoundary", load["name"], init=init)
    add_connect(m, bus["name"], "epp", load["name"], "epp")

add_comment(m, "", "Sgen", type="///")
for _, sgen in net.sgen.iterrows():
    bus = busses.loc[sgen["bus"]]

    init = {
        "useInputConnectorP": False,
        "P_el_set_const": -sgen["p_mw"] * u.MW,
        "useInputConnectorQ": False,
        "Q_el_set_const": -sgen["q_mvar"] * u.Mvar,
        "useCosPhi": False,
        "v_n": bus["vn_kv"] * u.kV,
    }
    add_component(m, "PQBoundary", sgen["name"], init=init)
    add_connect(m, bus["name"], "epp", sgen["name"], "epp")

add_comment(m, "Gen", type="///")
for _, gen in net.gen.iterrows():
    bus = busses.loc[gen["bus"]]

    init = {
        "v_gen": gen["vm_pu"] * bus["vn_kv"] * u.kV,
        "P_gen": gen["p_mw"] * u.MW,
    }
    add_component(m, "PVBoundary", gen["name"], init=init)
    add_connect(m, bus["name"], "epp", gen["name"], "epp")

add_comment(m, "Shunt", type="///")
for _, shunt in net.shunt.iterrows():
    bus = busses.loc[shunt["bus"]]

    init = {
        "v_n": shunt["vn_kv"] * u.kV,
        "Q_el_set": shunt["q_mvar"] * u.Mvar,
        "useCosPhi": False,
        "beta": 2,
    }
    add_component(m, "SimpleExponentialElectricConsumerComplex", shunt["name"], init)
    add_connect(m, bus["name"], "epp", shunt["name"], "epp")

add_comment(m, "Ext grid", type="///")
for _, ext_grid in net.ext_grid.iterrows():
    bus = busses.loc[ext_grid["bus"]]
    init = {
        "v_gen": ext_grid["vm_pu"] * bus["vn_kv"] * u.kV,
        "delta_slackgen": math.radians(ext_grid["va_degree"]),
    }
    add_component(m, "SlackBoundary", ext_grid["name"], init=init)
    add_connect(m, ext_grid["name"], "epp", bus["name"], "epp")

add_comment(m, "Line", type="///")
for _, line in net.line.iterrows():
    from_bus = busses.loc[line["from_bus"]]
    to_bus = busses.loc[line["to_bus"]]

    # """My Model
    init = {
        "length": line["length_km"] * u.km,
        "parallel": line["parallel"],
        "r": line["r_ohm_per_km"] / 1000,
        "x": line["x_ohm_per_km"] / 1000,
        "b": 2 * math.pi * net.f_hz * line["c_nf_per_km"] * 1e-9 / 1000,
        "i_n": line["max_i_ka"] * u.kA,
    }
    add_component(m, "Line", line["name"], init=init)
    add_connect(m, from_bus["name"], "epp", line["name"], "epp_1")
    add_connect(m, to_bus["name"], "epp", line["name"], "epp_2")
    # """
    """PiModelComplex
    init = {
        "ChooseVoltageLevel": 4,
        "l": line["length_km"] * u.km,
        "r_custom": line["r_ohm_per_km"] / 1000,
        "x_custom": line["x_ohm_per_km"] / 1000,
        "c_custom": line["c_nf_per_km"] / 1e9 / 1000,
        "p": line["parallel"],
    }
    add_component(m, "PiModelComplex", name, init=init)
    add_connect(m, from_bus["name"], "epp", line["name"], "epp_p")
    add_connect(m, to_bus["name"], "epp", line["name"], "epp_n")
    # """


add_comment(m, "Trafo", type="///")
for _, trafo in net.trafo.iterrows():
    hv_bus = busses.loc[trafo["hv_bus"]]
    lv_bus = busses.loc[trafo["lv_bus"]]

    init = {
        "S_n": trafo["sn_mva"] * u.MVA,
        "vn_hv": trafo["vn_hv_kv"] * u.kV,
        "vn_lv": trafo["vn_lv_kv"] * u.kV,
        "vk": trafo["vk_percent"] / 100,
        "vk_r": trafo["vkr_percent"] / 100,
        "P_Fe": trafo["pfe_kw"] * u.kW,
        "i_0": trafo["i0_percent"] / 100,
    }
    if trafo["tap_side"] != None:
        init["isTapped"] = True

        init["ratio"] = (trafo["tap_pos"] - trafo["tap_neutral"]) * trafo["tap_step_percent"] / 100
        init["ratio"] += 1
        if math.isnan(init["ratio"]):
            init["ratio"] = 1.0

        if trafo["tap_side"] == "lv":
            init["tapLV"] = True
            init["ratio"] = 1 / init["ratio"]
    add_component(m, "Transformer", trafo["name"], init=init)
    add_connect(m, trafo["name"], "epp_1", hv_bus["name"], "epp")
    add_connect(m, trafo["name"], "epp_2", lv_bus["name"], "epp")

pprint(m)
