from __future__ import annotations

from modelipy import model


def test_model():
    m = model.Model()
    assert m.ident == "Unnamed"
