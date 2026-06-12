# 10_parse.py

BF_NOP: int = 0
BF_ADD: int = 1
BF_SEEK: int = 2
BF_JZ: int = 3
BF_JNZ: int = 4
BF_READ: int = 5
BF_WRITE: int = 6

class BFCommand:
    __slots__ = ("com_type", "com_value")
    com_type: int
    com_value: int
    def __init__(self: typing.Self, com_type: int, com_value: int) -> None:
        self.com_type = com_type
        self.com_value = com_value

class BFCommandList:
    __slots__ = ("cls_data")
    cls_data: bytes
    def __init__(self: typing.Self, commands: list[BFCommand]) -> None:
        cls_data: bytearray = bytearray(len(commands) * 5)
        i: int
        for i in range(len(commands)):
            j: int = i * 5
            command: BFCommand = commands[i]
            com_value: int = command.com_value & 0xFFFFFFFF
            cls_data[j] = command.com_type
            cls_data[j + 1] = com_value & 0xFF
            cls_data[j + 2] = (com_value >> 8) & 0xFF
            cls_data[j + 3] = (com_value >> 16) & 0xFF
            cls_data[j + 4] = com_value >> 24
        self.cls_data = bytes(cls_data)
    def size(self: typing.Self) -> int:
        return len(self.cls_data) // 5
    def at(self: typing.Self, i: int) -> BFCommand:
        j: int = i * 5
        com_value: int = self.cls_data[j + 1] | (self.cls_data[j + 2] << 8) | (self.cls_data[j + 3] << 16) | (self.cls_data[j + 4] << 24)
        return BFCommand(self.cls_data[j], com_value if com_value < 0x80000000 else com_value - 0x100000000)

def bf_parse(s: str) -> BFCommandList | None:
    i: int = 0
    com_type: int = BF_NOP
    com_value: int = 0
    commands: list[BFCommand] = []
    loops: list[int] = []
    while i < len(s):
        c: int = ord(s[i])
        i += 1
        if c == ord("+"): # inc *p
            if com_type == BF_ADD:
                com_value = (com_value + 1) & 0xFF
                continue
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            com_type = BF_ADD
            com_value = 0x01
            continue
        if c == ord("-"): # dec *p
            if com_type == BF_ADD:
                com_value = (com_value - 1) & 0xFF
                continue
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            com_type = BF_ADD
            com_value = 0xFF
            continue
        if c == ord("<"): # dec p
            if com_type == BF_SEEK:
                com_value -= 1
                if com_value < ~0x7FFFFFFF:
                    return None
                continue
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            com_type = BF_SEEK
            com_value = -1
            continue
        if c == ord(">"): # inc p
            if com_type == BF_SEEK:
                com_value += 1
                if com_value > 0x7FFFFFFF:
                    return None
                continue
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            com_type = BF_SEEK
            com_value = 1
            continue
        if c == ord("["): # jz
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            loops.append(len(commands))
            commands.append(BFCommand(BF_JZ, 0))
            continue
        if c == ord("]"): # jnz
            if len(loops) == 0: # Unmatched `]`
                return None
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            jnz: int = loops.pop()
            jz: int = len(commands)
            commands[jnz].com_value = jz
            commands.append(BFCommand(BF_JNZ, jnz));
            continue
        if c == ord("."): # write
            if com_type == BF_WRITE:
                com_value += 1
                if com_value > 0x7FFFFFFF:
                    return None
                continue
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            com_type = BF_WRITE
            com_value = 1
            continue
        if c == ord(","): # read
            if com_type == BF_READ:
                com_value += 1
                if com_value > 0x7FFFFFFF:
                    return None
                continue
            if com_type != BF_NOP:
                if com_value != 0:
                    commands.append(BFCommand(com_type, com_value))
                com_type = BF_NOP
            com_type = BF_READ
            com_value = 1
            continue
    if com_type != BF_NOP:
        commands.append(BFCommand(com_type, com_value))
    if len(loops) != 0: # Unmatched `[`
        return None
    if len(commands) > 0x7FFFFFFF:
        return None
    return BFCommandList(commands)

