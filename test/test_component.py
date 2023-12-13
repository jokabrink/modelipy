#!/usr/bin/env python3

from modelipy import Component, Model, pprint
from modelipy.model import add_component


def test():
    m = Model()

    add_component(
        m,
        "Real",
        "x",
        [1, 2, 3, 4],
        init={"min": 0},
        parameter=True,
        protected=True,
        flags=Component.final | Component.inner | Component.outer | Component.replaceable,
        variability=Component.parameter,
        causality=Component.input,
        flux=Component.flow,
        subscripts=[4],
        condition=True,
        # constraint=1,
        description="",
        annotation={"test": True},
    )

    pprint(m)
