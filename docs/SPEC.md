# Phishing Pattern & Dataset Specification (Week 1 deliverable)

## Purpose
Defensive synthetic-data pipeline for training phishing-detection classifiers. Samples are non-deployable simulations.

## Common phishing characteristics
Artificial urgency, threats of suspension, claimed authority, unexpected rewards or refunds, requests to log in or pay through a link, generic greetings, changed bank details, requests for secrecy, unexpected file shares, pressure to phone a number.

## Taxonomy (labels)
| Key | Category | Binary label |
|---|---|---|
| urgency | Urgency / deadline pressure | 1 |
| authority | Authority impersonation | 1 |
| fear | Fear / account threat | 1 |
| reward | Reward / refund bait | 1 |
| shared_doc | Shared-document lure | 1 |
| invoice | Invoice / payment fraud | 1 |
| credential_reset | Credential / password reset | 1 |
| callback | Callback / phone scam | 1 |
| legitimate | Benign (incl. hard negatives) | 0 |

## Dataset schema (`data/dataset.csv`)
`id, subject, body, label, category, style, difficulty, indicators, source, safety_passed, created_at`
- `style`: formal | casual | terse | polished  - `difficulty`: easy (obvious cues) | hard (subtle)
- `source`: groq | template

## Placeholder rules
Only `[COMPANY] [USER] [SAFE-LINK] [PHONE] [AMOUNT] [DATE] [EMAIL]` are allowed. No real brands, URLs, domains, addresses, phone numbers, credentials, malware, attachment instructions or attack how-to.
Enforced in code by `core/safety.py` (`sanitize` then `validate`) on every sample, including Groq output.

## Quality requirements
- Balanced classes (ratio <= 1.5)  - no exact duplicates; near-duplicates (cosine > 0.9) < 15 %
- Every phishing category present; both difficulty levels present
- 0 safety violations  - lexical diversity (distinct bigrams) reported and monitored
- Hard negatives included so the classifier cannot rely on "has a link" or "mentions a deadline" alone
