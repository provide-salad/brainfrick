# 99_main.py

def main(args: tuple[str, ...]):
    if len(args) < 2:
        print("[ERR] Usage: <input>", file=sys.stderr)
        return 2
    with open(args[1], "r") as f:
        source_code: str = f.read()
    bf = bf_parse(source_code)
    if bf is None:
        print("[ERR] Failed to parse BF", file=sys.stderr)
        return 1
    impl = BFImpl()

    @impl.readfunc
    def _read() -> int:
        buf: bytes = sys.stdin.buffer.read(1)
        if len(buf) == 0:
            return 0
        return buf[0]

    @impl.writefunc
    def _write(x: int) -> None:
        sys.stdout.buffer.write(bytes((x,)))

    optimizer = BFOptimizer(bf)
    optimized = optimizer.optimize()

#    interp = BFInterp(optimized, impl, 0)
#    interp.run()
#    return 0

    compiler = BFCompilerX64(optimized)
    compiled = compiler.compile()
    if compiled is None:
        print("[ERR] Failed to compile BF", file=sys.stderr)
        return 1
    print(".extern _read\n.extern _write\n.global _bf\n_bf:")
    print(compiled)
    print("ret")
    return 0

if __name__ == "__main__":
    exit(main(tuple(sys.argv)))

