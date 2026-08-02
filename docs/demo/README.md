# Boomerang demo

Production-style static demo combining the Boomerang marketing surface with the OnBxrD resident-operations workflow described in `docs/PRD.md` and `docs/uiFlow.mermaid`.

## Run locally

```bash
pnpm install
pnpm dev
```

On this machine, Node is provided by WSL Ubuntu:

```bash
wsl -d Ubuntu -- bash -lic "cd /mnt/d/P-052/docs/demo && corepack pnpm install && corepack pnpm dev --host 0.0.0.0"
```

The demo is intentionally local-only: the resident checklist, grounded concierge response, workflow steps, and management approval queue use mock data in `src/data.ts` and React state.

## Build

```bash
pnpm build
```

From PowerShell through WSL:

```powershell
wsl.exe -d Ubuntu -- bash -lic "cd /mnt/d/P-052/docs/demo && corepack pnpm build"
```
