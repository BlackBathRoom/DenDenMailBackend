from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement
    from sqlmodel import SQLModel

from sqlalchemy import false, not_, true

# Define operators for database queries
type Operator = Literal[
    # comparisons
    "eq",  # =
    "ne",  # != / <>
    "lt",  # <
    "le",  # <=
    "gt",  # >
    "ge",  # >=
    # pattern matching
    "like",
    "not_like",
    # range / membership
    "between",
    "not_between",
    "in",
    "not_in",
    # null / identity
    "is",
    "is_not",
]
type LogicalOperator = Literal["and", "or"]
type NotOperator = Literal["not"]

type DBPrimitive = str | int | float | bool | bytes | datetime | None


class FieldCondition(TypedDict):
    field: str
    operator: Operator
    value: DBPrimitive | list[DBPrimitive]


class LogicalCondition(TypedDict):
    operator: LogicalOperator
    conditions: list[FieldCondition | LogicalCondition]


class NotCondition(TypedDict):
    operator: NotOperator
    condition: FieldCondition | LogicalCondition


type Condition = FieldCondition | LogicalCondition | NotCondition


def _col(model: type[SQLModel], field: str) -> Any:  # noqa: ANN401
    return getattr(model, field)


type OperatorFn = Callable[[Any, Any], Any]

_OPS: dict[str, OperatorFn] = {
    "eq": lambda c, v: c == v,
    "ne": lambda c, v: c != v,
    "lt": lambda c, v: c < v,
    "le": lambda c, v: c <= v,
    "gt": lambda c, v: c > v,
    "ge": lambda c, v: c >= v,
    "like": lambda c, v: c.like(v),
    "not_like": lambda c, v: ~c.like(v),
    "in": lambda c, v: c.in_(v),
    "not_in": lambda c, v: ~c.in_(v),
    "between": lambda c, v: c.between(v[0], v[1]),
    "not_between": lambda c, v: ~c.between(v[0], v[1]),
    # SQLAlchemy の NULL セマンティクス
    "is": lambda c, v: c.is_(v),
    "is_not": lambda c, v: c.isnot(v),
}


def _ensure_list(value: object, expected_len: int | None = None, name: str = "value") -> list[Any]:
    if not isinstance(value, list):
        msg = f"Value for '{name}' must be a list."
        raise TypeError(msg)
    if expected_len is not None and len(value) != expected_len:
        msg = f"Value for '{name}' must be a list of {expected_len} elements."
        raise TypeError(msg)
    return value


def resolve_condition(model: type[SQLModel], condition: Condition) -> ColumnElement[bool]:
    op = condition["operator"]

    if op == "and":
        expr: ColumnElement[bool] = true()
        for cond in condition.get("conditions", []):
            expr = expr & resolve_condition(model, cond)
        return expr

    if op == "or":
        expr: ColumnElement[bool] = false()
        for cond in condition.get("conditions", []):
            expr = expr | resolve_condition(model, cond)
        return expr

    if op == "not":
        c = cast("NotCondition", condition)
        return not_(resolve_condition(model, c["condition"]))

    field = condition.get("field")
    value = condition.get("value")
    if field is None:
        msg = "Missing 'field'."
        raise ValueError(msg)

    # リスト必須の演算子を正規化
    if op in {"in", "not_in"}:
        value = _ensure_list(value, None, op)
    if op in {"between", "not_between"}:
        value = _ensure_list(value, 2, op)

    fn = _OPS.get(op)
    if fn is None:
        msg = f"Unsupported operator: {op}"
        raise ValueError(msg)
    return fn(_col(model, field), value)
