---
name: tdd
description: Build features or fix bugs test-first with the red-green-refactor cycle. Use when the user requests TDD, test-first development, regression tests, or integration tests.
---

# Test-Driven Development

Work in short vertical slices using the red → green → refactor cycle. Each test should describe observable behavior and remain useful when the implementation changes.

When exploring the codebase, read `CONTEXT.md` (if it exists) so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

Identify the seam before writing a test. Confirm it with the user only when choosing the seam would materially change the public interface, scope, or architecture. For straightforward work, use the existing public interface and proceed.

Ask: "What's the public interface, and which seams should we test?"

When the interface itself is in question, use `$codebase-design` to decide where the seam belongs and what it should expose.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Rules of the loop

- **Red.** Write one test for the next behavior and run it. Confirm it fails for the expected reason before changing production code.
- **Green.** Write only enough production code to make that test pass. Run the focused test and the relevant suite.
- **Refactor.** Improve names, duplication, structure, and design while preserving behavior. Keep the tests green throughout.
- **One slice at a time.** Complete red → green → refactor for one behavior before starting the next.
