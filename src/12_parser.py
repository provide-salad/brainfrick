# 13_parser.py

class BFParser:
    __slots__ = ("bfp_lexer", "bfp_config", "bfp_cur_insn", "bfp_loop_depth")
    bfp_lexer: BFLexer
    bfp_config: BFConfig
    bfp_cur_insn: BFInsn
    bfp_loop_depth: int
    def __init__(self: typing.Self, bfp_lexer: BFLexer, bfp_config: BFConfig) -> None:
        self.bfp_lexer = bfp_lexer
        self.bfp_config = bfp_config
        self.bfp_cur_insn = bfp_lexer.next()
        self.bfp_loop_depth = 0
    def raw_insn(self: typing.Self) -> BFInsn:
        lexer: BFLexer = self.bfp_lexer
        config: BFConfig = self.bfp_config
        c: BFInsn = self.bfp_cur_insn

        while c.tok_type != TOK_END:
            if c.tok_type == TOK_ADD or c.tok_type == TOK_SUB:
                change: int = (-(c.tok_type - TOK_ADD) << 1) + 1
                if not config.cfg_fold_repetition():
                    self.bfp_cur_insn = lexer.next()
                    return BFInsn(BF_ADD, change & 0xFF)
                c = lexer.next()
                while c.tok_type == TOK_ADD or c.tok_type == TOK_SUB:
                    change += (-(c.tok_type - TOK_ADD) << 1) + 1
                    c = lexer.next()
                self.bfp_cur_insn = c
                change &= 0xFF
                if change == 0 and config.cfg_dead_code_removal():
                    continue
                return BFInsn(BF_ADD, change)
            if c.tok_type == TOK_SEEKB or c.tok_type == TOK_SEEKF:
                change: int = ((c.tok_type - TOK_SEEKB) << 1) - 1
                if not config.cfg_fold_repetition():
                    self.bfp_cur_insn = lexer.next()
                    return BFInsn(BF_SEEK, change)
                c = lexer.next()
                while c.tok_type == TOK_SEEKB or c.tok_type == TOK_SEEKF:
                    change += ((c.tok_type - TOK_SEEKB) << 1) - 1
                    c = lexer.next()
                self.bfp_cur_insn = c
                if change == 0 and config.cfg_dead_code_removal():
                    continue
                return BFInsn(BF_SEEK, change)
            if c.tok_type == TOK_JZ:
                self.bfp_loop_depth += 1
                self.bfp_cur_insn = lexer.next()
                return BFInsn(BF_JZ, 0)
            if c.tok_type == TOK_JNZ:
                if self.bfp_loop_depth == 0:
                    print(f"Syntax error: unmatched `]` at offset {c.tok_offset}", file=sys.stderr)
                    return BFInsn(BF_END, 1)
                self.bfp_cur_insn = lexer.next()
                self.bfp_loop_depth -= 1
                return BFInsn(BF_JNZ, 0)
            if c.tok_type == TOK_READ:
                if not config.cfg_fold_repetition():
                    self.bfp_cur_insn = lexer.next()
                    return BFInsn(BF_READ, 1)
                count: int = 1
                c = lexer.next()
                while c.tok_type == TOK_READ:
                    count += 1
                    c = lexer.next()
                self.bfp_cur_insn = c
                return BFInsn(BF_READ, count)
            if c.tok_type == TOK_WRITE:
                if not config.cfg_fold_repetition():
                    self.bfp_cur_insn = lexer.next()
                    return BFInsn(BF_WRITE, 1)
                count: int = 1
                c = lexer.next()
                while c.tok_type == TOK_WRITE:
                    count += 1
                    c = lexer.next()
                self.bfp_cur_insn = c
                return BFInsn(BF_WRITE, count)
        if self.bfp_loop_depth != 0:
            print(f"Syntax error: unmatched `[`", file=sys.stderr)
            return BFInsn(BF_END, 1)
        self.bfp_cur_insn = c
        return BFInsn(BF_END, 0)

