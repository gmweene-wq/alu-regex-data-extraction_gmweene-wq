# ALU Regex Data Extraction & Secure Validation

A regex-based program that extracts structured data from raw text returned by
an external API, validates each match for correctness, and rejects hostile or
malformed input.

Built as a Junior Frontend Developer assignment — focus is on accuracy,
robustness, and security awareness.

## Project structure

alu-regex-data-extraction_{GithubUsername}/
├── input/
│   └── raw-text.txt          # realistic raw text (CRM ticket export)
├── src/
│   └── main.py               # extractors, validators, security checks
├── output/
│   └── sample-output.json    # generated results (masked sensitive data)
└── README.md

## How to run

Requires **Python 3.9+** — no third-party packages needed.

```bash
# from the project root
python3 src/main.py
```

The program will:

1. Read `input/raw-text.txt` (with a 1 MB safety cap).
2. Run every regex extractor against the text.
3. Validate each match (Luhn check for cards, digit-count for phones, ALU
   domain whitelist for ALU emails, dangerous-pattern check for everything).
4. Print a summary to the console.
5. Write the full structured result to `output/sample-output.json` with
   sensitive fields **masked**.

Sample console output:

```
=======================================================
  ALU Regex Extraction — Run Summary
=======================================================
  emails_found       9
  urls_found         7
  phones_found       6
  cards_found        2
  times_found        12
  html_tags_found    14
  hashtags_found     16
  currency_found     7
  alu_official       5
  alu_alumni         1
  alu_si             2


  Sensitive fields are masked in output (see JSON).

```
## What gets extracted

All eight optional data types are implemented (the assignment requires a
minimum of four; emails and credit cards are required).

| # | Type            | Notes                                                |
|---|-----------------|------------------------------------------------------|
| 1 | Emails          | RFC-pragmatic shape; masked in output                |
| 2 | URLs            | http / https; path, query, fragment supported        |
| 3 | Phone numbers   | `+CC`, `(NNN) NNN-NNNN`, `NNN-NNN-NNNN`, etc.        |
| 4 | Credit cards    | Visa / MC / Discover (4-4-4-4) + AMEX (4-6-5);  |
| 5 | Time            | Both 12-hour (`3:42 PM`) and 24-hour (`14:05`)       |
| 6 | HTML tags       | Open, close, and self-closing                        |
| 7 | Hashtags        | Must start with a letter; allows hyphens             |
| 8 | Currency        | `$`, `€`, `£`, `USD`, `EUR`, `GBP`, `RWF`; supports both `1,000.00` and `1.000,50` formats |

### ALU-specific email validation

Every email found is also classified into one of three ALU buckets if its
domain matches (case-insensitive):

| Bucket   | Domain                       |
|----------|------------------------------|
| official | `@alueducation.com`          |
| alumni   | `@alumni.alueducation.com`   |
| SI       | `@si.alueducation.com`       |

Anything else is still extracted as a generic email but is **not** classified
as ALU.

---
## Regex pattern explanations

Every pattern lives in `src/main.py` with a comment above it. Quick tour:

- **`EMAIL_RE`** — local part up to 64 chars, domain labels separated by dots,
  TLD 2-24 chars. Bounded character classes prevent catastrophic backtracking.
- **`URL_RE`** — `http(s)://` + host + optional port + optional path. The path
  segment uses `[^\s<>"']*` to stop at whitespace and at HTML-quoting
  characters (so URLs don't bleed into attribute values).
- **`PHONE_RE`** — three explicit alternatives (international, parenthesised,
  hyphenated). Negative look-arounds `(?<![\w/])` / `(?![\w/])` prevent
  overlap with dates like `2026-04-12` and with longer digit runs like card
  numbers.
- **`CARD_RE`** — two alternatives: AMEX (4-6-5) and the standard 16-digit
  4-group shape. Final acceptance requires a **Luhn checksum** — random
  16-digit strings that happen to match the shape are rejected.
- **`TIME_RE`** — one alternative for 12-hour with AM/PM, one for 24-hour.
  Bounded character classes (`[0-5]\d`, `[01]?\d|2[0-3]`) enforce real ranges.
- **`HTML_TAG_RE`** — tag name 1-31 chars, optional attributes capped at 200
  chars to avoid pathological inputs.
- **`HASHTAG_RE`** — leading look-behind so `foo#bar` doesn't match, must
  start with a letter, up to 50 chars of word-chars or hyphens.
- **`CURRENCY_RE`** — currency symbol or 3-letter ISO code, then a digit run
  that accepts thousands separators in either `,` or `.` style.

---
## Security considerations

Security thinking is built into every layer, not bolted on at the end.

### 1. Input is treated as untrusted
- The input file is read with a hard **1 MB size cap** (`MAX_INPUT_BYTES`).
  Anything larger is refused — prevents memory exhaustion and ReDoS
  amplification.
- Bytes are decoded with `errors="replace"` so a malformed encoding can't
  crash the pipeline.

### 2. ReDoS resistance
- No pattern uses nested unbounded quantifiers (`(a+)+`, `(a*)*`).
- All character classes are bounded with explicit `{m,n}` limits.
- Alternations are written so each branch matches a disjoint shape.

### 3. Injection-pattern detection
- A `DANGEROUS_PATTERNS` list flags `<script`, `javascript:`, `on*=` event
  handlers, `<iframe`, and SQL-keyword sequences like `DROP TABLE`.
- Any match that contains a dangerous substring is **dropped silently** —
  it is never echoed back as "valid" data and never written to the output.
- The included input (`raw-text.txt`) contains a hostile ticket (#48204)
  with all of these probes, and the output confirms none of them appear.

### 4. Schema-level validation, not just shape
- **Phones** — must contain 7-15 digits after stripping separators (E.164).
- **Credit cards** — must contain 13-19 digits **and** pass the Luhn
  checksum. `1234 5678 9012 3456` looks card-shaped but fails Luhn and is
  rejected.
- **ALU emails** — domain is matched against an explicit whitelist; lookalikes
  like `alueducation.co` or `alu-education.com` are rejected.

### 5. Sensitive data is masked in artefacts
- **Emails** are written as `a*********e@domain.com` — first and last char of
  the local part visible, everything else masked.
- **Credit cards** are written as `************4242` — last 4 only, as
  recommended by PCI-DSS for non-production logs.
- The full unmasked values exist only in memory during the run; they are
  not persisted to `sample-output.json` and not printed to the console.

### 6. Defensive coding
- All extraction goes through one helper (`extract`) that always applies the
  dangerous-pattern check, so a new extractor can't accidentally skip it.
- De-duplication preserves document order so the output is deterministic
  and easy to diff in code review.

---
## Verifying the security claims

Run the program, then check that none of the hostile tokens from the spam
ticket appear in the output:

```bash
python3 src/main.py

python3 -c "
import json
data = json.dumps(json.load(open('output/sample-output.json')))
for token in ['admin@@', '4532aaaa', 'javascript:', '<script',
              'DROP TABLE', '1234 5678 9012', 'htp:/', 'ABC-DEF']:
    assert token not in data, f'LEAK: {token!r} appears in output'
print('All hostile tokens were correctly filtered.')
"
```

---
## What's intentionally out of scope

- No HTML/UI front-end — the assignment focuses on extraction logic.
- No network calls — the "external API response" is simulated as a static
  text file.
- No persistent storage / database — output is a single JSON artefact.
