<div align="center">

# Citer

**Ask natural-language questions about any codebase and get precise, cited answers with file and line references.**

Multi-turn, agentic, and evaluated.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](backend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](backend/app)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](frontend/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](frontend/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C.svg)](backend/app/agent)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)](backend/migrations)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF.svg)](.github/workflows/ci.yml)

</div>

## What is Citer?

Citer is an agentic codebase Q&A tool. Point it at any GitHub repository, and it clones, parses, and embeds the source so you can ask questions like *"Where is authentication handled?"* — and get answers backed by **exact file + line citations**, not hallucinations.

The pipeline is a LangGraph agent: **planner → retriever tools → synthesizer**, grounded in a hybrid retrieval layer that fuses vector search, full-text search, and symbol-level matching (RRF).

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (React, TypeScript) |
| Backend | Python FastAPI |
| Agent | LangGraph (planner → tools → synthesis loop) |
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-large |
| Vector DB | PostgreSQL + pgvector |
| Search | Hybrid: vector + PostgreSQL FTS + symbol match (RRF fusion) |
| Cache | Redis (semantic cache) |
| Observability | LangSmith |
| Deploy | Docker Compose |

## Quick Start

```bash
cp .env.example .env   # fill in keys
docker compose up -d   # postgres + redis

# backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

Open the chat UI at `http://localhost:3000`, index a repository, and start asking questions.

## Repo Layout

```
├── backend/                 FastAPI service
│   ├── app/
│   │   ├── api/routes/      /index /ask /sessions /eval
│   │   ├── core/            config, logging
│   │   ├── db/              models, queries, session mgmt
│   │   ├── ingestion/       clone → parse → chunk → embed → store
│   │   ├── retrieval/       hybrid: vector + keyword + symbol
│   │   ├── agent/           LangGraph state, nodes, tools, prompts
│   │   ├── cache/           Redis semantic cache
│   │   ├── eval/            golden dataset, runner, metrics, report
│   │   └── schemas/         Pydantic request/response models
│   ├── migrations/          SQL schema + pgvector index
│   ├── scripts/             CLI: index a repo, run eval
│   └── tests/               ingestion, retrieval, agent
├── frontend/                Next.js app
│   ├── app/chat/            streaming chat UI + citations
│   ├── app/eval/            eval dashboard
│   ├── components/          markdown, SSE reader
│   └── lib/                 API client
├── data/                    local repo clones / cache
└── docker-compose.yml       postgres + redis
```

## Roadmap

- **Backbone:** DB + Docker, ingestion pipeline, hybrid retrieval, LangGraph agent, `/ask` streaming.
- **Product:** Next.js chat UI + citations, sessions & multi-turn, semantic cache, eval harness + dashboard, deploy.

## License

[MIT](LICENSE)