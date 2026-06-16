
CFG_REMOVE_DEAD_CODE: int = 1 << 0
CFG_FOLD_REPETITION: int = 1 << 2
CFG_LAZY_SEEK: int = 1 << 3
CFG_PARTIAL_EVAL: int = 1 << 4

class BFConfig:
    __slots__ = ("cfg_flags",)
    cfg_flags: int

    def __init__(self,
        cfg_remove_dead_code: bool = True,
        cfg_fold_repetition: bool = True,
        cfg_lazy_seek: bool = True,
        cfg_partial_eval: bool = False,
    ) -> None:
        # Each line in the form flags | FLAG & -flag
        # because it turns the boolean into a bitmask.
        # -True becomes -1 and -False becomes 0.
        # Since X & 0 is 0 and X & -1 is X, it allows
        # to add flags if the boolean is True.
        flags: int = 0
        flags |= CFG_REMOVE_DEAD_CODE & -cfg_remove_dead_code
        flags |= CFG_FOLD_REPETITION & -cfg_fold_repetition
        flags |= CFG_LAZY_SEEK & -cfg_lazy_seek
        flags |= CFG_PARTIAL_EVAL & -cfg_partial_eval
        self.cfg_flags = flags

    def cfg_remove_dead_code(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_REMOVE_DEAD_CODE) != 0

    def cfg_fold_repetition(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_FOLD_REPETITION) != 0

    def cfg_lazy_seek(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_LAZY_SEEK) != 0

    def cfg_partial_eval(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_PARTIAL_EVAL) != 0

DEFCONFIG: BFConfig = BFConfig()

DEFCONFIGS: dict[str, BFConfig] = {
    "default" : DEFCONFIG,
    "none" : BFConfig(
        cfg_remove_dead_code=False,
        cfg_lazy_seek=False,
        cfg_fold_repetition=False,
    ),
    "all" : BFConfig(
        cfg_partial_eval=True,
    ),
}

TEST_CONFIG = BFConfig(
    cfg_remove_dead_code=False,
    cfg_lazy_seek=False,
    cfg_fold_repetition=False,
    cfg_partial_eval=True,
)

def debug(*args: typing.Any) -> None:
    print(*args, file=sys.stderr)

