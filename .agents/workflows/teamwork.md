---
description: Safe isolated wrapper for /teamwork-preview
---

Когда пользователь вводит `/teamwork <задача>`:
1. Активируйте `teamwork-bridge` и запустите pre-flight проверку.
2. Сгенерируйте Timestamp (например, `20260822_150000`).
3. Выполните оркестрацию подзадач, направляя черновики в `.agents/exhaust/<timestamp>/`.
4. Запустите очистку: `python .agents/scripts/cleanup_exhaust.py <timestamp>`.
5. Выведите итоговый манифест созданных файлов.
