# 21_interp.py

class BFMemory:
    __slots__ = ("mem_data","mem_pos","mem_limit")
    mem_data: bytearray
    mem_pos: int
    mem_limit: int
    def __init__(self: typing.Self, mem_limit: int) -> None:
        self.mem_data = bytearray()
        self.mem_limit = mem_limit
        self.mem_pos = 0
    def memseek(self: typing.Self, i: int) -> bool:
        self.mem_pos += i
        if self.mem_pos < 0:
            return True
        if self.mem_limit and self.mem_pos >= self.mem_limit:
            return True
        return False
    def memread(self: typing.Self) -> int:
        if self.mem_pos >= len(self.mem_data):
            return 0
        return self.mem_data[self.mem_pos]
    def memwrite(self: typing.Self, value: int) -> None:
        if self.mem_pos == len(self.mem_data):
            self.mem_data.append(value)
            return
        if self.mem_pos > len(self.mem_data):
            self.mem_data += bytes(self.mem_pos - len(self.mem_data))
            self.mem_data.append(value)
            return
        self.mem_data[self.mem_pos] = value

class BFInterp:
    __slots__ = ("itp_bf","itp_mem","itp_impl")
    itp_bf: tuple[BFInsn, ...]
    itp_mem: BFMemory
    itp_impl: BFImpl
    def __init__(self: typing.Self, strm: BFInsnStream, itp_impl: BFImpl, mem_limit: int) -> None:
        insns: list[BFInsn] = []
        c: BFInsn = strm.next()
        loops: list[int] = []
        while c.insn_type != BF_END:
            if c.insn_type == BF_JZ:
                loops.append(len(insns))
            elif c.insn_type == BF_JNZ:
                jz: int = loops.pop()
                jnz: int = len(insns)
                insns[jz].insn_value = jnz
                c.insn_value = jz
            insns.append(c)
            c = strm.next()
        self.itp_bf = tuple(insns)
        self.itp_mem = BFMemory(mem_limit)
        self.itp_impl = itp_impl
    def run(self: typing.Self) -> bool:
        ip: int = 0
        while ip < len(self.itp_bf):
            insn: BFInsn = self.itp_bf[ip]
            if insn.insn_type == BF_ADD:
                self.itp_mem.memwrite((self.itp_mem.memread() + insn.insn_value) & 0xFF)
            elif insn.insn_type == BF_SEEK or insn.insn_type == BF_LAZY_SEEK:
                if self.itp_mem.memseek(insn.insn_value):
                    return True
            elif insn.insn_type == BF_JZ:
                if self.itp_mem.memread() == 0:
                    ip = insn.insn_value
            elif insn.insn_type == BF_JNZ:
                if self.itp_mem.memread() != 0:
                    ip = insn.insn_value
            elif insn.insn_type == BF_READ:
                for i in range(insn.insn_value - 1):
                    self.itp_impl.read()
                self.itp_mem.memwrite(self.itp_impl.read())
            elif insn.insn_type == BF_WRITE:
                c: int = self.itp_mem.memread()
                for i in range(insn.insn_value):
                    self.itp_impl.write(c)
            elif insn.insn_type == BF_SET:
                self.itp_mem.memwrite(insn.insn_value)
            ip += 1
        return False

