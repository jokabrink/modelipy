#!/usr/bin/env python3

from modelipy import Model, pprint
from modelipy.model import add_import


def test():
    solution = """model Unnamed
  import A.B.C;
  import A.B.*;
  import MyC = A.B;
  import A.B.{C, CC};
end Unnamed;
"""
    m = Model()

    add_import(m, "A.B.C")
    add_import(m, "A.B.*")
    add_import(m, "A.B", "MyC")
    add_import(m, "A.B", ["C", "CC"])

    s = pprint(m, stream=None)
    assert s == solution
