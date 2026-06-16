# 15_optimizer.py

class BFOptimizer(BFInsnStream):
    __slots__ = ("opt_strm", "opt_queue", "opt_input_queue", "opt_queue_idx", "opt_lazy_seek_offset", "opt_lazy_seek_reference", "opt_loops", "opt_loop_summaries", "opt_loop_number", "opt_mem")
    opt_strm: BFInsnStreamStack
    opt_queue: list[BFInsn]
    opt_input_queue: list[BFInsnStream]
    opt_queue_idx: int
    opt_lazy_seek_offset: int
    opt_lazy_seek_reference: int
    opt_loops: list[int]
    opt_loop_summaries: list[BFLoopSummary]
    opt_loop_number: int
    opt_mem: BFOptimizerMemory

    def __init__(self: typing.Self, strm: BFInsnStream) -> None:
        self.opt_queue = []
        self.opt_input_queue = []
        self.opt_queue_idx = 0
        self.opt_lazy_seek_offset = 0
        self.opt_lazy_seek_reference = -1
        self.opt_loops = []
        self.opt_loop_summaries = []
        self.opt_loop_number = 0
        self.opt_mem = BFOptimizerMemory(self, None, OPTM_ZERO | OPTM_TOP)
        self.opt_strm = BFInsnStreamStack()
        opt_strm = BFInsnStreamStack()
        opt_strm.push(strm)
        self.opt_strm = opt_strm

    def lazy_seek(self: typing.Self, offset: int) -> BFInsn:
        self.opt_lazy_seek_reference = len(self.opt_queue)
        self.opt_lazy_seek_offset += offset
        return BFInsn(BF_LAZY_SEEK, offset)

    def abs_seek(self: typing.Self, offset: int) -> None:
        config: BFConfig = self.opt_strm.config()
        optmem: BFOptimizerMemory = self.opt_mem
        rel_offset: int = offset - optmem.optm_pos
        if rel_offset == 0 and config.cfg_remove_dead_code():
            return
        optmem.optm_pos = offset
        self.opt_queue.append(self.lazy_seek(rel_offset) if config.cfg_lazy_seek() else BFInsn(BF_SEEK, rel_offset))

    def commit_seek(self: typing.Self) -> None:
        if self.opt_lazy_seek_offset == 0 and self.opt_strm.config().cfg_remove_dead_code():
            self.opt_lazy_seek_reference = -1
            return
        if self.opt_lazy_seek_reference == -1:
            self.opt_queue.append(BFInsn(BF_SEEK, 0))
        else:
            self.opt_queue[self.opt_lazy_seek_reference].insn_type = BF_SEEK
            self.opt_lazy_seek_reference = -1
        self.opt_lazy_seek_offset = 0

    def push_loop(self: typing.Self) -> BFInsn:
        nr: int = self.opt_loop_number
        self.opt_loop_number += 1
        self.opt_loops.append(nr)
        return BFInsn(BF_JZ, nr)

    def pop_loop(self: typing.Self) -> BFInsn:
        nr: int = self.opt_loops.pop()
        return BFInsn(BF_JNZ, nr)

    def config(self: typing.Self) -> BFConfig:
        return self.opt_strm.config()

    def optimize(self: typing.Self) -> BFInsn:
        strm: BFInsnStreamStack = self.opt_strm
        config: BFConfig = strm.config()
        loop: BFLoopSummary
        optmem: BFOptimizerMemory
        optmem_base: int
        while True:
            insn: BFInsn = strm.next()
            if insn.insn_type == BF_ADD:
                if config.cfg_partial_eval():
                    self.opt_mem.add(insn.insn_value)
                    continue
                return insn
            elif insn.insn_type == BF_SEEK:
                if config.cfg_partial_eval():
                    self.opt_mem.seek(insn.insn_value)
                if config.cfg_lazy_seek():
                    return self.lazy_seek(insn.insn_value)
                return insn
            elif insn.insn_type == BF_JZ:
                loop = BFLoopAnalyzer(self.opt_mem, self.opt_strm).run()
                counter: int = self.opt_mem.read()
                pure: bool = (loop.loop_flags & LOOP_PURE) != 0
                insns: BFInsnList = loop.loop_insns
                if config.cfg_partial_eval():
                    if config.cfg_remove_dead_code() and counter == 0:
                        continue
                    elif loop.loop_offset == 0 and pure and len(loop.loop_clobbers) == 0: # type: ignore
                        return BFInsn(BF_SPIN_NZ if optmem.read() == -1 else BF_SPIN, 0)
                    elif counter != -1:
                        insn_list: tuple[BFInsn, ...] = insns.all()
                        if config.cfg_unroll_loops <= (len(insn_list) - 1) * counter or ((config.cfg_lazy_seek() or counter == 1) and config.cfg_unroll_loops >= 0):
                            self.opt_strm.push(BFInsnList(insn_list[:-1] * counter))
                            continue
                        insns = BFInsnList(insn_list)
                        self.opt_mem.reset()
                        if config.cfg_lazy_seek():
                            self.commit_seek()
                        self.opt_strm.push(insns)
                        self.opt_loop_summaries.append(loop)
                        return self.push_loop()
                if loop.loop_offset == 0:
                    if config.cfg_partial_eval():
                        optmem = self.opt_mem
                        optmem_base = optmem.optm_pos
                        for clobber in loop.loop_clobbers: # type: ignore
                            if clobber != 0:
                                optmem.commit_at(optmem_base + clobber)
                                optmem.discard(optmem_base + clobber)
                        self.abs_seek(optmem_base)
                else:
                    if config.cfg_partial_eval():
                        self.opt_mem.reset()
                    if config.cfg_lazy_seek():
                        self.commit_seek()
                self.opt_strm.push(insns)
                self.opt_loop_summaries.append(loop)
                return self.push_loop()
            elif insn.insn_type == BF_JNZ:
                loop = self.opt_loop_summaries.pop()
                if loop.loop_offset == 0:
                    if config.cfg_partial_eval():
                        optmem = self.opt_mem
                        optmem_base = optmem.optm_pos
                        for clobber in loop.loop_clobbers: # type: ignore
                            self.opt_mem.commit_at(optmem_base + clobber)
                            self.opt_mem.discard(optmem_base + clobber)
                        self.abs_seek(optmem_base)
                else:
                    if config.cfg_lazy_seek():
                        self.commit_seek()
                    if config.cfg_partial_eval():
                        self.opt_mem.reset()
                if config.cfg_partial_eval():
                    self.opt_mem.write(0)
                return self.pop_loop()
            elif insn.insn_type == BF_READ:
                if config.cfg_partial_eval():
                    optmem = self.opt_mem
                    optmem.discard(optmem.optm_pos)
                if config.cfg_lazy_seek():
                    self.commit_seek()
                return insn
            elif insn.insn_type == BF_WRITE:
                if config.cfg_lazy_seek():
                    self.commit_seek()
                if config.cfg_partial_eval():
                    self.opt_mem.commit()
                return insn
            else:
                return insn

    def next(self: typing.Self) -> BFInsn:
        if self.opt_queue_idx < len(self.opt_queue):
            insn: BFInsn = self.opt_queue[self.opt_queue_idx]
            self.opt_queue_idx += 1
            return insn
        self.opt_queue = []
        self.opt_queue_idx = 0
        back: BFInsn = self.optimize()
        config: BFConfig = self.opt_strm.config()
        if back.insn_type == BF_END:
            if len(self.opt_queue) == 0:
                return back
            self.opt_queue.append(back)
            self.opt_queue_idx = 1
            return self.opt_queue[0]
        if self.opt_lazy_seek_reference != -1:
            self.opt_queue.append(back)
            while self.opt_lazy_seek_reference != -1:
                self.opt_queue.append(self.optimize())
            if len(self.opt_queue) == 0:
                return back
        elif len(self.opt_queue) == 0:
            return back
        else:
            self.opt_queue.append(back)
        self.opt_queue_idx = 1
        return self.opt_queue[0]

