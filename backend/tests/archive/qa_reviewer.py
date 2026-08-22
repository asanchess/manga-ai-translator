import os
import sys

print("🚀 Запуск строгого QA-инспектора пайплайна...")

errors = 0

# 1. Проверка правил Inpainting'а (запрет на cv2.rectangle)
cleaner_path = os.path.join(os.path.dirname(__file__), "agents", "cleaner_agent.py")
if os.path.exists(cleaner_path):
    with open(cleaner_path, "r", encoding="utf-8") as f:
        content = f.read()
        if "cv2.rectangle" in content and "inpaint" not in content.lower():
            print("❌ ОШИБКА: Обнаружен старый костыль (cv2.rectangle) вместо нормального Inpainting в cleaner_agent.py!")
            errors += 1
        elif "simple_lama_inpainting" not in content and "cv2.INPAINT_TELEA" not in content:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Cleaner Agent не использует LaMa или OpenCV Inpainting явно.")
        else:
            print("✅ Cleaner Agent использует правильные методы Inpainting.")
else:
    print("❌ ОШИБКА: cleaner_agent.py не найден.")
    errors += 1

# 2. Проверка интеграции Ollama
translator_path = os.path.join(os.path.dirname(__file__), "agents", "llm_translator.py")
if os.path.exists(translator_path):
    with open(translator_path, "r", encoding="utf-8") as f:
        content = f.read()
        if "11434" not in content and "ollama" not in content.lower():
            print("❌ ОШИБКА: llm_translator.py не настроен на локальный Ollama (порт 11434 не найден).")
            errors += 1
        else:
            print("✅ Ollama интеграция найдена в llm_translator.py.")
else:
    print("❌ ОШИБКА: llm_translator.py не найден.")
    errors += 1

# 3. Проверка API Deploy
main_path = os.path.join(os.path.dirname(__file__), "main.py")
if os.path.exists(main_path):
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
        if "/api/deploy" not in content:
            print("❌ ОШИБКА: Эндпоинт /api/deploy для ИИ Ассистента не найден в main.py!")
            errors += 1
        else:
            print("✅ Эндпоинт /api/deploy найден в main.py.")

if errors == 0:
    print("🎉 QA Check пройден: Архитектурные правила соблюдены.")
else:
    print(f"💥 QA Check провален: Найдено {errors} критических ошибок!")
    sys.exit(1)
