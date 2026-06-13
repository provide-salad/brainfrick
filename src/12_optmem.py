# 12_optmem.py

OPTM_KNOWN: int = 0
OPTM_UNKNOWN: int = 1
OPTM_COMMITTED: int = 2

OPTM_ZERO: int = 1 << 0

class BFOptimizerMemory:
    __slots__ = ("optm_optimizer","optm_az","optm_bz","optm_pos","optm_flags","optm_seq_id")
    optm_optimizer: "BFOptimizer"
    optm_az: bytearray
    optm_bz: bytearray
    optm_pos: int
    optm_flags: int
    optm_seq_id: int
    def __init__(self: typing.Self, optm_optimizer: "BFOptimizer") -> None:
        self.optm_optimizer = optm_optimizer
        self.optm_az = bytearray()
        self.optm_bz = bytearray()
        self.optm_pos = 0
        self.optm_flags = OPTM_ZERO
        self.optm_seq_id = 0
    def seek(self: typing.Self, i: int) -> bool:
        self.optm_pos += i
        if self.optm_seq_id == 0 and self.optm_pos < 0:
            return True
        return False
    def read(self: typing.Self) -> int:
        idx: int = self.optm_pos if self.optm_pos >= 0 else -self.optm_pos
        buf: bytearray = self.optm_az if self.optm_pos >= 0 else self.optm_bz
        if idx >= len(buf) >> 1:
            return 0 if self.optm_flags & OPTM_ZERO else -1
        value: int = buf[idx << 1]
        state: int = buf[(idx << 1) | 1]
        return -1 if state == OPTM_UNKNOWN else value
    def write(self: typing.Self, value: int) -> None:
        idx: int = self.optm_pos if self.optm_pos >= 0 else -self.optm_pos
        buf: bytearray = self.optm_az if self.optm_pos >= 0 else self.optm_bz
        if idx >= len(buf) >> 1:
            for i in range(0, idx - (len(buf) >> 1)):
                buf.append(0)
                buf.append(OPTM_COMMITTED if self.optm_flags & OPTM_ZERO else OPTM_UNKNOWN)
            buf.append(value)
            buf.append(OPTM_COMMITTED if (self.optm_flags & OPTM_ZERO) and value == 0 else OPTM_KNOWN)
            return
        old_value: int = buf[idx << 1]
        old_state: int = buf[(idx << 1) | 1]
        if value == old_value and old_state != OPTM_UNKNOWN:
            return
        buf[idx << 1] = value
        buf[(idx << 1) | 1] = OPTM_KNOWN
    def add(self: typing.Self, value: int) -> None:
        idx: int = self.optm_pos if self.optm_pos >= 0 else -self.optm_pos
        buf: bytearray = self.optm_az if self.optm_pos >= 0 else self.optm_bz
        if idx >= len(buf) >> 1:
            for i in range(0, idx - (len(buf) >> 1)):
                buf.append(0)
                buf.append(OPTM_COMMITTED if self.optm_flags & OPTM_ZERO else OPTM_UNKNOWN)
            buf.append(value)
            buf.append((OPTM_COMMITTED if value == 0 else OPTM_KNOWN) if self.optm_flags & OPTM_ZERO else OPTM_UNKNOWN)
            return
        buf[idx << 1] = (buf[idx << 1] + value) & 0xFF
        if buf[(idx << 1) | 1] == OPTM_COMMITTED:
            buf[(idx << 1) | 1] = OPTM_KNOWN
    def invalidate(self: typing.Self) -> None:
        idx: int = self.optm_pos if self.optm_pos >= 0 else -self.optm_pos
        buf: bytearray = self.optm_az if self.optm_pos >= 0 else self.optm_bz
        if idx >= len(buf) >> 1:
            for i in range(0, idx - (len(buf) >> 1)):
                buf.append(0)
                buf.append(OPTM_COMMITTED if self.optm_flags & OPTM_ZERO else OPTM_UNKNOWN)
            buf.append(0)
            buf.append(OPTM_UNKNOWN)
            return
        buf[idx << 1] = 0
        buf[(idx << 1) | 1] = OPTM_UNKNOWN
    def commit_at(self: typing.Self, i: int) -> bool:
        idx: int = i if i >= 0 else -i
        buf: bytearray = self.optm_az if i >= 0 else self.optm_bz
        if idx >= len(buf) >> 1:
            return False
        value: int = buf[idx << 1]
        state: int = buf[(idx << 1) | 1]
        optimizer: BFOptimizer = self.optm_optimizer
        if state == OPTM_KNOWN:
            optimizer.opt_queue.append(BFInsn(BF_SET, value))
            buf[(idx << 1) | 1] = OPTM_COMMITTED
        elif state == OPTM_UNKNOWN and value != 0:
            optimizer.opt_queue.append(BFInsn(BF_ADD, value))
            buf[idx << 1] = 0
        return state == OPTM_UNKNOWN or value != 0
    def commit(self: typing.Self) -> None:
        self.commit_at(self.optm_pos)
    def reset(self: typing.Self) -> None:
        use_zero: bool = (self.optm_flags & OPTM_ZERO) != 0
        for i in range((-len(self.optm_bz) or -1) + 1, len(self.optm_az)):
            if self.commit_at(i):
                use_zero = False
        self.optm_pos = 0
        self.optm_az = bytearray()
        self.optm_bz = bytearray()
        self.optm_flags = OPTM_ZERO & -use_zero
        self.optm_seq_id += 1

