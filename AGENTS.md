# AI Agent Collaboration Protocol

This repository is optimized for autonomous AI coding assistants (Antigravity, Claude Engineer, etc.).

## Handover Instructions
1. **Context First**: Always read the `implementation_plan.md` in the `.gemini/antigravity` directory.
2. **Mandate Adherence**: 
    1. **PRODUCTION FINAL**: Strictly follow the "PRODUCTION FINAL" mandate provided in the initial conversation history.
    2. **Zero-Mock Policy**: Use real infrastructure (Supabase, Redis, RabbitMQ, MinIO) for all tests. Mocking of infrastructure is strictly prohibited. Unit tests should only exist for pure logic; any interaction with services must be an integration test.
3. **No Stubs**: Never commit `pass`, `// TODO`, or incomplete logic.
4. **Numerical Standards**: All variables in `apps/api/src/methods/` must be descriptive (e.g., `strike_price`, not `K`).
5. **Observability**: Every new API route must be instrumented in `src/metrics.py`.

## Verification Workflow
1. Run `pytest` in `apps/api/` for logic validation.
2. Check `http://localhost:9090` for metrics registration.
3. Verify Realtime functionality via `apps/web/src/hooks/useRealtime.ts`.

---
*Created by Antigravity for Joseph Kamau Maina (SJOSKA2211)*
