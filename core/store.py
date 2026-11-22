"""Tiny dataset store: in-memory list persisted to data/dataset.csv (schema = Week 1 spec)."""
import os, re, threading, uuid
from datetime import datetime, timezone
import pandas as pd

COLUMNS = ["id", "subject", "body", "label", "category", "style", "difficulty", "indicators", "source", "safety_passed", "created_at"]
PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dataset.csv")

def norm(subject, body): return re.sub(r"\W+", " ", f"{subject} {body}".lower()).strip()

class Store:
    def __init__(self, path=PATH):
        self.path, self.lock = path, threading.Lock()
        self.rows = pd.read_csv(path).to_dict("records") if os.path.exists(path) else []
        self.keys = {norm(r["subject"], r["body"]) for r in self.rows}

    def make_row(self, email, category, style, difficulty, source):
        return {"id": uuid.uuid4().hex[:8], "subject": email["subject"], "body": email["body"], "label": 0 if category == "legitimate" else 1,
                "category": category, "style": style, "difficulty": difficulty, "indicators": "|".join(email.get("indicators", [])),
                "source": source, "safety_passed": True, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    def add(self, rows):
        added = skipped = 0
        with self.lock:
            for r in rows:
                k = norm(r["subject"], r["body"])
                if k in self.keys: skipped += 1; continue
                self.keys.add(k); self.rows.append(r); added += 1
            self._save()
        return added, skipped

    def df(self): return pd.DataFrame(self.rows, columns=COLUMNS)

    def replace(self, df):
        with self.lock:
            self.rows = df.to_dict("records"); self.keys = {norm(r["subject"], r["body"]) for r in self.rows}; self._save()

    def clear(self):
        with self.lock: self.rows, self.keys = [], set(); self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        pd.DataFrame(self.rows, columns=COLUMNS).to_csv(self.path, index=False)
