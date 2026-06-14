# Pre-thesis-prep

Documenting my preparation for a Master's thesis on real-time virtual PLCs
on PREEMPT_RT Linux, starting at Linutronix GmbH in September 2026.

Following a personal 13-week study plan (June–August 2026) covering:

- PREEMPT_RT kernel build, tuning, and measurement
- Real-time scheduling theory (Bertolotti & Manduchi)
- Linux internals (Kerrisk, TLPI)
- KVM and ACRN hypervisor architecture
- Container runtimes for real-time workloads
- IEC 61131-3, Soft-PLCs, TSN

Each week has its own folder under `measurements/` with raw data summary,
analysis, and the plot artifacts. Code is in `code/`. Kernel configs in
`kernel-config/`.

## Hardware

MSI GF75 Thin 9SCSR, Intel Core i7-9750H (12 logical CPUs), Ubuntu 24.04.
Consumer laptop — not industrial-grade. SMI hits and firmware quirks are
expected; the point is learning the methodology, not chasing absolute
numbers.

## Status

- [x] W23: PREEMPT_RT 6.12 built and booted
- [ ] W24: 24-hour cyclictest baseline under load
- [ ] W25: ftrace deep dive
- [ ] ... (etc.)
