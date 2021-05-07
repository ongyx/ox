# coding: utf8

from oxlang.scorpion import Opcode, Instruction


def test_bytecode():
    ins = Instruction(Opcode.PUSH_CONST, [b"lol", 256, 3.14, True])
