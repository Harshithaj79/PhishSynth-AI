# PhishSynth AI - Final Report (Week 4)
1. **Problem & defensive purpose** - why synthetic data, limits of real data.
2. **Taxonomy & dataset spec** - link to SPEC.md, any changes you made.
3. **Generation method** - prompt design (`build_prompt`), template fallback, safety layer; example samples.
4. **Preprocessing & features** - `clean_text`, TF-IDF (1-2 grams), handcrafted cue features; why each helps.
5. **Models** - logistic regression vs Naive Bayes vs random forest; table of accuracy / precision / recall / F1 / 5-fold F1.
6. **Evaluation** - confusion matrix, per-category recall, held-out-category recall, easy vs hard accuracy, real-data test (upload).
7. **Refinement** - what the quality report flagged, what you changed (new templates, dedupe, prompts), before/after metrics.
8. **Limitations** - synthetic-on-synthetic optimism, template repetition, language/style drift.
9. **Responsible use** - safety controls, intended defensive use only.
