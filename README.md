# Riail: hurling rules explained

Riail is a small web app for club referees. You describe something that happened in a hurling match, choose which rulebook applies, and Riail finds the matching rules and explains them in plain English, citing the rule numbers it used.

- **Two rulebooks:** club games use the current rules; college games use the 2026 trial rules. Every answer is labelled with the rulebook it came from, so the two are never mixed up.
- **No guessing:** if no rule matches the question, Riail says "not covered" and the AI is never asked.
- **Checked answers:** an AI answer is only shown if it cites at least one rule, and every rule it cites was actually found for that question.
- **Fallback:** if the AI is down, slow or gives a bad answer, Riail shows the matching rules without an explanation instead.

IS3329 Deliverable 2 · Ethan Nash · 124465124

## Quick start (no API key needed)

This runs Riail with the mock AI and simple word matching, so it needs no key and no model download.

```bash
python -m venv .venv
.venv\Scripts\activate              # macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env              # macOS / Linux: cp .env.example .env
```

Open `.env` and set:

```
RIAIL_ANSWERER=mock
RIAIL_EMBEDDER=keyword
```

Then load the rules and start the app:

```bash
python -m riail.ingestion.load_rules
python app.py
```

Open http://127.0.0.1:5000. The loader should print:

```
Loaded 48 rules for Club game: current rules
Loaded 50 rules for College game: 2026 trial rules
```

Mock answers start with `[Mock AI answer]` and repeat the best-matching rule.

## Settings

All settings live in `.env`. It is listed in `.gitignore`, so your API key is never committed, and the key is never sent to the browser.

| Setting | Options | What it does |
| --- | --- | --- |
| `RIAIL_ANSWERER` | `llm`, `mock`, `mock_fail` | `llm` uses the real AI (Groq). `mock` gives fixed answers with no key. `mock_fail` pretends the AI is down, to show the fallback. |
| `RIAIL_LLM_API_KEY` | your key | Needed only for `llm`. Free key from https://console.groq.com/keys |
| `RIAIL_EMBEDDER` | `local`, `keyword` | How rules are matched to questions. `local` uses a small AI model that understands meaning (downloads about 80 MB once). `keyword` only matches shared words. |
| `RIAIL_MIN_SCORE` | 0 to 1 (default 0.3) | Matches scoring below this are ignored. |
| `RIAIL_MAX_RESULTS` | number (default 4) | The most rules passed to the AI per question. |

**For real AI answers**, set `RIAIL_ANSWERER=llm` and add your key. **For better matching**, set `RIAIL_EMBEDDER=local`. Run `python -m riail.ingestion.load_rules` again whenever you change `RIAIL_EMBEDDER` or edit a rule file.

## Tests

```bash
pytest
```

All tests run offline. The AI is replaced by a mock or a fake web reply, and matching uses the keyword method, so no key or download is needed and the results are the same every run.

| Test file | What it checks |
| --- | --- |
| `test_models.py` | Rules need a number and text; the `/ask` reply has the agreed shape |
| `test_embedding.py` | Text becomes the same numbers every time; similar text scores higher |
| `test_rulestore.py` | Searches never return the other rulebook; re-adding a rule replaces it |
| `test_ingestion.py` | The real rule files are valid; the trial overlay works; bad files are rejected and leave the old rules in place |
| `test_retriever.py` | Weak matches are dropped; no match means "not covered" |
| `test_answerer.py` | Missing or invented citations are rejected; timeouts, usage limits and bad replies are handled; prompt injection stays in the question; the key stays in the auth header |
| `test_query.py` | Not covered, the AI-failure fallback, the wrong-rulebook guard; the question is never logged |
| `test_feedback.py` | Only "up" or "down" ratings are accepted; no personal data is stored |
| `test_gateway.py` | Empty, too-long and badly formed requests are rejected; the key never reaches the browser |
| `test_architecture.py` | Only `wiring.py` picks the real implementations; only the AI component makes web calls |

## How it works

When a question comes in:

1. The **gateway** (`riail/gateway/`) checks the input: a question of up to 500 characters and a valid rulebook.
2. The **query service** (`riail/query/`) asks the **retriever** (`riail/retrieval/`) for matching rules from the chosen rulebook.
3. The retriever searches the **rule store** (`riail/rulestore/`, a Chroma database in `instance/`). The store uses an **embedder** (`riail/embedding/`) to turn text into numbers so similar meanings can be found. The retriever keeps only matches scoring at least `RIAIL_MIN_SCORE`.
4. No matches means the answer is "not covered". Otherwise the **answerer** (`riail/answer/`) asks the AI to explain the rules, and the answer is checked so it only cites rules that were found.
5. If the AI fails, the query service shows the matching rules instead. Either way, the **feedback log** (`riail/feedback/`) records the outcome without the question text, and users can rate the answer with 👍 or 👎.

Each component talks to the others only through the contract in its `interface.py`. `riail/wiring.py` is the one place that decides which real class sits behind each contract, which is why swapping the mock AI for the real one is just a setting. Shared data types (`RuleChunk`, `Answer`, `RuleSet`, `AnswerStatus`) are in `riail/models.py`.

| Component | Folder | Prototype version |
| --- | --- | --- |
| Web page | `riail/client/` | One HTML page |
| API gateway | `riail/gateway/` | Flask routes with input checks |
| Query service | `riail/query/` | `QueryService` |
| Retriever | `riail/retrieval/` | `VectorRetriever` |
| Answerer (AI) | `riail/answer/` | `LLMAnswerer` (Groq), `MockAnswerer` |
| Rule store | `riail/rulestore/` | `ChromaRuleStore` (local file) |
| Embedder | `riail/embedding/` | `LocalModelEmbedder`, `KeywordEmbedder` |
| Ingestion | `riail/ingestion/` | One-off loading script |
| Feedback log | `riail/feedback/` | `FileFeedbackLog` (one JSON line per event) |

### Web API

- `POST /ask` takes `{"question": "...", "rule_set": "current" | "trial_2026"}` and returns `{"answer_id", "status": "ok" | "not_covered" | "fallback", "rule_set", "rule_set_label", "answer", "citations", "rules"}`.
- `POST /feedback` takes `{"answer_id": "...", "rating": "up" | "down"}` and returns `{"ok": true}`.
- Bad input gets HTTP 400 with an `error` message.

## About the rule data

The rules in `data/rules/` are **plain-English summaries written for this prototype, not the official GAA wording**. Rule numbers follow the Official Guide Part 2 (edition in force from 10 March 2025, plus the 2026 dissent change). The 2026 trial rules come from news reports, because the full official text could not be found. Every rule shows its source and the date it took effect.

`trial_2026.json` lists only the changes. When the rules are loaded, every current rule the trial does not change is copied into the trial rulebook, so a college referee sees the full set: a trial rule with the same number replaces the current one, and trial-only rules (T1, T2) are added.

**Riail gives guidance only. Do not rely on it for a real decision; check the Official Guide.**
