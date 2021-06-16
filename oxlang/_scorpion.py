# coding: utf8
"""Scorpion low-level VM.
(https://github.com/louisdh/cub/blob/master/docs/Scorpion.md)
"""

from __future__ import annotations

import collections
import enum
from dataclasses import dataclass
from typing import List, Union


Primitive = Union[bytes, int, float, bool]


class Opcode(enum.Enum):
    PUSH_CONST = 0
    ADD = 1
    SUB = 2
    MUL = 3
    DIV = 4
    POW = 5
    AND = 6
    OR = 7
    NOT = 8
    EQ = 9
    NEQ = 10
    IF_TRUE = 11
    IF_FALSE = 12
    CMPLE = 13
    CMPLT = 14
    GOTO = 15
    REG_STORE = 15
    REG_UPDATE = 17
    REG_CLEAR = 18
    REG_LOAD = 19
    INVOKE_VIRT = 20
    EXIT_VIRT = 21
    POP = 22
    SKIP_PAST = 23
    STRUCT_INIT = 24
    STRUCT_SET = 25
    STRUCT_UPDATE = 26
    STRUCT_GET = 27
    VIRT_H = 28
    PVIRT_H = 29
    VIRT_E = 30
    P_VIRT_E = 31


@dataclass
class Instruction:
    opcode: Opcode
    args: List[Primitive]


class Runtime:
    def __init__(self):
        self.stack = collections.deque()

    def execute(self, ins: Instruction):
        opcode_name = ins.opcode.name
        opcode_func = getattr(self, f"ins_{opcode_name.lower()}")

        opcode_func(*ins.args)

    def ins_push_const(self, value: Primitive):
        self.stack.append(value)

    def ins_add(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 + value2)

    def ins_sub(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 - value2)

    def ins_mul(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 * value2)

    def ins_div(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 / value2)

    def ins_pow(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 ** value2)

    def ins_and(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(bool(value1 and value2))

    def ins_or(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(bool(value1 or value2))

    def ins_not(self):
        value = self.stack.pop()

        self.stack.append(bool(not value))

    def ins_eq(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 == value2)

    def ins_neq(self):
        value1 = self.stack.pop()
        value2 = self.stack.pop()

        self.stack.append(value1 != value2)
