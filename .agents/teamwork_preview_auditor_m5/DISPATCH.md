## 2026-08-22T13:07:26Z
<USER_REQUEST>
You are the Forensic Integrity Auditor (teamwork_preview_auditor) for the Manga AI Translator v3.0 project.
Your Working Directory: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_auditor_m5
Project Root: c:\Users\asana\OneDrive\Desktop\Manga
Original User Request: c:\Users\asana\OneDrive\Desktop\Manga\.agents\ORIGINAL_REQUEST.md
User Rules: c:\Users\asana\OneDrive\Desktop\Manga\AGENTS.md
Project Spec: c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_orchestrator_1\PROJECT.md

MANDATORY INTEGRITY AUDIT:
Perform a deep, adversarial forensic integrity audit on the entire codebase:
1. Static code analysis:
   - Verify that `cv2.rectangle` is ABSENT from `backend/agents/cleaner_agent.py`, `backend/agents/manga_pipeline_service.py`, and `backend/agents/translator_typesetter_agent.py`.
   - Verify that genuine inpainting (`cv2.inpaint` with Telea or LaMa) and per-pixel glyph binarization are implemented.
   - Verify physical layer isolation: `v3_translated` strictly takes `v2_cleaned` as input and does not bypass it to `v1_original`.
2. Glossary & Dialogue Topology:
   - Verify `backend/data/manga/The_Ultimate_of_All_Ages/glossary.json` contains genuine Xianxia terms (Gu Feiyang, Li Yunxiao, Beimin Clan, Yao Beast, Dantian, Qi) and that `llm_translator.py` genuinely injects them into LLM prompts.
   - Verify topological bubble sorting and 1-based sequential integer ID contract.
   - Verify mathematical chord equation in `translator_typesetter_agent.py`.
3. Singleton & Integrity Checker:
   - Verify `ModelInferenceManager` singleton logic.
   - Verify `ChapterIntegrityChecker` manifest generation (SHA-256 checksums) and `.zip` creation.
4. Anti-Patch Guard:
   - Audit `backend/tests/anti_patch_guard.py` to confirm it genuinely checks color variance ($\sigma^2 < 1.0$) and SSIM background difference ($\le 0.5\%$). Confirm zero dummy or mocked assertions.
5. Next.js Reader UX & Persistence:
   - Verify `frontend/src/app/reader/[manga]/page.tsx` contains real implementation of layer switcher (1/2/3), width presets, dual reading modes, dynamic progress, dead UI removal, and URL `?chapter=chapter_XXX` + `localStorage` persistence.
6. Write a comprehensive audit report with detailed evidence to `c:\Users\asana\OneDrive\Desktop\Manga\.agents\teamwork_preview_auditor_m5/audit_report.md` and `handoff.md` with a clear verdict: CLEAN or INTEGRITY VIOLATION.
7. Send a message to the parent orchestrator with your verdict and findings.
</USER_REQUEST>
