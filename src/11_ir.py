# 11_ir.py

BF_END = 0
BF_ADD = 1
BF_SEEK = 2
BF_JZ = 3
BF_JNZ = 4
BF_READ = 5
BF_WRITE = 6
BF_LAZY_SEEK = 7

class BFInsn:
    __slots__ = ("insn_type", "insn_value")
    insn_type: int
    insn_value: int
    def __init__(self: typing.Self, insn_type: int, insn_value: int) -> None:
        self.insn_type = insn_type
        self.insn_value = insn_value

