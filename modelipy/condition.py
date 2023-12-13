# Copyright (c) 2023, Jonas Kock am Brink

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List  # NOTE: This can be removed if py37, and py38 support cast(list[...], ...)
from typing import Optional, Union, cast, overload

from .misc import Equation, Expression, ForIndex, Statement

"""
- While()
- For()
- If()
- When()
"""

# while


@dataclass
class WhileEquation:
    test: Expression
    body: list[Equation]


@dataclass
class WhileStatement:
    test: Expression
    body: list[Statement]

    def end(self) -> WhileStatement:
        return self


class While:
    def __init__(self, test: Expression):
        self.test = test

    @overload
    def loop(self, *body: Equation) -> WhileEquation:
        ...

    @overload
    def loop(self, *body: Statement) -> WhileStatement:
        ...

    def loop(self, *body: Union[Equation, Statement]) -> Union[WhileEquation, WhileStatement]:
        assert len(body) > 0, "For loop must have at least one body element"
        if isinstance(body[0], Equation):
            assert all(isinstance(b, Equation) for b in body)
            eq_lst = cast(List[Equation], list(body))
            return WhileEquation(test=self.test, body=eq_lst)
        else:
            assert all(isinstance(b, Statement) for b in body)
            stmt_lst = cast(List[Statement], list(body))
            return WhileStatement(test=self.test, body=stmt_lst)


# for


@dataclass
class ForEquation:
    indices: list[ForIndex]
    body: list[Equation]

    def loop(self, *body: Equation) -> ForEquation:
        self.body.extend(body)
        return self

    def end(self) -> ForEquation:
        return self


@dataclass
class ForStatement:
    indices: list[ForIndex]
    body: list[Statement]

    def loop(self, *body: Statement) -> ForStatement:
        self.body.extend(body)
        return self

    def end(self) -> ForStatement:
        return self


class For:
    def __init__(self, *index: ForIndex):
        self.indices = list(index)

    @overload
    def loop(self, *body: Equation) -> ForEquation:
        ...

    @overload
    def loop(self, *body: Statement) -> ForStatement:
        ...

    def loop(self, *body: Union[Equation, Statement]) -> Union[ForEquation, ForStatement]:
        assert len(body) > 0, "For loop must have at least one body element"
        if isinstance(body[0], Equation):
            assert all(isinstance(b, Equation) for b in body)
            eq_lst = cast(List[Equation], list(body))
            return ForEquation(indices=self.indices, body=eq_lst)
        else:
            assert all(isinstance(b, Statement) for b in body)
            stmt_lst = cast(List[Statement], list(body))
            return ForStatement(indices=self.indices, body=stmt_lst)


# if


@dataclass
class IfEquation:
    test: Expression
    body: list[Equation] = field(default_factory=list)
    elseif: list[tuple[Expression, list[Equation]]] = field(default_factory=list)
    orelse: Optional[list[Equation]] = None


@dataclass
class IfEquationOrelse:
    test: Expression
    body: list[Equation]
    elseif: list[tuple[Expression, list[Equation]]]
    _orelse: list[Equation]

    def orelse(self, *body: Equation) -> IfEquationOrelse:
        self._orelse.extend(body)
        return self

    def then(self, *body: Equation) -> IfEquationOrelse:
        self._orelse.extend(body)
        return self

    def end(self) -> IfEquation:
        return IfEquation(test=self.test, body=self.body, elseif=self.elseif, orelse=self._orelse)


@dataclass
class IfEquationElseif:
    test: Expression
    body: list[Equation]
    _elseif: list[tuple[Expression, list[Equation]]]

    def elseif(self, test: Expression) -> IfEquationElseif:
        self._elseif.append((test, []))
        return self

    def then(self, *body: Equation) -> IfEquationElseif:
        self._elseif[-1][1].extend(body)
        return self

    def orelse(self, *body: Equation) -> IfEquationOrelse:
        return IfEquationOrelse(
            test=self.test, body=self.body, elseif=self._elseif, _orelse=list(body)
        )

    def end(self) -> IfEquation:
        return IfEquation(test=self.test, body=self.body, elseif=self._elseif, orelse=None)


