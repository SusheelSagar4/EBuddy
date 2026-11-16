# ADR-0001: Zero-Outbound Airgap & LiteLLM Gateway Isolation

## Status
Accepted (2026-11-13)

## Context
Competition and enterprise safety guidelines mandate strict data privacy and zero outbound telemetry. The system must run air-gapped without unvetted third-party calls, while supporting flexible model switching across OpenAI, Gemini, Azure, or local Ollama deployments.

## Decision
1. `litellm` is established as the sole LLM interaction library.
2. Only `app/llm/client.py` is permitted to import `litellm`. No other module in the codebase may directly import `litellm`.
3. Telemetry is explicitly disabled (`litellm.telemetry = False`) and local cost mapping is enabled (`litellm.local_model_cost_map = True`).
4. A deterministic `FakeLLM` is implemented for all tests and offline CI runs, ensuring 100% test reproducibility with zero token cost and zero network calls.

## Consequences
### Positive
- Strict isolation prevents token leaks, inadvertent network requests, and external dependencies during test runs.
- Easy drop-in configuration for different local or hosted model providers via `.env`.

### Negative
- Requires maintaining prompt schemas and mock responses in `FakeLLM` to match production tasks.

