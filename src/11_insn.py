
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