@dataclass
class IfEquationBody:
    test: Expression
    body: list[Equation]

    def then(self, *body: Equation) -> IfEquationBody:
        self.body.extend(body)
        return self

    def elseif(self, test: Expression) -> IfEquationElseif:
        return IfEquationElseif(test=self.test, body=self.body, _elseif=[(test, [])])

    def orelse(self, *eq: Equation) -> IfEquationOrelse:
        raise NotImplementedError()

    def end(self) -> IfEquation:
        return IfEquation(test=self.test, body=self.body, elseif=[], orelse=None)


@dataclass
class IfStatement:
    test: Expression
    body: list[Statement]
    elseif: list[tuple[Expression, list[Statement]]]
    orelse: Optional[list[Statement]]


@dataclass
class IfStatementOrelse:
    test: Expression
    body: list[Statement]
    elseif: list[tuple[Expression, list[Statement]]]
    _orelse: list[Statement]

    def orelse(self, *body: Statement) -> IfStatementOrelse:
        self._orelse.extend(body)
        return self

    def then(self, *body: Statement) -> IfStatementOrelse:
        self._orelse.extend(body)
        return self

    def end(self) -> IfStatement:
        return IfStatement(test=self.test, body=self.body, elseif=self.elseif, orelse=self._orelse)


@dataclass
class IfStatementElseif:
    test: Expression
    body: list[Statement]
    _elseif: list[tuple[Expression, list[Statement]]]

    def elseif(self, test: Expression) -> IfStatementElseif:
        self._elseif.append((test, []))
        return self

    def then(self, *body: Statement) -> IfStatementElseif:
        self._elseif[-1][1].extend(body)
        return self

    def orelse(self, *body: Statement) -> IfStatementOrelse:
        return IfStatementOrelse(
            test=self.test, body=self.body, elseif=self._elseif, _orelse=list(body)
        )

    def end(self) -> IfStatement:
        return IfStatement(test=self.test, body=self.body, elseif=self._elseif, orelse=None)


@dataclass
class IfStatementBody:
    test: Expression
    body: list[Statement]

    def then(self, *body: Statement) -> IfStatementBody:
        self.body.extend(body)
        return self

    def elseif(self, test: Expression) -> IfStatementElseif:
        return IfStatementElseif(test=self.test, body=self.body, _elseif=[(test, [])])

    def orelse(self, *eq: Statement) -> IfStatementOrelse:
        raise NotImplementedError()

    def end(self) -> IfStatement:
        return IfStatement(test=self.test, body=self.body, elseif=[], orelse=None)


@dataclass
class IfExpression:
    test: Expression
    body: Expression
    elseif: list[tuple[Expression, Expression]]
    orelse: Expression

    def end(self) -> IfExpression:
        return self


@dataclass
class IfExpressionElseif:
    if_expression_body: IfExpressionBody
    elseif_test: Expression

    def then(self, body: Expression) -> IfExpressionBody:
        self.if_expression_body._elseif.append((self.elseif_test, body))
        return self.if_expression_body


@dataclass
class IfExpressionBody:
    test: Expression
    body: Expression
    _elseif: list[tuple[Expression, Expression]]

    def elseif(self, test: Expression) -> IfExpressionElseif:
        return IfExpressionElseif(if_expression_body=self, elseif_test=test)

    def orelse(self, body: Expression) -> IfExpression:
        return IfExpression(test=self.test, body=self.body, elseif=[], orelse=body)


