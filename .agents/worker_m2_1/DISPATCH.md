## 2026-08-23T10:37:03Z
You are the Builder / Worker for Milestone 2 (Multi-Provider LLM Cascade & 10-Chapter Terminology Graph) of the «Manga AI Translator Studio» project.
Your working directory is: c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m2_1
You MUST read the following authoritative files first before starting:
1. c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
2. c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
3. c:\Users\asana\OneDrive\Desktop\Manga\PROJECT.md
4. c:\Users\asana\OneDrive\Desktop\Manga\.agents\explorer_backend_1\report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Write Boundaries:
You own exclusively:
- `c:\Users\asana\OneDrive\Desktop\Manga\backend\agents\llm_translator.py`

Tasks:
1. Inspect `backend/agents/llm_translator.py` and `backend/config/translation_providers.json`.
2. Implement missing provider adapters in `SOTALLMTranslator`:
   - `translate_with_openrouter()`: Calling OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`) with models like Claude 3.5 Sonnet / Qwen 2.5 72B using `OPENROUTER_API_KEY`.
   - `translate_with_deepseek()`: Calling DeepSeek API (`https://api.deepseek.com/v1/chat/completions`) with DeepSeek-V3 / DeepSeek-R1 using `DEEPSEEK_API_KEY`.
3. Establish robust 4-tier cascade failover logic in `translate_batch()`:
   - Tier 1: OpenRouter (if configured/available)
   - Tier 2: Google Gemini 2.5 Flash (`GEMINI_API_KEY`)
   - Tier 3: Groq (`GROQ_API_KEY`)
   - Tier 4: Local Xianxia Terminology Fallback
4. Maintain 10-chapter terminology graph injection (`glossary_memory.json` / `glossary.json`):
   - Strict 1-based sequential ID contracts (`[{"id": 1, "translated": "..."}]`).
   - Resilient JSON array parsing with markdown fence stripping, trailing comma cleanup, and regex extraction fallback.
   - Zero English dialogue leaks on target Russian translations.
5. Verify test compatibility by running:
   `python -m unittest backend/tests/test_glossary_and_topology.py`
6. Document all changes and verification test runs in `c:\Users\asana\OneDrive\Desktop\Manga\.agents\worker_m2_1\handoff.md`.
7. Send completion message back to parent orchestrator.
