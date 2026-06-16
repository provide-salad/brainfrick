# 11_insn.py

BF_END = 0
BF_ADD = 1
BF_SEEK = 2
BF_JZ = 3
BF_JNZ = 4
BF_READ = 5
BF_WRITE = 6
BF_SET = 7
BF_LAZY_SEEK = 8

BF_TYPES: tuple[str, ...] = (
    "BF_END",
    "BF_ADD",
    "BF_SEEK",
    "BF_JZ",
    "BF_JNZ",
    "BF_READ",
    "BF_WRITE",
    "BF_SET",
    "BF_LAZY_SEEK",
)

class BFInsn:
    __slots__ = ("insn_type", "insn_value")
    insn_type: int
    insn_value: int

    def __init__(self: typing.Self, insn_type: int, insn_value: int) -> None:
        self.insn_type = insn_type
        self.insn_value = insn_value

    def __repr__(self: typing.Self) -> str:
        return f"{BF_TYPES[self.insn_type]}({self.insn_value})"

class BFInsnStream:
    __slots__ = () # interface

    @abc.abstractmethod
    def next(self: typing.Self) -> BFInsn:
        pass

    @abc.abstractmethod
    def config(self: typing.Self) -> BFConfig:
        pass

class BFInsnList(BFInsnStream):
    __slots__ = ("ils_insns", "ils_idx")
    ils_insns: tuple[BFInsn, ...]
    ils_idx: int
    
    def __init__(self: typing.Self, insns: list[BFInsn]) -> None:
        self.ils_insns = tuple(insns)
        self.ils_idx = 0

    def next(self: typing.Self) -> BFInsn:
        insns: tuple[BFInsn, ...] = self.ils_insns
        idx: int = self.ils_idx
        if idx >= len(insns):
            return BFInsn(BF_END, 0)
        insn: BFInsn = insns[idx]
        self.ils_idx += 1
        return insn

    def all(self: typing.Self) -> tuple[BFInsn, ...]:
        insns: tuple[BFInsn, ...] = self.ils_insns
        idx: int = self.ils_idx
        if idx != 0:
            insns = insns[idx:]
        self.ils_insns = ()
        return insns

    def config(self: typing.Self) -> BFConfig:
        raise NotImplementedError()

class BFInsnStreamStack(BFInsnStream):
    __slots__ = ("istk_strms",)
    istk_strms: list[BFInsnStream]

    def __init__(self: typing.Self) -> None:
        self.istk_strms = []

    def next(self: typing.Self) -> BFInsn:
        strms: list[BFInsnStream] = self.istk_strms
        while True:
            strm: BFInsnStream = strms[-1]
            insn: BFInsn = strm.next()
            if insn.insn_type != BF_END or insn.insn_value != 0 or len(strms) <= 1:
                return insn
            strms.pop()

    def push(self: typing.Self, strm: BFInsnStream) -> None:
        self.istk_strms.append(strm)

    def config(self: typing.Self) -> BFConfig:
        return self.istk_strms[0].config()

