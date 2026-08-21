import json

with open(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\agents\translations_db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

for entry in db["dialogue"]:
    if "earth-attribute" in entry["patterns"] or "playing with earth" in entry["patterns"]:
        entry["patterns"].extend(["playing with", "in front of me", "front of me", "atinidutc", "martial skills", "skkills"])
        print("Updated entry patterns:", entry["patterns"])

with open(r"c:\Users\asana\OneDrive\Desktop\Manga\backend\agents\translations_db.json", "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("Saved updated translations_db.json")
