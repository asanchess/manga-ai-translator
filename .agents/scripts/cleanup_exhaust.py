import os
import sys
import shutil
from datetime import datetime

WHITELIST = {"README.MD", "AGENTS.MD", "GEMINI.MD", "MEMORY.MD", "CONVERSATION_HISTORY.MD"}

def main():
    ts = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d_%H%M%S")
    target = os.path.join(".agents", "exhaust", ts)
    os.makedirs(target, exist_ok=True)
    moved = []
    for item in os.listdir("."):
        if os.path.isfile(item) and item.upper().endswith(".MD") and item.upper() not in WHITELIST:
            shutil.move(item, os.path.join(target, item))
            moved.append(item)
    with open(os.path.join(target, "MANIFEST.md"), "w", encoding="utf-8") as f:
        f.write(f"# Teamwork Manifest ({ts})\n\nИзолировано файлов: {len(moved)}\n")
        for m in moved:
            f.write(f"- `{m}`\n")
    print(f"[Sweeper] Moved {len(moved)} stray files to {target}")

if __name__ == "__main__":
    main()
