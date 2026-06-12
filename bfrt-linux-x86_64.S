
.LBFMEM_SIZE_Q = 1<<4

.global _read
.global _write
.global _start
.extern _bf
.text

_read:
	movq	%rdi,%rsi
	xorl	%eax,%eax
	xorl	%edi,%edi
	movl	$1,%edx
	syscall
	movq	%rsi,%rdi
	ret

_write:
	movl	$1,%eax
	movq	%rdi,%rsi
	movl	%eax,%edx
	movl	%eax,%edi
	syscall
	movq	%rsi,%rdi
	ret

_start:
	movabsq	$_bfmem,%rdi
	call _bf
	decq	(%rsp)
	movl	$60,%eax
	xorl	%edi,%edi
	syscall

.bss
_bfmem:
	.zero .LBFMEM_SIZE_Q << 3 /* 1 MiB */

