"""Phishing-category taxonomy, style and difficulty descriptions, placeholder rules (Week 1 spec)."""

PLACEHOLDERS = ["[COMPANY]", "[USER]", "[SAFE-LINK]", "[PHONE]", "[AMOUNT]", "[DATE]", "[EMAIL]"]

CATEGORIES = {
    "urgency": {"label": "Urgency / deadline pressure", "desc": "An artificial deadline pushes the reader to act before thinking.",
                "indicators": ["artificial deadline", "pressure to act now", "generic greeting"]},
    "authority": {"label": "Authority impersonation", "desc": "Pretends to be a director, HR or IT to exploit hierarchy and secrecy.",
                  "indicators": ["claims authority", "request for secrecy", "unusual request"]},
    "fear": {"label": "Fear / account threat", "desc": "Threatens suspension, compromise or penalties to trigger a rushed response.",
             "indicators": ["threat of suspension", "security scare", "vague 'unusual activity'"]},
    "reward": {"label": "Reward / refund bait", "desc": "Offers money, prizes or refunds to lure a click.",
               "indicators": ["unexpected reward", "refund offer", "claim-now wording"]},
    "shared_doc": {"label": "Shared-document lure", "desc": "A fake 'a file was shared with you' notification.",
                   "indicators": ["unexpected file share", "curiosity hook", "generic document name"]},
    "invoice": {"label": "Invoice / payment fraud", "desc": "Fake invoice or a claimed change of bank details.",
                "indicators": ["payment request", "changed bank details", "overdue pressure"]},
    "credential_reset": {"label": "Credential / password reset", "desc": "Asks the reader to re-enter or reset login details through a link.",
                         "indicators": ["password expiry claim", "login request via link", "account verification"]},
    "callback": {"label": "Callback / phone scam", "desc": "No link; pushes the reader to phone a number about a charge.",
                 "indicators": ["unexpected charge", "phone-number callback", "urgent cancellation"]},
    "legitimate": {"label": "Legitimate (benign)", "desc": "Normal business or service email. Includes hard negatives that use deadlines or links honestly.",
                   "indicators": ["expected context", "no pressure", "no credential request"]},
}
PHISH_CATEGORIES = [k for k in CATEGORIES if k != "legitimate"]

TONE_DESCRIPTIONS = {
    "formal": "formal and corporate, with complete sentences and a professional sign-off.",
    "casual": "friendly and conversational, short sentences, informal wording.",
    "terse": "very short and abrupt, a few lines at most.",
    "polished": "fluent, personalised and typo-free, like a modern AI-written message with no obvious language errors.",
}
DIFFICULTY_TIPS = {
    "easy": "contains several obvious red flags (pressure words, generic wording, alarming claims).",
    "hard": "subtle and well written, with few obvious red flags, so a classifier must rely on context and intent.",
}
