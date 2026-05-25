import re
import json
import os
# open the file and read the text
def read_file():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input", "raw-text.txt"))
    return open(path, "r", encoding="utf-8").read()

# emails
def find_emails(text):
    return re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)

# urls
def find_urls(text):
    return re.findall(r"https?://[A-Za-z0-9.\-/?=&_:]+", text)

# cards
def find_cards(text):
    return re.findall(r"\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}", text)
#html tags
def find_html(text):
    return re.findall(r"<[^>]+>", text)

# hashtags
def find_hashtags(text):
    return re.findall(r"#\w+", text)


# Check if a value is safe
def is_safe(value):
    bad = ["<script", "javascript:", "onclick", "onload", "drop table"]
    for word in bad:
        if word in value.lower():
            return False
    return True


# validate credit card numbers
def is_valid_card(card):
    digits = re.sub(r"\D", "", card)
    if len(digits) not in range(13, 20):
        return False
    total = 0
    for i, n in enumerate(digits[::-1]):
        n = int(n)
        if i % 2 == 1:
            n = n * 2
            if n in range(10, 19):
                n = n - 9
        total = total + n
    return total % 10 == 0

# Hide most of an email
def mask_email(email):
    name, _, domain = email.partition("@")
    if len(name) in range(0, 3):
        return ("*" * len(name)) + "@" + domain
    return name[0] + ("*" * (len(name) - 2)) + name[-1] + "@" + domain

# Hide a credit card (show only last 4)
def mask_card(card):
    digits = re.sub(r"\D", "", card)
    return ("*" * (len(digits) - 4)) + digits[-4:]

# Remove duplicates and unsafe items from a list
def clean_list(items):
    clean = []
    for item in items:
        if is_safe(item) and item not in clean:
            clean.append(item)
    return clean

# Sort ALU emails into three groups by domain
def classify_alu(emails):
    alu = {"official": [], "alumni": [], "si": []}
    for e in emails:
        if e.lower().endswith("@alueducation.com"):
            alu["official"].append(mask_email(e))
        elif e.lower().endswith("@alumni.alueducation.com"):
            alu["alumni"].append(mask_email(e))
        elif e.lower().endswith("@si.alueducation.com"):
            alu["si"].append(mask_email(e))
    return alu

# Print a list of results
def show(name, items):
    print(f"\n===== {name.upper()} ({len(items)}) =====")
    for item in items:
        print(" ", item)
def save_results(results):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "sample-output.json"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(results, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nSaved to: {path}")
# Main program
def main():
    text = read_file()

    # Find everything
    emails = clean_list(find_emails(text))
    urls = clean_list(find_urls(text))
    cards = clean_list(find_cards(text))
    html = clean_list(find_html(text))
    hashtags = clean_list(find_hashtags(text))

    # Sort ALU emails before masking
    alu = classify_alu(emails)

    # Mask sensitive data
    emails = [mask_email(e) for e in emails]
    cards = [mask_card(c) for c in cards]

    # Print results
    show("emails", emails)
    show("urls", urls)
    show("cards", cards)
    show("html_tags", html)
    show("hashtags", hashtags)

    print("\n===== ALU EMAILS =====")
    for group, items in alu.items():
        print(f"  {group}: {items}")

    total = len(emails) + len(urls) + len(cards) + len(html) + len(hashtags)
    print(f"\nGRAND TOTAL: {total}")
    
main()

print("CHECK THE UOTPUT SAMPLE IN OUTPUT/JSON")
