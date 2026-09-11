# API Reference

Base URL `http://localhost:7860`. Interactive docs at `/docs`, schema at
`/openapi.json`.

All bodies are JSON unless marked `multipart/form-data`.

---

## Startups

### `POST /startups` · 201

Register a startup.

```json
{
  "name": "QuantumFleet AI",
  "domain": "Logistics AI",
  "description": "Route optimisation for mid-size freight fleets.",
  "team": "Two ex-Flipkart supply-chain engineers.",
  "extras": "Stage: Seed. Raising $500k."
}
```

Only `name` is required. Legacy fields `startupId`, `idea`, `stage`, `teamSize`
and `fundingRequired` are accepted and normalised: `idea` becomes
`description`, and the other three fold into `extras`.

```json
{
  "startup_id": "3f2b...",
  "name": "QuantumFleet AI",
  "domain": "Logistics AI",
  "description": "Route optimisation for mid-size freight fleets.",
  "team": "Two ex-Flipkart supply-chain engineers.",
  "extras": "Stage: Seed. Raising $500k.",
  "created_at": "2026-09-11T09:14:22Z",
  "updated_at": "2026-09-11T09:14:22Z",
  "document_collections": []
}
```

| Also | |
| :--- | :--- |
| `PUT /startups/{id}` | Update any of `name`, `domain`, `description`, `team`, `extras`. 404 if unknown. |
| `GET /startups` | List all. |
| `GET /startups/{id}` | One startup. 404 if unknown. |
| `POST /api/startups/register` | Alias of `POST /startups`, for the Express-era frontend. |

---

## Documents

### `POST /startups/{id}/documents`

Ingest from a URL.

```json
{ "document_url": "https://example.com/pitch_deck.pdf" }
```

### `POST /api/startups/{id}/documents/upload` · `multipart/form-data`

Ingest an uploaded file. Field name: `documents`.

```bash
curl -X POST "$BASE/api/startups/$SID/documents/upload" -F "documents=@deck.pdf"
```

Both return:

```json
{
  "status": "success",
  "startup_id": "3f2b...",
  "collection_name": "startup_3f2b...",
  "chunks_stored": 47,
  "message": "Document processed and indexed (47 chunks)."
}
```

`collection_name` is `null` and the message says so when the vector store is
unavailable — the text is still held in memory and the startup remains
analysable.

| Status | Meaning |
| :--- | :--- |
| 400 | The URL could not be downloaded. |
| 404 | Unknown startup. |
| 422 | No readable text — typically a scanned deck with no OCR layer. |

---

## Verification

### `POST /startups/{id}/verify/mca`

```json
{ "cin": "U72900MH2021PTC123456" }
```

```json
{
  "startup_id": "3f2b...",
  "cin": "U72900MH2021PTC123456",
  "mca_verified": true,
  "company_status": "ACTIVE",
  "company_name": "QuantumFleet AI",
  "directors": ["Arjun Malhotra", "Dr. Elena Novak"],
  "name_match": true,
  "flags": [],
  "last_checked": "2026-09-11T09:20:04Z",
  "message": "Verification successful."
}
```

| Status | Meaning |
| :--- | :--- |
| 200 | Verified. `flags` may still list warnings. |
| 400 | Well-formed CIN, but the company is not active. **The result is still stored** so the report can cite it. |
| 422 | Malformed CIN — rejected locally, before any provider call. |

`flags`:

| Flag | Meaning |
| :--- | :--- |
| `MCA_NOT_VERIFIED` | No successful verification on record. |
| `NAME_MISMATCH` | The registered name differs from the submitted name. |
| `NO_DIRECTORS_FOUND` | The registry returned no directors. |
| `COMPANY_STATUS_<STATUS>` | The company is not `ACTIVE`. |

### `GET /startups/{id}/verify/mca`

Reads back the stored status without re-calling the provider. Use it for a UI
badge.

> **Sandbox** — without `MCA_API_KEY`, a CIN whose serial ends in `0` resolves
> to a struck-off company and everything else resolves to active. See
> `dataset/sample_cins.csv`.

---

## Reports

### `POST /reports/{id}` → `application/pdf`

Runs the full pipeline and streams the PDF. Takes 30–90 seconds. Registry flags
annotate the report; they never block it.

### `POST /api/startups/{id}/analyze`

Starts the same pipeline in the background.

```json
{ "status": "analysis_started", "id": "3f2b..." }
```

### `GET /api/startups/{id}/report/status`

```json
{
  "status": "complete",
  "analysis": {
    "executiveSummary": "...",
    "marketAnalysis": "...",
    "teamAssessment": "...",
    "riskFactors": "...",
    "recommendation": "...",
    "score": 8.5
  }
}
```

`status` is one of `not_started`, `processing`, `complete`, `failed`. When
`failed`, an `error` field carries the reason.

---

## Investor chat

### `POST /chat/{id}` · `POST /chat/by-name/{name}`

```json
{ "question": "What are the biggest risks for an investor here?" }
```

```json
{ "answer": "...", "startup_name": "QuantumFleet AI" }
```

Answers are grounded in the startup's profile and documents; the prompt
instructs the model to say when something is not stated rather than fill the
gap. Name lookup is case-insensitive and resolves duplicates to the most
recently registered startup.

---

## FinScope

### `POST /finscope/chat`

```json
{ "question": "What is an index fund?", "user_profile": "beginner", "session_id": "demo" }
```

```json
{ "answer": "...", "agent_used": "Financial Educator", "intent": "education" }
```

Returns 400 when the guardrail filter blocks the input — before any model runs.

### `POST /finscope/analyze-document` · `multipart/form-data`

Fields: `document` (file), `session_id`, `user_profile`. The extracted text is
cached against `session_id` so follow-up questions need no re-upload.

```json
{ "analysis": "[FLASHCARD]...", "agent_used": "Document Analyzer", "intent": "document" }
```

### `GET /api/finance-news/headlines?symbol=INFY:NSE&limit=10`

Raw headlines, no model in the loop. `limit` is clamped to 20. Returns
`{"headlines": []}` when `RAPIDAPI_KEY` is unset — it never errors.

---

## System

### `GET /health`

```json
{
  "status": "healthy",
  "service": "FinAgent",
  "version": "3.0.0",
  "qdrant_connected": true,
  "embeddings_ready": true,
  "llm_ready": true,
  "docling_ready": true,
  "startups_loaded": 3,
  "mca_api_configured": false
}
```

`status` stays `healthy` with degraded dependencies — the individual flags are
how you see that retrieval or document conversion is in fallback mode.

### Socket.IO `log_stream`

```js
const socket = io("http://localhost:7860");
socket.on("log_stream", (event) => console.log(event.message));
```

Every log record on the server, including agent progress.
