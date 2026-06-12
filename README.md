# Brainfrick Compiler for x86-64 🚀

A Brainfrick parser, interpreter, and x86-64 code generator written in Python.

This project parses Brainfrick source code into a compact intermediate representation, performs instruction compression, and emits x86-64 assembly that can be linked against a small runtime library.

It's not "just a Brainfrick interpreter" — it's a complete compilation pipeline consisting of a parser, bytecode format, interpreter, and native code generator.

## ✨ Features

* Brainfrick parser with bracket validation
* Compact fixed-width bytecode representation
* Dynamic memory model with optional limits
* Built-in interpreter
* x86-64 assembly code generation
* Runtime I/O abstraction
* Instruction compression and normalization
* Custom runtime ABI support

It's more than "just source-to-assembly translation" — the same intermediate representation can be interpreted directly or compiled into native code.

## 🔧 Instruction Compression

The parser automatically combines consecutive operations into a single instruction.

| Source | Internal Representation |
| ------ | ----------------------- |
| `++++` | `BF_ADD(4)`             |
| `----` | `BF_ADD(252)`           |
| `>>>>` | `BF_SEEK(4)`            |
| `<<<<` | `BF_SEEK(-4)`           |
| `....` | `BF_WRITE(4)`           |
| `,,,,` | `BF_READ(4)`            |

This dramatically reduces instruction count for generated Brainfrick programs.

For example:

```brainfrick
++++++++++++++++++++++++++++++++++++++++++++++++++
```

becomes a single internal instruction rather than fifty separate operations.

## 📦 Bytecode Format

Instructions are stored in a compact fixed-width format:

| Offset | Size    | Description           |
| ------ | ------- | --------------------- |
| 0      | 1 byte  | Opcode                |
| 1      | 4 bytes | Signed 32-bit operand |

Total size per instruction:

```text
5 bytes
```

The design is intentionally simple — every instruction has exactly the same size, making indexing and jump resolution trivial.

### Opcodes

| Opcode     | Value |
| ---------- | ----- |
| `BF_ADD`   | 1     |
| `BF_SEEK`  | 2     |
| `BF_JZ`    | 3     |
| `BF_JNZ`   | 4     |
| `BF_READ`  | 5     |
| `BF_WRITE` | 6     |

## 🧠 Memory Model

Memory is represented as a dynamically growing byte array.

Properties:

* 8-bit cells
* Automatic growth
* Optional upper memory limit
* Zero-initialized semantics
* Bounds checking on negative pointer movement

Reads from unwritten memory return zero.

Cell arithmetic wraps modulo 256:

```brainfrick
-
```

executed on a zero-valued cell produces:

```text
255
```

It's not signed arithmetic — it's byte arithmetic.

## ⚙️ Runtime Interface

Generated code relies on a small runtime library.

Required symbols:

```asm
_read
_write
```

### `_read`

Reads a byte and returns a value in the range:

```text
0..255
```

Returning `0` on EOF is recommended.

### `_write`

Consumes the current cell value and performs output.

The implementation is entirely runtime-defined — terminal I/O, files, sockets, virtual devices, embedded systems, or something stranger.

## 🏗️ Custom ABI

The generated code assumes a custom runtime ABI.

The active Brainfrick data pointer is stored in:

```text
rdi
```

Runtime functions must preserve `rdi`.

This allows generated code to call runtime helpers without saving and restoring the Brainfrick data pointer around every call.

It's not the System V ABI — it's a deliberately minimal ABI designed around Brainfrick execution.

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

Loops become labels and conditional branches:

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
as hello.s -o hello.o
ld hello.o runtime.o -o hello
```

The exact build process depends on your assembler, linker, and runtime implementation.

## ❌ Parser Errors

Parsing fails when:

* `]` appears without a matching `[`
* `[` remains unmatched at end-of-file
* A compressed seek exceeds signed 32-bit range
* A compressed read/write count exceeds signed 32-bit range
* Instruction count exceeds signed 32-bit range

## 🎯 Design Philosophy

Brainfrick already has an instruction set.

This project intentionally does not extend it.

Instead of introducing new opcodes, functionality is provided through the runtime boundary. Generated code interacts with the outside world through `_read`, `_write`, and any additional runtime support code you choose to provide.

It's not "Brainfrick with extensions" — it's Brainfrick with a customizable runtime.

The compiler's job is simple:

1. Parse Brainfrick.
2. Build a compact intermediate representation.
3. Execute it or generate native code.

Everything else belongs in the runtime.

Small language. Small compiler. Native code. ⚡

