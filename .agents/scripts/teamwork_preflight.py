import os

def main():
    print("[Pre-flight] Checking environment before Teamwork...")
    gitignore = ".gitignore"
    entry = "\n.agents/exhaust/\n"
    if os.path.exists(gitignore):
        with open(gitignore, "r", encoding="utf-8") as f:
            c = f.read()
        if ".agents/exhaust" not in c:
            with open(gitignore, "a", encoding="utf-8") as f:
                f.write(entry)
    else:
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write(entry.strip() + "\n")
    print("[Pre-flight] .agents/exhaust/ isolated in .gitignore.")

if __name__ == "__main__":
    main()
