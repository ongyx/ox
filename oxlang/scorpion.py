# coding: utf8
"""Scorpion low-level VM.
(https://github.com/louisdh/cub/blob/master/docs/Scorpion.md)

The bytecode emitted by this implementation is documented below.

All numbers are represented as big-endian.

The start of the bytecode should always be the three-byte string 'SPN'.

Scorpion is based on instructions: an opcode, which may be followed by arguments.

An instruction has a 2-byte header:

Byte 1: The opcode as an unsigned char.
Byte 2: The number of arguments to pass to the opcode as an unsigned char.

Arguments are stored in a contiguous order and have a 3-byte header:

Byte 1: The argument type as a char.
Byte 2-3: The length of the argument in bytes as a unsigned short.

The bytes after the header are interpreted according to argument type and length.
At the end of the argument, the next argument should immediately follow, unless there are no more arguments to consume.

Argument types (the char is in parentheses):

    string (s):
        A variable-length bytestring (strs must be encoded) up to 65535 bytes long ().

    integer (i):
        A 4-byte signed integer.

    float (d):
        A 4-byte floating-point number.

    bool (?):
        A 1-byte boolean.
"""

from __future__ import annotations

import enum
import struct
from dataclasses import dataclass
from typing import List, Union

MAGIC = b"SPN"
OFFSET = len(MAGIC)

INS_HEADER = struct.Struct(">2B")

ARG_TYPES = {
    "bytes": b"s",
    "int": b"i",
    # Float in python is actually a C double, so we use double here too to avoid precision errors.
    "float": b"d",
    "bool": b"?",
}

ARG_HEADER = struct.Struct(">cH")


def _as_bytecode(arg):
    fmt = ARG_TYPES[arg.__class__.__name__]

    if fmt == b"s":
        arg_len = len(arg)
        arg_data = struct.pack(f">{arg_len}s", arg)
    else:
        arg_len = struct.Struct(fmt).size
        arg_data = struct.pack(f">{fmt.decode()}", arg)

    arg_header = ARG_HEADER.pack(fmt, arg_len)

    return arg_header + arg_data


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
    args: List[Union[bytes, int, float, bool]]
    length: int = 0

    def dump(self) -> bytes:
        header = INS_HEADER.pack(self.opcode.value, len(self.args))
        args_data = b"".join(_as_bytecode(arg) for arg in self.args)

        return header + args_data

    @classmethod
    def load(cls, bytecode: bytes, offset: int) -> Instruction:
        opcode, nargs = INS_HEADER.unpack(bytecode[offset : offset + 2])

        args = []

        h_start = offset + 2
        while nargs > 0:
            h_end = h_start + 3

            arg_type, arg_len = ARG_HEADER.unpack(bytecode[h_start:h_end])

            if arg_type == b"s":
                fmt = f">{arg_len}s"
            else:
                fmt = f">{arg_type.decode()}"

            arg_data = bytecode[h_end : h_end + arg_len]
            arg = struct.unpack(fmt, arg_data)[0]

            args.append(arg)

            h_start = h_end + arg_len
            nargs -= 1

        return cls(opcode, args, h_start)
