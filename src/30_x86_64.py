# define 30_x86_64.py

class BFCompilerX64:
    __slots__ = ("itp_bf","itp_asm")
    itp_bf: BFCommandList
    itp_asm: list[str]
    def __init__(self: typing.Self, itp_bf: BFCommandList) -> None:
        self.itp_bf = itp_bf
        self.itp_asm = []
    def compile(self: typing.Self) -> str | None:
        ip: int = 0
        while ip < self.itp_bf.size():
            insn: BFCommand = self.itp_bf.at(ip)
            if insn.com_type == BF_ADD:
                if insn.com_value == 0x01:
                    self.itp_asm.append(f"incb (%rdi)")
                elif insn.com_value == 0xFF:
                    self.itp_asm.append(f"decb (%rdi)")
                else:
                    self.itp_asm.append(f"addb ${insn.com_value},(%rdi)")
            elif insn.com_type == BF_SEEK:
                if insn.com_value == 1:
                    self.itp_asm.append(f"incq %rdi")
                elif insn.com_value == -1:
                    self.itp_asm.append(f"decq %rdi")
                else:
                    self.itp_asm.append(f"addq ${insn.com_value},%rdi")
            elif insn.com_type == BF_JZ:
                self.itp_asm.append(f".L{ip}:\ncmpb $0,(%rdi)\nje .L{insn.com_value}")
            elif insn.com_type == BF_JNZ:
                self.itp_asm.append(f".L{ip}:\ncmpb $0,(%rdi)\njne .L{insn.com_value}")
            elif insn.com_type == BF_READ:
                self.itp_asm.append("\n".join(f"call _read" for i in range(insn.com_value)))
            elif insn.com_type == BF_WRITE:
                self.itp_asm.append("\n".join(f"call _write" for i in range(insn.com_value)))
            ip += 1
        return "\n".join(self.itp_asm)

