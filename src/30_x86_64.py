# define 30_x86_64.py

class BFCompilerX64:
    __slots__ = ("comp_strm","comp_asm","comp_mem_ptr")
    comp_strm: BFInsnStream
    comp_asm: list[str]
    comp_mem_ptr: int

    def __init__(self: typing.Self, comp_strm: BFInsnStream) -> None:
        self.comp_strm = comp_strm
        self.comp_asm = []
        self.comp_mem_ptr = 0
    
    def compile(self: typing.Self) -> str | None:
        strm: BFInsnStream = self.comp_strm
        config: BFConfig = strm.config()
        ip: int = 0
        insn: BFInsn = strm.next()
        while insn.insn_type != BF_END:
            if insn.insn_type == BF_ADD:
                if config.cfg_remove_dead_code() or (not config.cfg_partial_eval() and not config.cfg_fold_repetition()):
                    if insn.insn_value == 0x01:
                        self.comp_asm.append(f"incb {self.comp_mem_ptr}(%rdi)")
                    elif insn.insn_value == 0xFF:
                        self.comp_asm.append(f"decb {self.comp_mem_ptr}(%rdi)")
                    else:
                        self.comp_asm.append(f"addb ${insn.insn_value},{self.comp_mem_ptr}(%rdi)")
                else:
                    self.comp_asm.append(f"addb ${insn.insn_value},{self.comp_mem_ptr}(%rdi)")
            elif insn.insn_type == BF_SEEK:
                offset: int = self.comp_mem_ptr + insn.insn_value
                self.comp_mem_ptr = 0
                if config.cfg_remove_dead_code() or (not config.cfg_lazy_seek() and not config.cfg_fold_repetition()):
                    if offset == 0:
                        pass
                    elif offset == 1:
                        self.comp_asm.append(f"incq %rdi")
                    elif offset == -1:
                        self.comp_asm.append(f"decq %rdi")
                    else:
                        self.comp_asm.append(f"addq ${offset},%rdi")
                else:
                    self.comp_asm.append(f"addq ${offset},%rdi")
            elif insn.insn_type == BF_JZ:
                self.comp_asm.append(f"cmpb $0,{self.comp_mem_ptr}(%rdi)\nje .LY{insn.insn_value}\n.LZ{insn.insn_value}:")
            elif insn.insn_type == BF_JNZ:
                self.comp_asm.append(f"cmpb $0,{self.comp_mem_ptr}(%rdi)\njne .LZ{insn.insn_value}\n.LY{insn.insn_value}:")
            elif insn.insn_type == BF_READ:
                self.comp_asm.append("\n".join(f"call _read" for i in range(insn.insn_value)))
            elif insn.insn_type == BF_WRITE:
                self.comp_asm.append("\n".join(f"call _write" for i in range(insn.insn_value)))
            elif insn.insn_type == BF_SET:
                self.comp_asm.append(f"movb ${insn.insn_value},{self.comp_mem_ptr}(%rdi)")
            elif insn.insn_type == BF_LAZY_SEEK:
                self.comp_mem_ptr += insn.insn_value
            elif insn.insn_type == BF_SPIN:
                self.comp_asm.append(f"1:rep nop\njmp 1b")
            elif insn.insn_type == BF_SPIN_NZ:
                self.comp_asm.append(f"cmpb $0,{self.comp_mem_ptr}(%rdi)\njz 2f\n1:rep nop\njmp 1b\n2:")
            ip += 1
            insn = strm.next()
        return "\n".join(self.comp_asm) + "\nret"

