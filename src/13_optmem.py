# 13_optmem.py

OPTM_KNOWN: int = 0
OPTM_UNKNOWN: int = 1
OPTM_COMMITTED: int = 2
OPTM_INHERIT: int = 3

OPTM_ZERO: int = 1 << 0
OPTM_TOP: int = 1 << 1

class BFOptimizerMemory:
    __slots__ = ("optm_optimizer", "optm_parent", "optm_az", "optm_bz", "optm_pos", "optm_offset_or_flags", "optm_reset_flag")
    optm_optimizer: "BFOptimizer"
    optm_parent: typing.Self | None
    optm_offset_or_flags: int
    optm_az: bytearray
    optm_bz: bytearray
    optm_pos: int
    optm_reset_flag: bool

    def __init__(self: typing.Self, optm_optimizer: "BFOptimizer", optm_parent: typing.Self | None, optm_offset_or_flags: int) -> None:
        self.optm_optimizer = optm_optimizer
        self.optm_parent = optm_parent
        self.optm_offset_or_flags = optm_offset_or_flags
        self.optm_az = bytearray()
        self.optm_bz = bytearray()
        self.optm_pos = 0
        self.optm_reset_flag = False

    def seek(self: typing.Self, i: int) -> bool:
        self.optm_pos += i
        return self.optm_parent is None and (self.optm_offset_or_flags & OPTM_TOP) != 0 and self.optm_pos < 0

    def read_state(self: typing.Self, i: int) -> int:
        idx: int = i if i >= 0 else ~i
        buf: bytearray = self.optm_az if i >= 0 else self.optm_bz
        parent: typing.Self | None = self.optm_parent
        offset_or_flags: int = self.optm_offset_or_flags
        if idx >= len(buf) >> 1:
            if parent is not None:
                return parent.read_state(i + offset_or_flags)
            return (OPTM_COMMITTED if offset_or_flags & OPTM_ZERO else OPTM_UNKNOWN) << 8
        state: int = buf[(idx << 1) | 1]
        if state == OPTM_INHERIT:
            if parent is not None:
                return parent.read_state(i + offset_or_flags)
            return (OPTM_COMMITTED if offset_or_flags & OPTM_ZERO else OPTM_UNKNOWN) << 8
        value: int = buf[idx << 1]
        return value | (state << 8)

    def write_state(self: typing.Self, i: int, state: int) -> None:
        idx: int = i if i >= 0 else ~i
        buf: bytearray = self.optm_az if i >= 0 else self.optm_bz
        parent: typing.Self | None = self.optm_parent
        offset_or_flags: int = self.optm_offset_or_flags
        old_state: int = ((OPTM_COMMITTED if offset_or_flags & OPTM_ZERO else OPTM_UNKNOWN) << 8) if parent is None else parent.read_state(i + offset_or_flags)
        if state == old_state or ((state >> 8) == OPTM_KNOWN and (old_state >> 8) == OPTM_COMMITTED and (state & 0xFF) == (old_state & 0xFF)):
            return
        if idx >= len(buf) >> 1:
            buf += bytes((0, OPTM_INHERIT)) * (idx - (len(buf) >> 1))
            buf += bytes((state & 0xFF, state >> 8))
        else:
            buf[idx << 1] = state & 0xFF
            buf[(idx << 1) | 1] = state >> 8

    def read(self: typing.Self) -> int:
        state: int = self.read_state(self.optm_pos)
        return -1 if (state >> 8) == OPTM_UNKNOWN else state & 0xFF

    def write(self: typing.Self, value: int) -> None:
        self.write_state(self.optm_pos, value | (OPTM_KNOWN << 8))

    def add(self: typing.Self, value: int) -> None:
        old_state: int = self.read_state(self.optm_pos)
        self.write_state(self.optm_pos, ((old_state + value) & 0xFF) | ((OPTM_UNKNOWN if (old_state >> 8) == OPTM_UNKNOWN else OPTM_KNOWN) << 8))

    def discard(self: typing.Self, i: int) -> None:
        self.write_state(i, OPTM_UNKNOWN << 8)

    def commit_at(self: typing.Self, i: int) -> bool:
        idx: int = i if i >= 0 else -i
        buf: bytearray = self.optm_az if i >= 0 else self.optm_bz
        if idx >= len(buf) >> 1:
            return False
        state_id: int = buf[(idx << 1) | 1]
        if state_id == OPTM_INHERIT:
            return False
        optimizer: BFOptimizer = self.optm_optimizer
        config: BFConfig = optimizer.opt_strm.config()
        value: int = buf[idx << 1]
        if state_id == OPTM_COMMITTED and config.cfg_remove_dead_code():
            return value == 0
        if state_id == OPTM_UNKNOWN:
            if value != 0 or not config.cfg_remove_dead_code():
                optimizer.abs_seek(i)
                optimizer.opt_queue.append(BFInsn(BF_ADD, value))
                buf[idx << 1] = 0
            return True
        else:
            optimizer.abs_seek(i)
            optimizer.opt_queue.append(BFInsn(BF_SET, value))
            buf[(idx << 1) | 1] = OPTM_COMMITTED
            return value != 0

    def commit(self: typing.Self) -> None:
        self.commit_at(self.optm_pos)

    def clear_reset(self: typing.Self) -> None:
        self.optm_reset_flag = False

    def reset(self: typing.Self) -> None:
        use_zero: bool = (self.optm_offset_or_flags & OPTM_ZERO) != 0
        optimizer: BFOptimizer = self.optm_optimizer
        restore_idx: int = self.optm_pos
        for i in range(-len(self.optm_bz), len(self.optm_az)):
            if self.commit_at(i):
                use_zero = False
        optimizer.abs_seek(restore_idx)
        self.optm_pos = 0
        self.optm_az = bytearray()
        self.optm_bz = bytearray()
        if self.optm_parent is None:
            self.optm_offset_or_flags = OPTM_ZERO & -use_zero
        self.optm_reset_flag = True

