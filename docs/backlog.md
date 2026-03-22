# Backlog

This document is a dated snapshot of the GitHub issue backlog for `MB3R-Lab/mb3r-stack`.

Source of truth: GitHub Issues in the repository itself.

Snapshot date: `2026-03-22`

## Open issues

At the time of this snapshot there is one open issue:

- [#20](https://github.com/MB3R-Lab/mb3r-stack/issues/20) `Migrate GitHub Actions workflows off deprecated Node.js 20 actions`

## Current status

- The repository has already moved `actions/checkout` to `v6` and `actions/setup-python` to `v6`.
- `azure/setup-helm@v4.3.1` still emits the GitHub Node.js 20 deprecation annotation.
- `ci` run `23407592947` for commit `ce14aef6dd2ee99571a7ef4d6a211f9cf9173aba` succeeded functionally but did not satisfy the backlog acceptance criteria for issue `#20`.
- Issue `#20` remains open until `.github/workflows/ci.yml` and `.github/workflows/release.yml` stop using a Node 20-based Helm setup action or otherwise run without the annotation.
