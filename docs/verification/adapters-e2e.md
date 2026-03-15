# Adapter E2E

This verification path exercises the reusable GitHub, GitLab, and Jenkins adapter contracts against representative payloads.

```bash
make e2e-adapters
```

What it checks:

- discovery, gate, and combined report artifacts for GitHub reusable workflows
- discovery, gate, and combined report artifacts for GitLab catalog components
- discovery, gate, and combined report artifacts for Jenkins shared-library semantics
- example consumer files still point at the expected adapter entrypoints
- generated artifacts keep the published `v1alpha1` contract shapes
