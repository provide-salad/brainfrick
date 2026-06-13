# 10_lexer.py

TOK_END: int = 0
TOK_ADD: int = 1
TOK_SUB: int = 2
TOK_SEEKB: int = 3
TOK_SEEKF: int = 4
TOK_JZ: int = 5
TOK_JNZ: int = 6
TOK_READ: int = 7
TOK_WRITE: int = 8

LEX_TOKENS: dict[int, int] = {
    ord("+") : TOK_ADD,
    ord("-") : TOK_SUB,
    ord("<") : TOK_SEEKB,
    ord(">") : TOK_SEEKF,
    ord("[") : TOK_JZ,
    ord("]") : TOK_JNZ,
    ord(",") : TOK_READ,
    ord(".") : TOK_WRITE,
}

class BFToken:
    __slots__ = ("tok_type", "tok_offset")
    tok_type: int
    tok_offset: int
    def __init__(self: typing.Self, tok_type: int, tok_offset: int) -> None:
        self.tok_type = tok_type
        self.tok_offset = tok_offset

class BFLexer:
    __slots__ = ("lex_source", "lex_offset")
    lex_source: bytes
    lex_offset: int
    def __init__(self: typing.Self, source: str) -> None:
        self.lex_source = bytes(source, "utf8")
        self.lex_offset = 0
    def next(self: typing.Self) -> BFToken:
        count: int = len(self.lex_source)
        i: int

        for i in range(self.lex_offset, len(self.lex_source)):
            c: int = self.lex_source[i]
            if c in LEX_TOKENS:
                self.lex_offset = i + 1
                return BFToken(LEX_TOKENS[c], i)
        return BFToken(TOK_END, 0)

