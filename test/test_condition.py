from __future__ import annotations

from modelipy.condition import For, If, When, While
from modelipy.misc import Equation, Expression, Ident, Statement

ex = Expression("EXPRESSION")
eq = Equation("LEFT", "RIGHT")
st = Statement("STATEMENT")
ident = Ident("IDENT")


def test_for_equation():
    for_eq = For(ident.In(ex)).loop(eq).loop(eq).end()


def test_for_statement():
    for_st = For(ident.In(ex)).loop(st, st).loop(st).end()


def test_if_equation():
    if_eq = If(ex).then(eq).elseif(ex).then(eq).orelse(eq).end()


def test_if_statement():
    if_st = If(ex).then(st).elseif(ex).then(st).orelse(st).end()


def test_if_expression():
    if_ex = If(ex).then(ex).orelse(ex).end()


def test_when_equation():
    when_eq = When(ex).then(eq).elsewhen(ex).then(eq).end()


def test_when_statement():
    when_st = When(ex).then(st).elsewhen(ex).then(st).end()


def test_while_statement():
    While(ex).loop(st).end()
