# -*- coding: utf-8 -*-
import json
import os
import re

def export_transcript():
    transcript_path = r"C:\Users\asana\.gemini\antigravity-ide\brain\82afacb4-6595-41bc-919d-fd18e11e0577\.system_generated\logs\transcript.jsonl"
    out_path = os.path.join(os.path.dirname(__file__), "..", "CONVERSATION_HISTORY.md")
    
    dialogue_entries = []
    
    step_num = 0
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            source = data.get("source", "")
            step_type = data.get("type", "")
            content = data.get("content", "")
            
            # Extract User Messages
            if source == "USER_EXPLICIT" or step_type == "USER_INPUT":
                # Clean up <USER_REQUEST> tags if present
                clean_text = content
                if "<USER_REQUEST>" in clean_text:
                    m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", clean_text, re.DOTALL)
                    if m:
                        clean_text = m.group(1).strip()
                dialogue_entries.append({
                    "role": "👤 User",
                    "text": clean_text
                })
                
            # Extract Assistant / Model Final Responses
            elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
                # Content has the markdown text sent to the user
                if content and isinstance(content, str) and content.strip():
                    text = content.strip()
                    # Skip internal system logs
                    if not text.startswith("Created At:") and not text.startswith("Tool is running as a background task"):
                        dialogue_entries.append({
                            "role": "🤖 Assistant (Antigravity)",
                            "text": text
                        })
            elif source == "MODEL" and step_type == "GENERIC":
                if content and isinstance(content, str) and len(content.strip()) > 30:
                    text = content.strip()
                    if not text.startswith("Created At:") and not text.startswith("Tool is running as a background task"):
                        dialogue_entries.append({
                            "role": "🤖 Assistant (Antigravity)",
                            "text": text
                        })

    # Build Markdown document
    lines = [
        "# 📜 Полная история диалога и разработки проекта (Manga AI Translator)",
        "",
        "> Автоматически экспортированная хроника всех пользовательских запросов, решений архитектуры, тестов и исправлений.",
        "",
        "---",
        ""
    ]
    
    turn = 1
    for entry in dialogue_entries:
        role = entry["role"]
        text = entry["text"]
        if not text:
            continue
            
        if "User" in role:
            lines.append(f"## 💬 Сообщение #{turn} • {role}\n")
            lines.append(f"{text}\n")
            lines.append("---\n")
            turn += 1
        else:
            lines.append(f"### {role}\n")
            lines.append(f"{text}\n")
            lines.append("---\n")
            
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines))
        
    print(f"Exported {len(dialogue_entries)} entries to {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    export_transcript()
