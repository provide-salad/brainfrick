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
    itp_bf: BFCommandList
    itp_mem: BFMemory
    itp_impl: BFImpl
    def __init__(self: typing.Self, itp_bf: BFCommandList, itp_impl: BFImpl, mem_limit: int) -> None:
        self.itp_bf = itp_bf
        self.itp_mem = BFMemory(mem_limit)
        self.itp_impl = itp_impl
    def run(self: typing.Self) -> bool:
        ip: int = 0
        while ip < self.itp_bf.size():
            insn: BFCommand = self.itp_bf.at(ip)
            if insn.com_type == BF_ADD:
                self.itp_mem.memwrite((self.itp_mem.memread() + insn.com_value) & 0xFF)
            elif insn.com_type == BF_SEEK or insn.com_type == BF_LAZY_SEEK:
                if self.itp_mem.memseek(insn.com_value):
                    return True
            elif insn.com_type == BF_JZ:
                if self.itp_mem.memread() == 0:
                    ip = insn.com_value
            elif insn.com_type == BF_JNZ:
                if self.itp_mem.memread() != 0:
                    ip = insn.com_value
            elif insn.com_type == BF_READ:
                for i in range(insn.com_value - 1):
                    self.itp_impl.read()
                self.itp_mem.memwrite(self.itp_impl.read())
            elif insn.com_type == BF_WRITE:
                c: int = self.itp_mem.memread()
                for i in range(insn.com_value):
                    self.itp_impl.write(c)
            ip += 1
        return False

