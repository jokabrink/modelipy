#!/usr/bin/env python3

import modelipy.units as u
import pandapipes as pp  # type: ignore
import pandapipes.networks  # type: ignore
from modelipy import Component, Model, add_component, add_connect, add_import, pprint

net = pp.networks.simple_gas_networks.gas_one_pipe1()

pp.pipeflow(net)

junctions = net.junction.join(net.junction_geodata).join(net.res_junction)
pipes = net.pipe.join(net.res_pipe)
ext_grids = net.ext_grid.join(net.res_ext_grid)
sinks = net.sink.join(net.res_sink, rsuffix="_")
fluid = net.fluid

m = Model("GasGrid")
add_import(m, "TransiEnt.Components.Boundaries.Gas.BoundaryRealGas_pTx", "ExtGrid")
add_import(
    m,
    "TransiEnt.Components.Gas.VolumesValvesFittings.Pipes.PipeFlow_L4_Simple_isoth",
    "Pipe",
)
add_import(m, "TransiEnt.Consumer.Gas.GasConsumerPipe_mFlow", "Sink")
add_import(
    m,
    "TransiEnt.Components.Gas.VolumesValvesFittings.Fittings.RealGasJunction_L2_nPorts_isoth",
    "Junction",
)

add_component(m, "TransiEnt.SimCenter", "simCenter", flags=Component.inner)
add_component(m, "TransiEnt.ModelStatistics", "modelStatistics", flags=Component.inner)

for idx, junction in junctions.iterrows():
    init = {
        "p_start": junction["p_bar"],
        # "h_start": 1,
        # "xi_start": 1,
        "T_start": junction["t_k"],
    }
    pos = (0, 20)  # junction[["x", "y"]].to_list()
    add_component(m, "Junction", junction["name"], init=init, pos=pos)


for idx, ext_grid in ext_grids.iterrows():
    junction = junctions.loc[ext_grid["junction"]]
    init = {
        "p_const": ext_grid["p_bar"],
        "T_const": ext_grid["t_k"],
        # "m": {"start": ext_grid["mdot_kg_per_s"]},
    }
    pos = (0, 20)
    add_component(m, "ExtGrid", ext_grid["name"])
    add_connect(m, ext_grid["name"], "gasPort", junction["name"], "gasPort[1]")


for idx, pipe in pipes.iterrows():
    from_junction = junctions.loc[pipe["from_junction"]]
    to_junction = junctions.loc[pipe["to_junction"]]
    init = {
        "length": pipe["length_km"] * u.km,
        "diameter_i": pipe["diameter_m"],
        "z_in": 0,
        "z_out": 0,
        "p_nom": 1,
    }
    pos = (0, 10)
    add_component(m, "Pipe", pipe["name"], init=init, pos=pos)
    add_connect(m, pipe["name"], "gasPortIn", from_junction["name"], "gasPort[1]")
    add_connect(m, pipe["name"], "gasPortOut", to_junction["name"], "gasPort[1]")


for idx, sink in sinks.iterrows():
    junction = junctions.loc[sink["junction"]]
    init = {
        "variable_m_flow": False,
        "m_flow_const": sink["mdot_kg_per_s"],
    }
    pos = (0, 30)
    add_component(m, "Sink", sink["name"], init=init, pos=pos)
    add_connect(m, sink["name"], "fluidPortIn", junction["name"], "gasPort[1]")


pprint(m)
