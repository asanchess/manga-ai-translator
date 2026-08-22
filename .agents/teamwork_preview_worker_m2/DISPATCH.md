## 2026-08-22T12:50:55Z
You are the Builder / Worker for Milestone M2: Dialogue Topology, Batch JSON & Persistent Glossary.
Your Working Directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m2
Project Root: c:\Users\asana\OneDrive\Desktop\Manga
Original User Request: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
User Rules: c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
Project Spec: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_orchestrator_1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A forensic auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Tasks for M2:
1. Create backend/data/manga/The_Ultimate_of_All_Ages/glossary.json:
   - Comprehensive terminology dictionary including:
     - Characters: Gu Feiyang -> Гу Фэйян, Li Yunxiao -> Ли Юньсяо, Luo Yunshang -> Ло Юньшан, etc.
     - Factions / Locations: Beimin Clan -> Клан Бэймин, Sanctuary -> Святилище, Heavenly Water Nation -> Страна Небесной Воды, etc.
     - Cultivation terms & Concepts: Yao Beast -> Демонический Зверь, Dantian -> Даньтянь, Qi -> Ци, Martial Sovereign -> Боевой Владыка, Nine Heavens -> Девять Небес, Primordial Divine Realm -> Изначальное Божественное Царство, etc.
2. Update backend/agents/llm_translator.py:
   - Dynamically load manga-specific glossary.json (e.g. from backend/data/manga/{title}/glossary.json) and inject it into system prompts for every translation pass.
   - Support batch JSON translation requests where whole page dialogues are translated in a single structured JSON array request/response, preserving strict 1-based sequential integer IDs.
3. Update backend/agents/ocr_engine.py:
   - Enforce bubble sorting top-to-bottom, right-to-left / left-to-right via y_center * 10000 + x_center (or (y_center // 50) * 10000 + x_center), assign 1-based sequential integer IDs to detected bubbles.
4. Verify & update backend/agents/translator_typesetter_agent.py and manga_pipeline_service.py:
   - Typeset strictly where dialogue.id == bubble.id.
   - Ensure elliptical chord equation 2*a*sqrt(1-(y/b)^2), <= 85% safe oval bounds, binary search font scale (38px to 12px), auto-contrast (black on light, white with 1.5px black outline on dark).
5. Create and run unit tests for glossary loading, prompt injection, and topological sorting:
   - python backend/tests/test_typesetter_layout.py
   - python backend/tests/test_glossary_and_topology.py (create unit test)
6. Write c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_worker_m2\changes.md and handoff.md.
7. Automatically commit and push all changes to Git per AGENTS.md rules.
8. Send a completion message to the parent orchestrator.
