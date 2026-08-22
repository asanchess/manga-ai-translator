---
description: Run the full SDLC pipeline: Spec -> Approval -> Code -> QA
---

Когда пользователь вводит `/pipeline <задача>`:
1. Активируйте `spec-builder`, сформируйте `production_artifacts/Spec.md`.
2. **ОСТАНОВИТЕСЬ** и ждите слова "Approved".
3. Активируйте `code-builder`, реализуйте код и модульные тесты.
4. Активируйте `qa-audit`, проверьте результат и сформируйте `production_artifacts/QA_Report.md`.
