
BF_LAZY_SEEK = 7

class BFOptimizer:
    opt_input: BFCommandList
    opt_output: list[BFCommand]
    opt_loops: list[int]
    opt_mem_offset: int
    opt_prev_seek: int
    def __init__(self: typing.Self, opt_input: BFCommandList) -> None:
        self.opt_input = opt_input
        self.opt_output = []
        self.opt_loops = []
        self.opt_mem_offset = 0
        self.opt_prev_seek = -1
    def seek(self: typing.Self, offset: int) -> None:
        if not OPT_CONFIG["cfg_lazy_seek"]:
            self.opt_output.append(BFCommand(BF_SEEK, offset))
            return
        self.opt_mem_offset += offset
        self.opt_prev_seek = len(self.opt_output)
        self.opt_output.append(BFCommand(BF_LAZY_SEEK, offset))
    def seek_commit(self: typing.Self) -> None:
        if not OPT_CONFIG["cfg_lazy_seek"]:
            return
        if self.opt_mem_offset != 0:
            if self.opt_prev_seek == -1:
                self.opt_output.append(BFCommand(BF_SEEK, 0))
            else:
                self.opt_output[self.opt_prev_seek].com_type = BF_SEEK
                self.opt_prev_seek = -1
    def optimize(self: typing.Self) -> BFCommandList:
        i: int = 0
        num_commands: int = self.opt_input.size()
        while i < num_commands:
            insn: BFCommand = self.opt_input.at(i)
            if insn.com_type == BF_NOP:
                pass
            if insn.com_type == BF_SEEK:
                self.seek(insn.com_value)
            elif insn.com_type == BF_JZ:
                self.seek_commit()
                self.opt_loops.append(len(self.opt_output))
                self.opt_output.append(BFCommand(BF_JZ, 0))
            elif insn.com_type == BF_JNZ:
                self.seek_commit()
                jz: int = self.opt_loops.pop()
                jnz: int = len(self.opt_output)
                self.opt_output[jz].com_value = jnz
                self.opt_output.append(BFCommand(BF_JNZ, jz))
            elif insn.com_type == BF_READ or insn.com_type == BF_WRITE:
                self.seek_commit()
                self.opt_output.append(insn)
            else:
                self.opt_output.append(insn)
            i += 1
        return BFCommandList(self.opt_output)

