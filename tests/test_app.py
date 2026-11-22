import json, os, sys, io
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.pop("GROQ_API_KEY", None)
import pytest
import app as A
from core.store import Store
from core.safety import sanitize, validate

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "store", Store(str(tmp_path / "d.csv"))); A.STATE["model"] = None
    return A.app.test_client()

def test_sanitize_and_validate():
    s = sanitize("Visit https://evil.com/x or paypal.com, mail a@b.com or call 415-555-2671 as PayPal")
    assert validate(s)[0] and "evil" not in s and "[SAFE-LINK]" in s and "[COMPANY]" in s
    assert not validate("download keylogger.exe")[0]

def test_extract_json_variants():
    assert A.extract_json('{"a":1}') == {"a": 1}
    assert A.extract_json('```json\n{"a":2}\n```') == {"a": 2}
    assert A.extract_json('Sure! {"a":3} done') == {"a": 3}

def test_generate_validation(client):
    assert client.post("/generate", json={"count": 99}).status_code == 400
    assert client.post("/generate", json={"category": "nope"}).status_code == 400
    assert client.post("/generate", json={"context": "see http://x.com"}).status_code == 400

def test_generate_template_mode(client):
    d = client.post("/generate", json={"category": "fear", "count": 3, "save": True}).get_json()
    assert d["success"] and len(d["emails"]) == 3 and "GROQ_API_KEY" in d["notice"]
    assert all(validate(e["subject"] + e["body"])[0] for e in d["emails"])

def test_groq_path_filters_unsafe(client, monkeypatch):
    class R:  # fake Groq client
        class choices_:  pass
    payload = {"emails": [{"subject": "Verify now", "body": "Hello [USER], confirm at http://evil.com within [DATE] to keep access.", "indicators": ["deadline"]},
                          {"subject": "Bad", "body": "Install this keylogger payload now please today", "indicators": []}]}
    class Msg: content = "```json\n" + json.dumps(payload) + "\n```"
    class Ch: message = Msg()
    class Resp: choices = [Ch()]
    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kw): return Resp()
    monkeypatch.setattr(A, "client", FakeClient)
    d = client.post("/generate", json={"category": "urgency", "count": 2}).get_json()
    assert d["emails"][0]["source"] == "groq" and "evil" not in d["emails"][0]["body"]
    assert d["emails"][1]["source"] == "template"   # unsafe Groq sample dropped, topped up from templates

def test_full_pipeline(client):
    assert client.post("/train", json={}).status_code == 400            # empty dataset
    b = client.post("/dataset/build", json={"per_category": 20}).get_json()
    assert b["added"] > 100
    t = client.post("/train", json={"model": "logistic_regression"}).get_json()["results"]
    assert t["accuracy"] > 0.8 and "heldout_category_recall" in t
    for m in ("naive_bayes", "random_forest"): assert client.post("/train", json={"model": m}).status_code == 200
    p = client.post("/predict", json={"text": "URGENT: verify your password within [DATE]: [SAFE-LINK]"}).get_json()
    assert p["label"] == "phishing"
    assert client.post("/dataset/refine").get_json()["success"]
    assert client.get("/dataset/download?fmt=jsonl").status_code == 200
    csv = "subject,body,label\nHi,See you at lunch tomorrow,0\nURGENT,Verify within [DATE] [SAFE-LINK],1\n"
    u = client.post("/evaluate_upload", data={"file": (io.BytesIO(csv.encode()), "t.csv")}).get_json()
    assert u["rows"] == 2

def test_index(client):
    r = client.get("/"); assert r.status_code == 200 and b"PhishSynth AI" in r.data
