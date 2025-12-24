# Indigo Machine - Checkpoints

We use checkpoints to prevent regressions and accidental “project drift”.

## What a checkpoint includes
1. Update `docs/ARCHITECTURE.md` if behavior changed (services, protocol, settings, endpoints).
2. Run smoke checks:
   - `make lint`
   - `make test`
   - `make dev` then verify:
     - GET `/api/health`
     - GET `/api/devices`
   - `make services` then verify logs show poll loop started
3. Create a git tag:
   - `git tag -a checkpoint-phase-2.6 -m "Phase 2.6 stable"`
   - `git push origin checkpoint-phase-2.6`

## Rules
- `make dev` must remain stable (API dev server).
- `make services` must remain stable (poller/services runner).
- `ENABLE_API` and `ENABLE_UI` are stable feature gates.
- Protocol changes must be documented in ARCHITECTURE.
