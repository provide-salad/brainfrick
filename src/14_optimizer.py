# 13_optimizer.py

class BFOptimizer(BFInsnStream):
    __slots__ = ("opt_strm", "opt_queue", "opt_queue_idx", "opt_lazy_seek_offset", "opt_lazy_seek_reference", "opt_loops", "opt_loop_number", "opt_mem")
    opt_strm: BFInsnStream
    opt_queue: list[BFInsn]
    opt_queue_idx: int
    opt_lazy_seek_offset: int
    opt_lazy_seek_reference: int
    opt_loops: list[int]
    opt_loop_number: int
    opt_mem: BFOptimizerMemory

    def __init__(self: typing.Self, opt_strm: BFInsnStream) -> None:
        self.opt_strm = opt_strm
        self.opt_queue = []
        self.opt_queue_idx = 0
        self.opt_lazy_seek_offset = 0
        self.opt_lazy_seek_reference = -1
        self.opt_loops = []
        self.opt_loop_number = 0
        self.opt_mem = BFOptimizerMemory(self)

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

    def prepare(self: typing.Self) -> BFInsn:
        strm: BFInsnStream = self.opt_strm
        config: BFConfig = strm.config()
        while True:
            insn: BFInsn = strm.next()
            if insn.insn_type == BF_END:
                return insn
            if insn.insn_type == BF_ADD:
                if config.cfg_partial_eval() and len(self.opt_loops) == 0:
                    self.opt_mem.add(insn.insn_value)
                    continue
                return insn
            if insn.insn_type == BF_SEEK:
                if config.cfg_partial_eval() and len(self.opt_loops) == 0:
                    self.opt_mem.seek(insn.insn_value)
                if config.cfg_lazy_seek():
                    self.lazy_seek(insn.insn_value)
                return insn
            if insn.insn_type == BF_JZ:
                # TODO: try and get rid of this commit_seek and opt_mem.reset
                if config.cfg_partial_eval() and len(self.opt_loops) == 0:
                    self.opt_mem.reset()
                if config.cfg_lazy_seek():
                    self.commit_seek()
                return self.push_loop()
            if insn.insn_type == BF_JNZ:
                # TODO: try and get rid of this commit_seek and opt_mem.reset
                if config.cfg_lazy_seek():
                    self.commit_seek()
                if config.cfg_partial_eval() and len(self.opt_loops) == 0:
                    self.opt_mem.reset()
                    self.opt_mem.write(0)
                return self.pop_loop()
            if insn.insn_type == BF_READ:
                if config.cfg_partial_eval() and len(self.opt_loops) == 0:
                    self.opt_mem.invalidate()
                if config.cfg_lazy_seek():
                    self.commit_seek()
                return insn
            if insn.insn_type == BF_WRITE:
                if config.cfg_lazy_seek():
                    self.commit_seek()
                if config.cfg_partial_eval() and len(self.opt_loops) == 0:
                    self.opt_mem.commit()
                return insn

    def next(self: typing.Self) -> BFInsn:
        if self.opt_queue_idx < len(self.opt_queue):
            insn: BFInsn = self.opt_queue[self.opt_queue_idx]
            self.opt_queue_idx += 1
            return insn
        self.opt_queue = []
        back: BFInsn = self.prepare()
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
                self.opt_queue.append(self.prepare())
            if len(self.opt_queue) == 0:
                return back
        elif len(self.opt_queue) == 0:
            return back
        else:
            self.opt_queue.append(back)
        self.opt_queue_idx = 1
        return self.opt_queue[0]

