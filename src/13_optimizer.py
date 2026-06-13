# 12_optimizer.py

class BFOptimizer:
    __slots__ = ("opt_parser", "opt_queue", "opt_queue_idx", "opt_queue_offset", "opt_lazy_seek_offset", "opt_lazy_seek_reference", "opt_loops")
    opt_parser: "BFParser"
    opt_queue: list[BFInsn]
    opt_queue_offset: int
    opt_queue_idx: int
    opt_lazy_seek_offset: int
    opt_lazy_seek_reference: int
    opt_loops: list[int]
    def __init__(self: typing.Self, opt_parser: "BFParser") -> None:
        self.opt_parser = opt_parser
        self.opt_queue = []
        self.opt_queue_idx = 0
        self.opt_queue_offset = 0
        self.opt_lazy_seek_offset = 0
        self.opt_lazy_seek_reference = -1
        self.opt_loops = []
    def lazy_seek(self: typing.Self, offset: int) -> None:
        self.opt_lazy_seek_reference = len(self.opt_queue)
        self.opt_lazy_seek_offset += offset
        return BFInsn(BF_LAZY_SEEK, offset)
    def commit_seek(self: typing.Self) -> None:
        if self.opt_lazy_seek_offset == 0 and self.opt_parser.bfp_config.cfg_dead_code_removal():
            return
        if self.opt_lazy_seek_reference == -1:
            self.opt_queue.append(BFInsn(BF_SEEK, 0))
        self.opt_queue[self.opt_lazy_seek_reference].insn_type = BF_SEEK
        self.opt_lazy_seek_reference = -1
    def push_loop(self: typing.Self) -> None:
        self.opt_loops.append(len(self.opt_queue))
        return BFInsn(BF_JZ, 0)
    def pop_loop(self: typing.Self) -> BFInsn:
        offset: int = self.opt_queue_offset
        jz: int = self.opt_loops.pop()
        jnz: int = len(self.opt_queue)
        self.opt_queue[jz].insn_value = jnz + offset
        return BFInsn(BF_JNZ, jz + offset)
    def prepare(self: typing.Self) -> BFInsn:
        parser: "BFParser" = self.opt_parser
        config: BFConfig = parser.bfp_config
        insn: BFInsn = parser.raw_insn()
        if insn.insn_type == BF_END:
            return insn
        if insn.insn_type == BF_ADD:
            return insn
        if insn.insn_type == BF_SEEK:
            if config.cfg_lazy_seek():
                return self.lazy_seek(insn.insn_value)
            return insn
        if insn.insn_type == BF_JZ:
            # TODO: try and get rid of this commit_seek
            if config.cfg_lazy_seek():
                self.commit_seek()
            return self.push_loop()
        if insn.insn_type == BF_JNZ:
            # TODO: try and get rid of this commit_seek
            if config.cfg_lazy_seek():
                self.commit_seek()
            return self.pop_loop()
        if insn.insn_type == BF_READ:
            if config.cfg_lazy_seek():
                self.commit_seek()
            return insn
        if insn.insn_type == BF_WRITE:
            if config.cfg_lazy_seek():
                self.commit_seek()
            return insn
    def next(self: typing.Self) -> BFInsn:
        if self.opt_queue_idx < len(self.opt_queue):
            insn: BFInsn = self.opt_queue[self.opt_queue_idx]
            self.opt_queue_idx += 1
            return insn
        self.opt_queue_offset += len(self.opt_queue)
        self.opt_queue = []
        back: BFInsn = self.prepare()
        if self.opt_lazy_seek_reference != -1 or len(self.opt_loops) != 0:
            self.opt_queue.append(back)
            while self.opt_lazy_seek_reference != -1 or len(self.opt_loops) != 0:
                self.opt_queue.append(self.prepare())
        elif len(self.opt_queue):
            self.opt_queue_offset += 1
            return back
        else:
            self.opt_queue.append(back)
        self.opt_queue_idx = 1
        return self.opt_queue[0]

