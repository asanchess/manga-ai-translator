import re

raw = "NO, IT'S NOT YAO TRANSFORMATION\nALTHOUGH THE EFFECTS ARE SIMILAR;\nTHIS STATE IS MUCH MORE POWERFL THAN\nYAO TRANSFORMATIONII"
clean_lower = " ".join(raw.lower().split())

pattern = r"no, it'?s not yao transformation.*"
m = re.search(pattern, clean_lower, flags=re.IGNORECASE | re.DOTALL)
print("Matched?", bool(m))
if m:
    print("Match text:", m.group(0))
