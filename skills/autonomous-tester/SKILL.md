---
name: autonomous-tester
description: Automated test execution, headless syntax verification, and zero-hang validation workflows.
when-to-use:
  - test
  - testing
  - verify
  - check errors
  - syntax check
  - validate
user-invocable: true
argument-hint: "[command or file to test]"
allowed-tools:
  - run_command
  - read_file
  - view_file_slice
---

# Autonomous Verification & Testing Workflows

Use this skill to verify code correctness without causing process timeouts or blocking dev server hangs.

## Core Rules for Testing:
1. **Never run interactive servers**:
   - Do NOT run `npm start`, `npx vite`, `python app.py` directly if they listen indefinitely.
   - Use `npm run build` or `npx tsc --noEmit` to verify React/TypeScript code.
   - Use `python -m py_compile <file.py>` or `pytest` to test Python code.

2. **Headless Node / JS Syntax Checks**:
   - Run `node -c <file.js>` to check for JavaScript parse errors.
   - Run `npx eslint <file> --no-ignore` if ESLint is installed.

3. **Verify Deliverable Existence**:
   - Confirm target file exists on disk and has length > 200 bytes.
   - Check that required documentation (`walkthrough.md`, `README.md`) exists.
