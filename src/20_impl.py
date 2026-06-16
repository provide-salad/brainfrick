# 20_impl.py

class BFImpl:
    impl_read: typing.Callable[[], int] | None
    impl_write: typing.Callable[[int], None] | None

    def __init__(self: typing.Self):
        self.impl_read = None
        self.impl_write = None
    
    def readfunc(self: typing.Self, fn: typing.Callable[[], int]) -> typing.Callable[[], int]:
        self.impl_read = fn
        return fn
    
    def writefunc(self: typing.Self, fn: typing.Callable[[int], None]) -> typing.Callable[[int], None]:
        self.impl_write = fn
        return fn
    
    def read(self: typing.Self) -> int:
        if self.impl_read is None:
            return 0
        return self.impl_read()
    
    def write(self: typing.Self, x: int) -> None:
        if self.impl_write is not None:
            self.impl_write(x)

