# FinAgent frontend

Next.js 16 investment workspace for the FinAgent FastAPI service.

## Run locally

Node.js 20.9 or newer is required.

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. The API is expected at `http://localhost:7860`
unless `NEXT_PUBLIC_API_BASE_URL` is changed.

## Connected backend capabilities

- Startup registration, listing, retrieval, and profile updates
- PDF/DOCX upload and public document URL ingestion
- MCA verification and stored verification status
- Background evaluation with status polling and synchronous PDF reports
- Grounded investor chat by startup ID or company name
- FinScope routed chat and session-aware document analysis
- Raw finance headlines
- Service health and live Socket.IO agent logs

## Commands

```bash
npm run dev
npm run lint
npm run build
```

The production image uses Next.js standalone output. From the repository root,
`docker compose up --build` starts the UI, API, and Qdrant together.
