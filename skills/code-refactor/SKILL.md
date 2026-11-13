---
name: code-refactor
description: Code restructuring, dead code elimination, SOLID principles, DRY pattern extraction, and complexity reduction without altering external behavior.
---

# Code Refactoring & Clean Architecture Skill

## When to Use
Use when code has high cyclomatic complexity, duplicated logic, tightly coupled modules, or needs modern Python best practices.

## Guidelines
1. Verify behavior preservation: Ensure existing tests pass before and after refactoring.
2. Single Responsibility: Break down monolithic functions (>50 lines) into focused, single-purpose helpers.
3. Type Hints: Add explicit Python 3.10+ typing (e.g. 'dict[str, Any]', 'list[str]', 'Optional[T]').
4. Error Handling: Replace broad 'except:' clauses with specific exceptions ('ValueError', 'TimeoutError').
5. Separation of Concerns: Separate I/O and network operations from pure business logic.
