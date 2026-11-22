"""Safety layer: every sample passes sanitize() and validate() before it can be stored or shown."""
import re
from .taxonomy import PLACEHOLDERS

URL_RE = re.compile(r"(?:https?://|hxxps?://|www\.)\S+|\b[\w-]+\.(?:com|net|org|io|co|info|biz|xyz|ru|cn)\b\S*", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<![\w\[])\+?\d[\d\-\s().]{7,}\d(?![\w\]])")
BRANDS = ["paypal", "amazon", "microsoft", "google", "apple", "netflix", "dhl", "fedex", "ups", "chase", "wells fargo",
          "bank of america", "irs", "facebook", "instagram", "linkedin", "dropbox", "docusign", "whatsapp", "office 365"]
BRAND_RE = re.compile(r"\b(" + "|".join(re.escape(b) for b in BRANDS) + r")\b", re.I)
# Content we never allow: operational attack material rather than classifier training text.
BLOCKLIST = re.compile(r"\b(keylogger|payload|exploit|ransomware|powershell|macro[- ]enabled|enable macros|cvv|ssn|social security number|"
                       r"card number|wallet address|bitcoin|seed phrase|\.exe|\.scr|\.js attachment)\b", re.I)
PLACEHOLDER_RE = re.compile(r"\[[A-Z-]+\]")

def sanitize(text: str) -> str:
    text = URL_RE.sub("[SAFE-LINK]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return BRAND_RE.sub("[COMPANY]", text).strip()

def validate(text: str):
    """Return (ok, reasons). A sample is safe only if it has no raw URL/email/phone/brand and no blocked terms."""
    reasons = []
    if URL_RE.search(text): reasons.append("raw URL")
    if EMAIL_RE.search(text): reasons.append("raw email address")
    if PHONE_RE.search(text): reasons.append("raw phone number")
    if BRAND_RE.search(text): reasons.append("real brand name")
    if BLOCKLIST.search(text): reasons.append("operational attack term")
    bad = [p for p in PLACEHOLDER_RE.findall(text) if p not in PLACEHOLDERS]
    if bad: reasons.append(f"unknown placeholder {bad[0]}")
    return (not reasons), reasons
