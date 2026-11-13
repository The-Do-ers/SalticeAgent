---
name: security-auditor
description: OWASP Top 10 security audits, secret leakage detection, shell command injection prevention, and dependency vulnerability inspection.
---

# Security Auditor & Vulnerability Scanner Skill

## When to Use
Use when reviewing code before deployment, handling user-supplied inputs, running shell commands, or storing credentials.

## Guidelines
1. Command Injection: Never pass unvalidated user inputs directly into 'shell=True' or raw string interpolation. Use list arguments.
2. Secret Protection: Verify that API keys, tokens, and passwords are never hardcoded in source files. Always load from '.env'.
3. SQL Injection: Use parameterized queries or ORM bindings; never concatenate raw strings in SQL statements.
4. Path Traversal: Validate that user-provided file paths are restricted within the target workspace directory.
5. Least Privilege: Ensure file operations only request the minimum required permissions.
