---
name: test-driven-development
description: Automated test generation with pytest/unittest, test coverage analysis, edge case identification, and mock isolation.
---

# Test-Driven Development (TDD) & Automated Testing Skill

## When to Use
Use when writing new modules, verifying bug fixes, auditing test coverage, or creating mock fixtures.

## Guidelines
1. Structure tests using Arrange-Act-Assert (AAA) pattern.
2. Test critical edge cases:
   - Empty/None inputs
   - Boundary values (0, -1, max limits)
   - Network timeouts and rate limits (429s)
   - Concurrency race conditions
3. Mock external services: Never make live network calls during automated unit tests; use 'unittest.mock'.
4. Ensure tests are self-contained and run cleanly via 'pytest' or 'python -m unittest'.
