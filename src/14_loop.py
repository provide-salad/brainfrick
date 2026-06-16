# 14_loop.py

LOOP_PURE: int = 1 << 0

class BFLoopSummary:
    __slots__ = ("loop_flags", "loop_offset", "loop_clobbers", "loop_insns")
    loop_flags: int
    loop_offset: int | None
    loop_clobbers: tuple[int, ...] | None
    loop_insns: BFInsnList
    
    def __init__(self: typing.Self, loop_flags: int, loop_offset: int | None, clobbers: set[int] | None, insns: list[BFInsn]) -> None:
        self.loop_flags = loop_flags
        self.loop_offset = loop_offset
        self.loop_clobbers = None if clobbers is None else tuple(clobbers)
        self.loop_insns = BFInsnList(insns)

class BFLoopAnalyzer:
    __slots__ = ("lol_mem", "lol_strm")
    lol_mem: BFOptimizerMemory
    lol_strm: BFInsnStream

    def __init__(self: typing.Self, lol_mem: BFOptimizerMemory, lol_strm: BFInsnStream) -> None:
        self.lol_mem = lol_mem
        self.lol_strm = lol_strm

    def run(self: typing.Self) -> BFLoopSummary:
        strm: BFInsnStream = self.lol_strm
        offset: int = 0
        pure: bool = True
        clobbers: set[int] = set()
        out: list[BFInsn] = []
        clobber: int
        insn: BFInsn
        while True:
            insn = strm.next()
            if insn.insn_type != BF_END:
                debug("LOOP", insn)
            out.append(insn)
            if insn.insn_type == BF_JNZ:
                return BFLoopSummary(LOOP_PURE & -pure, offset, clobbers, out)
            elif insn.insn_type == BF_ADD or insn.insn_type == BF_SET:
                clobbers.add(offset)
            elif insn.insn_type == BF_SEEK or insn.insn_type == BF_LAZY_SEEK:
                offset += insn.insn_value
            elif insn.insn_type == BF_JZ:
                sub: BFLoopSummary = BFLoopAnalyzer(self.lol_mem, strm).run()
                out += sub.loop_insns.all()
                pure &= (sub.loop_flags & LOOP_PURE) != 0
                for clobber in sub.loop_clobbers: # type: ignore
                    clobbers.add(clobber + offset)
                if sub.loop_offset != 0:
                    break
            elif insn.insn_type == BF_READ:
                pure = False
                clobbers.add(offset)
            elif insn.insn_type == BF_WRITE:
                pure = False
        # if control reaches here we have no idea where we are, just locate the end of the loop
        depth: int = 0
        while True:
            insn = strm.next()
            out.append(insn)
            if insn.insn_type != BF_END:
                debug("LOOP2", insn)
            if insn.insn_type == BF_JZ:
                depth += 1
            elif insn.insn_type == BF_JNZ:
                if depth == 0:
                    return BFLoopSummary((LOOP_PURE & -pure), None, None, out)
                depth -= 1
            elif insn.insn_type == BF_READ or insn.insn_type == BF_WRITE:
                pure = False

