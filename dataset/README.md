# dataset/

Fixture data for demos, manual testing, and evaluation. Nothing here is
training data — FinAgent trains no models; it orchestrates a hosted LLM, a
sentence-transformer encoder, and live APIs.

| File | Rows | Purpose |
| :--- | ---: | :--- |
| `sample_startups.json` | 6 | Synthetic startup profiles spanning strong, mixed and weak cases. |
| `sample_cins.csv` | 10 | CINs covering the valid, malformed and struck-off paths. |
| `finscope_intents.jsonl` | 30 | Labelled messages for checking the intent router. |
| `sample_pitch_deck.md` | 1 | A pitch deck in text form, for the ingestion path. |
| `guardrail_probes.jsonl` | 20 | Prompts that must be blocked, and ones that must not. |

## Provenance

Every record is synthetic, written for this project. Company names, founders,
metrics and CINs are invented. Any resemblance to a real company is
coincidental, and the numbers should not be cited as market data.

The exception is `finscope_intents.jsonl`, which contains ordinary finance
questions phrased the way a retail investor would ask them — generic wording,
no attribution needed.

## Using them

```bash
# Register every sample startup
python - <<'PY'
import json, requests
for s in json.load(open("dataset/sample_startups.json")):
    r = requests.post("http://localhost:7860/startups", json=s)
    print(r.status_code, r.json().get("name"))
PY

# Check the intent router against its labels
python - <<'PY'
import json, requests
ok = total = 0
for line in open("dataset/finscope_intents.jsonl"):
    case = json.loads(line)
    got = requests.post("http://localhost:7860/finscope/chat",
                        json={"question": case["message"]}).json()["intent"]
    ok += got == case["intent"]; total += 1
    if got != case["intent"]:
        print(f"  {case['message'][:60]!r}: expected {case['intent']}, got {got}")
print(f"{ok}/{total} routed as labelled")
PY
```
