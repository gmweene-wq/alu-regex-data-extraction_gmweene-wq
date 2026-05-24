import re, json, os

# Read the raw text file 
in_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input", "raw-text.txt"))
text = open(in_path, "r", encoding="utf-8").read()

# Regex patterns for each type of data
PATTERNS = {
    "emails":    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
    "urls":      r"https?://[A-Za-z0-9.\-/?=&_:]+",
    "cards":     r"\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}",
    "times":     r"\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?",
    "html_tags": r"<[^>]+>",
    "hashtags":  r"#\w+"
}

BAD_WORDS = ["<script", "javascript:", "onclick", "onload", "drop table"]

#  algorithm to validate credit cards
def is_valid_card(card):
    digits = re.sub(r"\D", "", card)
    if len(digits) not in range(13, 20): return False
    total = 0
    for i, n in enumerate(digits[::-1]):
        n = int(n) * (2 if i % 2 == 1 else 1)
        total = total + (n - 9 if n in range(10, 19) else n)
    return total % 10 == 0

# Hide most of an email
def mask_email(e):
    name, _, domain = e.partition("@")
    if len(name) in range(0, 3): return ("*" * len(name)) + "@" + domain
    return name[0] + ("*" * (len(name) - 2)) + name[-1] + "@" + domain

# Hide a card (show only last 4)
def mask_card(c):
    d = re.sub(r"\D", "", c)
    return ("*" * (len(d) - 4)) + d[-4:]

# Find all matches, remove duplicates and other unsafe items
results = {}
for name, pattern in PATTERNS.items():
    clean = []
    for m in re.findall(pattern, text):
        m = m.strip()
        if any(w in m.lower() for w in BAD_WORDS) or m in clean: continue
        if name == "cards" and not is_valid_card(m): continue
        clean.append(m)
    results[name] = clean

# Sort ALU emails by domain (before masking, so we still see the domain)
alu = {"official": [], "alumni": [], "si": []}
for e in results["emails"]:
    if e.lower().endswith("@alueducation.com"):        alu["official"].append(mask_email(e))
    elif e.lower().endswith("@alumni.alueducation.com"): alu["alumni"].append(mask_email(e))
    elif e.lower().endswith("@si.alueducation.com"):     alu["si"].append(mask_email(e))

# Mask sensitive data
results["emails"] = [mask_email(e) for e in results["emails"]]
results["cards"] = [mask_card(c) for c in results["cards"]]

# Print everything
for name, items in results.items():
    print(f"\n===== {name.upper()} ({len(items)}) =====")
    for item in items: print(" ", item)
print("\n===== ALU EMAILS =====")
for group, items in alu.items(): print(f"  {group}: {items}")
print(f"\nGRAND TOTAL: {sum(len(v) for v in results.values())}")

# Save to JSON
results["alu_emails"] = alu
print("\n check the sample file to see results in JSON...")