class If:
    def __init__(self, test: Expression):
        self.test = test

    @overload
    def then(self, *body: Equation) -> IfEquationBody:
        ...

    @overload
    def then(self, *body: Statement) -> IfStatementBody:
        ...

    @overload
    def then(self, *body: Expression) -> IfExpressionBody:
        ...

    def then(
        self, *body: Union[Equation, Statement, Expression]
    ) -> Union[IfEquationBody, IfStatementBody, IfExpressionBody]:
        assert (
            len(body) != 0
        ), "When using 'If' the body is not allowed to be zero in order to find the correct type"
        if isinstance(body[0], Equation):
            assert all(isinstance(b, Equation) for b in body)
            eq_lst = cast(List[Equation], list(body))
            return IfEquationBody(test=self.test, body=eq_lst)
        elif isinstance(body[0], Statement):
            assert all(isinstance(b, Statement) for b in body)
            stmt_lst = cast(List[Statement], list(body))
            return IfStatementBody(self.test, body=stmt_lst)
        else:
            assert isinstance(body[0], Expression)
            assert len(body) == 1, "If expression can only have one expression insie the body"
            return IfExpressionBody(test=self.test, body=body[0], _elseif=[])

    def end(self) -> IfEquation:
        return IfEquation(test=self.test, body=[], elseif=[], orelse=None)


# when


@dataclass
class WhenEquation:
    test: Expression
    body: list[Equation]
    elsewhen: list[tuple[Expression, list[Equation]]]


@dataclass
class WhenEquationElsewhen:
    test: Expression
    body: list[Equation]
    _elsewhen: list[tuple[Expression, list[Equation]]]

    def elsewhen(self, test: Expression) -> WhenEquationElsewhen:
        self._elsewhen.append((test, []))
        return self

    def then(self, *body: Equation) -> WhenEquationElsewhen:
        self._elsewhen[-1][1].extend(body)
        return self

    def end(self) -> WhenEquation:
        return WhenEquation(test=self.test, body=self.body, elsewhen=self._elsewhen)


@dataclass
class WhenEquationBody:
    test: Expression
    body: list[Equation]

    def then(self, *body: Equation) -> WhenEquationBody:
        self.body.extend(body)
        return self

    def elsewhen(self, test: Expression) -> WhenEquationElsewhen:
        return WhenEquationElsewhen(test=self.test, body=self.body, _elsewhen=[(test, [])])

    def end(self) -> WhenEquation:
        return WhenEquation(test=self.test, body=self.body, elsewhen=[])


@dataclass
class WhenStatement:
    test: Expression
    body: list[Statement]
    elsewhen: list[tuple[Expression, list[Statement]]]


@dataclass
class WhenStatementElsewhen:
    test: Expression
    body: list[Statement]
    _elsewhen: list[tuple[Expression, list[Statement]]]

    def elsewhen(self, test: Expression) -> WhenStatementElsewhen:
        self._elsewhen.append((test, []))
        return self

    def then(self, *body: Statement) -> WhenStatementElsewhen:
        self._elsewhen[-1][1].extend(body)
        return self

    def end(self) -> WhenStatement:
        return WhenStatement(test=self.test, body=self.body, elsewhen=self._elsewhen)


@dataclass
class WhenStatementBody:
    test: Expression
    body: list[Statement]

    def then(self, *body: Statement) -> WhenStatementBody:
        self.body.extend(body)
        return self

    def elsewhen(self, test: Expression) -> WhenStatementElsewhen:
        return WhenStatementElsewhen(test=self.test, body=self.body, _elsewhen=[(test, [])])

    def end(self) -> WhenStatement:
        return WhenStatement(test=self.test, body=self.body, elsewhen=[])


class When:
    def __init__(self, test: Expression):
        self.test = test

    @overload
    def then(self, *body: Equation) -> WhenEquationBody:
        ...

    @overload
    def then(self, *body: Statement) -> WhenStatementBody:
        ...

    def then(self, *body: Union[Equation, Statement]) -> Union[WhenEquationBody, WhenStatementBody]:
        assert (
            len(body) != 0
        ), "When using 'When' the body is not allowed to be zero in order to find the correct type"
        if isinstance(body[0], Equation):
            assert all(isinstance(b, Equation) for b in body)
            eq_lst = cast(List[Equation], list(body))
            return WhenEquationBody(test=self.test, body=eq_lst)
        else:
            assert all(isinstance(b, Statement) for b in body)
            stmt_lst = cast(List[Statement], list(body))
            return WhenStatementBody(self.test, body=stmt_lst)
            raise NotImplementedError()

    def end(self) -> WhenEquation:
        return WhenEquation(test=self.test, body=[], elsewhen=[])
