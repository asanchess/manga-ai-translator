import sys
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+[/~]",
    r"rmdir\s+/s\s+/q\s+[c-zC-Z]:\\",
    r"del\s+/f\s+/s\s+/q\s+[c-zC-Z]:\\",
    r"format\s+[c-zC-Z]:",
    r"drop\s+database",
    r"git\s+push\s+.*--force.*(main|master)",
]

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"decision": "allow"}))
            return
        payload = json.loads(raw)
        tool_call = payload.get("toolCall", {})
        if tool_call.get("name") == "run_command":
            cmd = tool_call.get("args", {}).get("CommandLine", "")
            for p in BLOCKED_PATTERNS:
                if re.search(p, cmd, re.IGNORECASE):
                    print(json.dumps({
                        "decision": "deny",
                        "reason": f"[Safety Guard] Заблокирована опасная команда: {p}"
                    }, ensure_ascii=True))
                    return
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        print(json.dumps({"decision": "ask", "reason": str(e)}))

if __name__ == "__main__":
    main()
