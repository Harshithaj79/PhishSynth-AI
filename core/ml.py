"""Preprocessing, feature engineering, Scikit-learn baseline, evaluation and dataset-quality analysis (Weeks 3-4)."""
import re
import numpy as np, pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import MaxAbsScaler
from .safety import validate

CUES = {
    "urgency": {"urgent", "immediately", "now", "asap", "expires", "expire", "within", "final", "today", "deadline", "act", "mandatory"},
    "threat": {"suspended", "suspend", "locked", "terminated", "penalties", "penalty", "unauthorized", "compromised", "closure", "dispute"},
    "reward": {"refund", "prize", "reward", "winner", "claim", "bonus", "gift", "congratulations", "credit"},
    "credential": {"password", "credentials", "login", "username", "verify", "confirm", "identity", "sign"},
}
FEATURE_NAMES = ["len_chars", "n_words", "exclamations", "caps_ratio", "safe_links", "placeholders", "urgency_cues", "threat_cues", "reward_cues", "credential_cues"]

def text_of(df): return (df["subject"].fillna("") + ". " + df["body"].fillna("")).astype(str)

def clean_text(t):
    t = re.sub(r"\[([a-z-]+)\]", lambda m: " ph" + m.group(1).replace("-", "") + " ", t.lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()

def cue_hits(text):
    words = set(re.findall(r"[a-z']+", text.lower()))
    return {k: sorted(words & v) for k, v in CUES.items()}

class Handcrafted(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        rows = []
        for t in X:
            words = re.findall(r"[a-z']+", t.lower()); letters = [c for c in t if c.isalpha()]; ws = set(words)
            rows.append([len(t) / 500, len(words) / 100, t.count("!"), 10 * sum(c.isupper() for c in letters) / max(len(letters), 1),
                         t.count("[SAFE-LINK]"), len(re.findall(r"\[[A-Z-]+\]", t)) / 3] + [len(ws & v) for v in CUES.values()])
        return np.array(rows, dtype=float)

def make_model(name="logistic_regression"):
    clf = {"logistic_regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
           "naive_bayes": MultinomialNB(), "random_forest": RandomForestClassifier(200, random_state=0, n_jobs=-1)}[name]
    feats = FeatureUnion([("tfidf", TfidfVectorizer(preprocessor=clean_text, ngram_range=(1, 2), sublinear_tf=True)),
                          ("hand", Pipeline([("h", Handcrafted()), ("s", MaxAbsScaler())]))])
    return Pipeline([("features", feats), ("clf", clf)])

def top_features(model, k=10):
    clf = model.named_steps["clf"]
    names = list(model.named_steps["features"].transformer_list[0][1].get_feature_names_out()) + FEATURE_NAMES
    if hasattr(clf, "coef_"): w = clf.coef_[0]
    elif hasattr(clf, "feature_log_prob_"): w = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    else:
        imp = clf.feature_importances_; i = np.argsort(imp)[::-1][:k * 2]
        return {"important": [names[j] for j in i], "phishing": [], "legitimate": []}
    o = np.argsort(w)
    return {"phishing": [names[j] for j in o[::-1][:k]], "legitimate": [names[j] for j in o[:k]]}

def near_duplicate_indices(df, thr=0.9, limit=2500):
    """Indices (of df.index) to drop: later rows whose TF-IDF cosine similarity to an earlier row exceeds thr."""
    sub = df.iloc[:limit]
    if len(sub) < 2: return []
    X = TfidfVectorizer(preprocessor=clean_text).fit_transform(text_of(sub))
    S = np.triu(cosine_similarity(X), 1)
    drop = sorted({sub.index[j] for j in np.where((S > thr).any(axis=0))[0]})
    return drop

def quality_report(df):
    n = len(df)
    if n == 0: return {"rows": 0, "suggestions": ["Dataset is empty. Build one first."]}
    vc = df["label"].value_counts().to_dict()
    texts = text_of(df)
    bigrams = [b for t in texts for b in zip(clean_text(t).split(), clean_text(t).split()[1:])]
    near = len(near_duplicate_indices(df.head(1200)))
    unsafe = sum(not validate(t)[0] for t in texts)
    rep = {"rows": n, "phishing": int(vc.get(1, 0)), "legitimate": int(vc.get(0, 0)),
           "by_category": df["category"].value_counts().to_dict(), "by_difficulty": df["difficulty"].value_counts().to_dict(),
           "exact_duplicates": int(texts.map(clean_text).duplicated().sum()), "near_duplicates": near,
           "avg_words": round(float(texts.str.split().str.len().mean()), 1),
           "distinct_bigrams": round(len(set(bigrams)) / max(len(bigrams), 1), 3),
           "safety_violations": int(unsafe)}
    s = []
    if rep["phishing"] and rep["legitimate"] and max(rep["phishing"], rep["legitimate"]) / min(rep["phishing"], rep["legitimate"]) > 1.5:
        s.append("Classes are imbalanced: generate more of the smaller class.")
    if near / min(n, 1200) > 0.15: s.append(f"{near} near-duplicates found: run Refine to remove them, or add more templates / use Groq for variety.")
    if rep["distinct_bigrams"] < 0.1: s.append("Low lexical diversity: add templates, switch on Groq generation, or raise style variety.")
    if unsafe: s.append(f"{unsafe} rows fail safety validation: remove them before sharing the data.")
    return {**rep, "suggestions": s or ["No data-quality problems detected."]}

def train_eval(df, model_name="logistic_regression", test_size=0.25, seed=42):
    df = df.dropna(subset=["subject", "body", "label"]).reset_index(drop=True)
    y = df["label"].astype(int)
    if len(df) < 40 or y.nunique() < 2 or y.value_counts().min() < 10:
        raise ValueError("Need at least 40 rows with 10+ examples of both classes. Build a larger dataset first.")
    X = text_of(df)
    tr, te = train_test_split(df.index, test_size=test_size, stratify=y, random_state=seed)
    model = make_model(model_name).fit(X[tr].tolist(), y[tr])
    pred = model.predict(X[te].tolist())
    p, r, f, _ = precision_recall_fscore_support(y[te], pred, average="binary", pos_label=1, zero_division=0)
    k = min(5, int(y.value_counts().min()))
    cv = cross_val_score(make_model(model_name), X.tolist(), y.values, cv=StratifiedKFold(k, shuffle=True, random_state=seed), scoring="f1")
    t = df.loc[te].assign(pred=pred, text=X[te])
    per_cat = {c: round(float((g.pred == 1).mean()), 3) for c, g in t[t.label == 1].groupby("category")}
    per_diff = {d: round(float((g.pred == g.label).mean()), 3) for d, g in t.groupby("difficulty")}
    # Generalisation: hold out an entire category to see whether the model catches an "unseen" manipulation style.
    legit_test = set(t[t.label == 0].index); gen = {}
    for c in sorted(df[df.label == 1].category.unique()):
        held = df[(df.category == c)].index
        if len(held) < 5: continue
        tr_idx = [i for i in df.index if i not in set(held) and i not in legit_test]
        if y[tr_idx].nunique() < 2: continue
        m = make_model("logistic_regression").fit(X[tr_idx].tolist(), y[tr_idx])
        gen[c] = round(float(m.predict(X[held].tolist()).mean()), 3)
    wrong = t[t.pred != t.label].head(5)
    suggestions = []
    weak = [c for c, v in per_cat.items() if v < 0.8]
    if weak: suggestions.append(f"Low recall on: {', '.join(weak)}. Add more or more varied samples for these categories.")
    if per_diff.get("hard", 1) + 0.05 < per_diff.get("easy", 0): suggestions.append("'Hard' samples are classified worse than 'easy' ones: add more subtle phishing and hard-negative legitimate emails.")
    low_gen = [c for c, v in gen.items() if v < 0.7]
    if low_gen: suggestions.append(f"Held-out category recall is low for: {', '.join(low_gen)}. The model may be memorising category wording, so diversify templates.")
    if accuracy_score(y[te], pred) > 0.98: suggestions.append("Near-perfect accuracy on synthetic data usually means templates are too easy or repetitive. Validate on real labelled emails before trusting it.")
    return model, {
        "model": model_name, "train_rows": len(tr), "test_rows": len(te),
        "accuracy": round(float(accuracy_score(y[te], pred)), 3), "precision": round(float(p), 3), "recall": round(float(r), 3), "f1": round(float(f), 3),
        "cv_f1_mean": round(float(cv.mean()), 3), "cv_f1_std": round(float(cv.std()), 3),
        "confusion_matrix": confusion_matrix(y[te], pred, labels=[0, 1]).tolist(),
        "per_category_recall": per_cat, "per_difficulty_accuracy": per_diff, "heldout_category_recall": gen,
        "top_features": top_features(model),
        "misclassified": [{"subject": r.subject, "category": r.category, "label": int(r.label), "pred": int(r.pred)} for r in wrong.itertuples()],
        "suggestions": suggestions or ["Metrics look healthy. Next step: test on a real labelled dataset."]}

def explain(model, text):
    proba = float(model.predict_proba([text])[0][1])
    return {"phishing_probability": round(proba, 3), "label": "phishing" if proba >= 0.5 else "legitimate",
            "cues": {k: v for k, v in cue_hits(text).items() if v}, "has_safe_link": "[SAFE-LINK]" in text}
