
CFG_DEAD_CODE_REMOVAL: int = 1 << 0
CFG_LAZY_SEEK: int = 1 << 1
CFG_FOLD_REPETITION: int = 1 << 2

class BFConfig:
    __slots__ = ("cfg_flags",)
    cfg_flags: int
    def __init__(self,
        cfg_dead_code_removal: bool = True,
        cfg_lazy_seek: bool = True,
        cfg_fold_repetition: bool = True,
    ) -> None:
        flags: int = 0
        flags |= CFG_DEAD_CODE_REMOVAL & -cfg_dead_code_removal
        flags |= CFG_LAZY_SEEK & -cfg_lazy_seek
        flags |= CFG_FOLD_REPETITION & -cfg_fold_repetition
        self.cfg_flags = flags
    def cfg_dead_code_removal(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_DEAD_CODE_REMOVAL) != 0
    def cfg_lazy_seek(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_LAZY_SEEK) != 0
    def cfg_fold_repetition(self: typing.Self) -> bool:
        return (self.cfg_flags & CFG_FOLD_REPETITION) != 0

DEFCONFIG: BFConfig = BFConfig()

DEFCONFIFS: dict[str, BFConfig] = {
    "default" : DEFCONFIG,
    "none" : BFConfig(
        cfg_dead_code_removal=False,
        cfg_lazy_seek=False,
        cfg_fold_repetition=False,
    ),
    "all" : BFConfig(),
}

