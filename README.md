# Brainfrick Compiler for x86_64 🚀

A Brainfrick parser, interpreter, and x86_64 code generator — written in Python. 🏗️

This project parses Brainfrick source code into a compact intermediate representation — with instruction compression — and emits x86_64 assembly that can be linked against a small runtime library. 🚀

It's not just a Brainfrick interpreter — it's a complete compilation pipeline consisting of a parser, bytecode format, interpreter, and native code generator. ⚙️

## ✨ Features

* Brainfrick parser — with bracket validation ✅
* Compact fixed-width bytecode representation 💾
* Dynamic memory model — with optional limits 🧠
* Built-in interpreter 📼
* x86_64 assembly code generation 🤖
* Runtime I/O abstraction ⚙️
* Instruction compression and normalization 📦
* Custom runtime ABI support 🏗️

It's more than "just source-to-assembly translation" — the same intermediate representation can be interpreted directly or compiled into native code. ⚙️

## 🧠 Memory Model

The interpreter represents memory as a dynamically growing byte array. 📼

Properties:

* 8-bit cells 📦
* Automatic growth ♾️
* Optional upper memory limit 🗜️
* Zero-initialized semantics 0️⃣
* Bounds checking on negative pointer movement ✅

Reads from unwritten memory return zero. 0️⃣

Cell arithmetic wraps modulo 256:

```brainfrick
-
```

executed on a zero-valued cell produces:

> 255

It's not signed arithmetic — it's byte arithmetic. 🧮🔄

## ⚙️ Runtime Interface

Generated code relies on a small runtime library. 🏗️

Required symbols:

* `_read`
* `_write`
* `_start`

### `_read`

Reads a byte and returns a value in the range:

> [0,256)

Returning `0` on EOF is recommended — but not required. 0️⃣

### `_write`

Consumes the current cell value and performs output. 🖨️

### `_start`

This symbol is the entry point of the program — it allocates the Brainfrick memory buffer and sets up the data pointer before calling the Brainfrick entry point `_bf`. 🚀

The implementation is entirely runtime-defined — terminal I/O, files, sockets, virtual devices, embedded systems, or time travel. ✨

## 🏗️ Custom ABI

The generated code assumes a custom runtime ABI. ⚙️

The active Brainfrick data pointer is stored in:

> %rdi

Runtime functions must preserve `%rdi` — they are not required to preserve any other registers. 💻

This allows generated code to call runtime helpers without saving and restoring the Brainfrick data pointer around every call. ✨

It's not the System V ABI — it's a deliberately minimal ABI designed around Brainfrick execution. 💯

## 📜 Example Output

Input:

```brainfrick
+++.
```

Generated assembly:

```asm
addb $3,(%rdi)
call _write
```

Loops become labels — and conditional branches:

```brainfrick
[->+<]
```

↓

```asm
.L0:
cmpb $0,(%rdi)
je .L6

...

.L6:
cmpb $0,(%rdi)
jne .L0
```

## 🚀 Usage

Generate assembly:

```bash
python3 bf.py hello.bf > hello.s
```

Assemble and link against a runtime implementation:

```bash
as bfrt-linux-x86_64.S -o runtime.o
as hello.s -o hello.o
ld hello.o runtime.o -o hello
```

The exact build process depends on your assembler, linker, and runtime implementation. 🏗️

## ❌ Parser Errors

Parsing fails when:

* `]` appears without a matching `[` → 💥
* `[` remains unmatched at end-of-file → 💥
* A compressed seek exceeds signed 32-bit range → 💥
* A compressed read/write count exceeds signed 32-bit range → 💥
* Instruction count exceeds signed 32-bit range → 💥

## 🚀 Optimizations

This compiler optimizes certain Brainfrick constructs to generate better code. 💯

Optimizations can be toggled individually by changing their respective flag in `01_config.py`. 📝

### `cfg_remove_dead_code`

This option allows the compiler to elide operations that add zero to the current cell or the data pointer, and converts instructions that add or subtract 1 to `inc` and `dec` respectively.
Only functional if `cfg_fold_repetition` is `True`. Default is `True`. 🗑️

For example:

```brainfrick
++--.+>.
```

↓

```asm
call _write
incb (%rdi)
incq %rdi
call _write
```

instead of

```asm
addb $2,(%rdi)
subb $2,(%rdi)
call _write
addb $1,(%rdi)
addq $1,%rdi
call _write
```

### `cfg_fold_repetition`

This option allows the compiler to fold multiple consecutive `+`/`-`, `<`/`>`, `.`, or `,` operations into a single instruction.
If this option is disabled, always use short instruction encoding for increments and decrements. Default is `True`. 📦

For example:

```brainfrick
+++++
```

↓

```asm
addb $5,(%rdi)
```

instead of:

```asm
incb (%rdi)
incb (%rdi)
incb (%rdi)
incb (%rdi)
incb (%rdi)
```

### `cfg_lazy_seek`

This option allows the compiler to avoid emitting code that moves the data pointer when it doesn't need to. Default is `True`. ✨

For example:

```brainfrick
+>>+++<<.
```

↓

```asm
incb (%rdi)
addb $3,2(%rdi)
call _write
```

instead of:

```asm
incb (%rdi)
addq $2,%rdi
addb $3,(%rdi)
subq $2,%rdi
call _write
```

### `cfg_partial_eval`

This option allows the compiler to precompute constants where `cfg_fold_repetition` would not be able to, and only emit them when they are needed. It assumes the memory buffer starts zeroed out.
Enabling this option may significantly increase compilation times, especially if `cfg_fold_repetition` is disabled. Default is `False`. 💯

For example:

```brainfrick
+++>++.<<+++.
```

↓

```asm
incq %rdi
movb $2,(%rdi)
call _write
decq %rdi
movb $6,(%rdi)
call _write
```

instead of

```
addb $3,(%rdi)
incq %rdi
addb $2,(%rdi)
call _write
decq %rdi
addb $3,(%rdi)
call _write
```

> Note: this may cause problems if your runtime is non-standard, see "Undefined Behavior" below. ⚠️

## ⚠️❓🤔 Undefined Behavior

The following conditions may cause a Brainfrick program to behave unexpectedly — in compiled mode:

* The `_read` function reads from the Brainfrick memory buffer → 💥
* The `_read` function writes to the Brainfrick memory buffer — other than the selected cell → 💥
* The `_write` function writes to the Brainfrick memory buffer → 💥
* The `_write` function writes to the Brainfrick memory buffer — other than the selected cell → 💥
* The Brainfrick program is started — but the Brainfrick memory buffer is not zeroed out → 💥
* The Brainfrick data pointer moves — outside of the Brainfrick memory buffer → 💥
* The start of the Brainfrick memory buffer is not 16-byte aligned → 💥

## 🎯 Design Philosophy

Brainfrick already has an instruction set. ✨

This project intentionally does not extend it — additional functionality can be provided by the runtime library using the `_read`, `_write`, and `_start` symbols. 🏗️

It's not "Brainfrick with extensions" — it's Brainfrick with a customizable runtime. 💯

The compiler's job is simple:

1. Parse Brainfrick. ⚙️
2. Build a compact intermediate representation. 📦
3. Execute it or generate native code. 🤖

Everything else belongs in the runtime. ⚙️

Small language. Small compiler. Native code. ⚡

> provide salad was here :)

