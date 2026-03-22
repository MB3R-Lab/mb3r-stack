# Backlog

This document is a dated snapshot of the GitHub issue backlog for `MB3R-Lab/mb3r-stack`.

Source of truth: GitHub Issues in the repository itself.

Snapshot date: `2026-03-22`

## Open issues

At the time of this snapshot there is one open issue:

- [#20](https://github.com/MB3R-Lab/mb3r-stack/issues/20) `Migrate GitHub Actions workflows off deprecated Node.js 20 actions`

## Current status

- The workflow updates in this branch move the repository to `actions/checkout@v6`, `actions/setup-python@v6`, and `azure/setup-helm@v4.3.1`.
- That change is intended to satisfy the acceptance criteria of issue `#20`.
- Close the issue after `ci` and `release` on `main` confirm the Node.js 20 deprecation warning is no longer emitted.
