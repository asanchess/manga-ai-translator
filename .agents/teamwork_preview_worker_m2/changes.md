# Changes Report — Milestone M2: Dialogue Topology, Batch JSON & Persistent Glossary

## 1. Persistent Xianxia Glossary
- **File**: ackend/data/manga/The_Ultimate_of_All_Ages/glossary.json
- **Details**:
  - Implemented comprehensive domain dictionary with 57 terms across characters, factions/locations, cultivation ranks, and concepts.
  - Characters: Gu Feiyang (Гу Фэйян), Li Yunxiao (Ли Юньсяо), Luo Yunshang (Ло Юньшан), Xiao Qingxuan (Сяо Цинсюань), Mo Huayuan (Мо Хуаюань), etc.
  - Factions/Locations: Beimin Clan (Клан Бэймин), Sanctuary (Святилище), Heavenly Water Nation (Страна Небесной Воды), etc.
  - Cultivation terms & Ranks: Martial Sovereign (Боевой Владыка), Nine Heavens (Девять Небес), Primordial Divine Realm (Изначальное Божественное Царство), Dantian (Даньтянь), Qi (Ци), Yao Beast (Демонический Зверь), etc.

## 2. Dynamic Glossary Loading & Batch Translation
- **File**: ackend/agents/llm_translator.py
- **Details**:
  - Implemented load_manga_glossary(manga_title, glossary_path) to load manga-specific terms dynamically from ackend/data/manga/{title}/glossary.json.
  - Implemented ormat_glossary_for_prompt(glossary) to inject mandatory terminology rules into LLM system prompts for local Ollama and OpenRouter.
  - Enhanced call_ollama_batch and call_openrouter_batch with prompt injection and robust JSON schema extraction supporting 	ranslated and 	ranslation keys.
  - Enhanced allback_translate_text to perform multi-word regex phrase replacements for all glossary terms.
  - Enforced strict 1-based sequential integer ID matching in 	ranslate_bubbles_batch where every input dialogue ID is guaranteed in the output.

## 3. Topological Bubble Sorting & 1-Based ID Ordering
- **File**: ackend/agents/ocr_engine.py
- **Details**:
  - Upgraded 	opological_reading_sort_key to calculate (y_center // row_height) * 10000 + x_center (and pure center math y_center * 10000 + x_center), supporting LTR (manhua) and RTL (manga).
  - Enforced top-to-bottom, left-to-right / right-to-left topological ordering before assigning strict 1-based sequential integer IDs (1, 2, 3, ...).
  - Added direction and ow_height parameters to extract_text_and_bubbles.

## 4. Typesetter Optimization & Auto-Contrast
- **Files**: ackend/agents/translator_typesetter_agent.py, ackend/agents/manga_pipeline_service.py
- **Details**:
  - Verified and upgraded 	ypeset_bubble with binary search font scaling (38px to 12px) fitting elliptical horizontal chord \sqrt{1-(y/b)^2}$ within $\le 85\%$ safe oval bounds.
  - Enforced auto-contrast (pure black on light background; bright white with 1.5px–2px stroke outline on dark background).
  - Updated process_page_translation and manga_pipeline_service.py to pass manga_title and pair translations strictly by dialogue.id == bubble.id.

## 5. Automated Verification Test Suite
- **File**: ackend/tests/test_glossary_and_topology.py
- **Details**:
  - Created 5 comprehensive unit tests covering:
    1. Glossary loading and term integrity (57 terms)
    2. Prompt injection block formatting
    3. Topological sorting math and sequential 1-based ID assignment
    4. Batch JSON translation contract with strict ID preservation
    5. Offline Xianxia multi-word fallback translation
  - Verified 100% test pass rate on 	est_glossary_and_topology.py, 	est_typesetter_layout.py, and nti_patch_guard.py.
