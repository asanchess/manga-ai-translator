# 📐 Архитектурная спецификация (Spec.md)
## Manga AI Translator v3.0 SOTA Enterprise Reconstruction

**Версия:** 3.0.0  
**Дата:** 2026-08-22  
**Статус:** 🟡 Ожидает утверждения (Awaiting Approval)  
**Роль:** Lead Architect (Model: Pro)

---

## 1. Обзор архитектурной реконструкции

Реконструкция архитектуры пайплайна и читалки Manga AI Translator для полного исключения дефектов плашек/патчей, ускорения инференса и обновления интерфейса до стандарта SOTA Enterprise.

---

## 2. Модули и требования

### 2.1. Изоляция слоев и Anti-Patch Guard
- **Слой `v1_original`**: Неизменяемый исходник. Доступен только Scraper и Cleaner.
- **Слой `v2_cleaned` (`backend/agents/cleaner_agent.py`)**: Попиксельная бинаризация букв (`cv2.threshold` + дилатация 2px) + `cv2.inpaint(img, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)` / LaMa. Полный запрет `cv2.rectangle` и сплошных заливок.
- **Слой `v3_translated` (`backend/agents/translator_typesetter_agent.py`)**: Вход строго `v2_cleaned`. Векторная отрисовка `ImageDraw.Draw` (или прозрачный RGBA-композит). Запрет непрозрачного `canvas.paste`.
- **Программный Guard-валидатор (`backend/tests/anti_patch_guard.py`)**:
  - Check A: Solid patch detector (детекция блоков с нулевой/низкой цветовой дисперсией вне текста).
  - Check B: Background SSIM diff вне баблов $\le 0.5\%$ между `v3_translated` и `v1_original`.

### 2.2. Топология диалогов, Batch JSON и Персистентный глоссарий
- **Глоссарий (`backend/data/manga/The_Ultimate_of_All_Ages/glossary.json`)**: Персонажи, фракции, термины культивации. Подмешивается во все запросы к LLM.
- **Топологическая сортировка**: `sort_key = y_center * 10000 + x_center`, сквозные `id` (1, 2, 3...), единый batch-JSON запрос на страницу.
- **Эллиптический тайпсеттинг**: Формула хорды эллипса $2 \cdot a \cdot \sqrt{1 - (y/b)^2}$, $\le 85\%$ safe box, бинарный поиск кегля (38px–12px), межстрочный интервал $1.15 \times \text{font\_size}$, авто-контраст (черный текст на светлом, белый с обводкой 1.5px на темном).

### 2.3. Синглтон-инференс и Инспектор целостности
- **`ModelInferenceManager`**: Загрузка весов EasyOCR / Inpainting один раз при старте.
- **`ChapterIntegrityChecker`**: Проверка объема $\ge 8$ страниц на главу (ротация зеркал MangaKatana, Comick, MangaDex при нехватке), генерация `pipeline_manifest.json` и ZIP архивов.

### 2.4. Редизайн Next.js ридера (`frontend/src/app/reader/[manga]/page.tsx`)
- Шапка / Бургер-меню ("В каталог", выпадающий список глав, кнопки Пред./След. + хоткеи A/D и $\leftarrow$/$\rightarrow$).
- Переключатель слоев 1 RAW / 2 Clean / 3 РУС (хоткеи 1, 2, 3).
- Режимы ширины (700px, 900px, 1200px, 100%), режим ленты скролла / постраничный.
- Удаление кнопки "Авто-перевод главы" из ридера и ревизия AI Studio.
- Персистентность через `?chapter=chapter_XXX` + `localStorage` + `window.history.replaceState`.

---

## 3. План верификации и приемки

1. `python backend/tests/anti_patch_guard.py` -> 0 патчей, SSIM Pass.
2. `production_artifacts/Ongoing_Sync_Report.md` -> сводная таблица глав 531+.
3. Проверка читалки в браузере с сохранением состояния на F5.
