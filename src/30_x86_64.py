# define 30_x86_64.py

class BFCompilerX64:
    __slots__ = ("comp_bf","comp_asm","comp_mem_ptr")
    comp_bf: BFCommandList
    comp_asm: list[str]
    comp_mem_ptr: int
    def __init__(self: typing.Self, comp_bf: BFCommandList) -> None:
        self.comp_bf = comp_bf
        self.comp_asm = []
        self.comp_mem_ptr = 0
    def compile(self: typing.Self) -> str | None:
        ip: int = 0
        while ip < self.comp_bf.size():
            insn: BFCommand = self.comp_bf.at(ip)
            if insn.com_type == BF_ADD:
                if insn.com_value == 0x01:
                    self.comp_asm.append(f"incb {self.comp_mem_ptr}(%rdi)")
                elif insn.com_value == 0xFF:
                    self.comp_asm.append(f"decb {self.comp_mem_ptr}(%rdi)")
                else:
                    self.comp_asm.append(f"addb ${insn.com_value},{self.comp_mem_ptr}(%rdi)")
            elif insn.com_type == BF_SEEK:
                offset: int = self.comp_mem_ptr + insn.com_value
                if offset == 0:
                    pass
                elif offset == 1:
                    self.comp_asm.append(f"incq %rdi")
                elif offset == -1:
                    self.comp_asm.append(f"decq %rdi")
                else:
                    self.comp_asm.append(f"addq ${insn.com_value},%rdi")
            elif insn.com_type == BF_JZ:
                self.comp_asm.append(f".L{ip}:\ncmpb $0,{self.comp_mem_ptr}(%rdi)\nje .L{insn.com_value}")
            elif insn.com_type == BF_JNZ:
                self.comp_asm.append(f".L{ip}:\ncmpb $0,{self.comp_mem_ptr}(%rdi)\njne .L{insn.com_value}")
            elif insn.com_type == BF_READ:
                self.comp_asm.append("\n".join(f"call _read" for i in range(insn.com_value)))
            elif insn.com_type == BF_WRITE:
                self.comp_asm.append("\n".join(f"call _write" for i in range(insn.com_value)))
            elif insn.com_type == BF_LAZY_SEEK:
                self.comp_mem_ptr += insn.com_value
            ip += 1
        return "\n".join(self.comp_asm)

