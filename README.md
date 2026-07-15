# Lead Qualification & Outreach Agent

A production-ready, AI-powered lead qualification system that automatically enriches, scores, classifies, and drafts personalized outreach emails for B2B leads, with a mandatory human approval gate before any email is sent.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React     │────▶│   FastAPI    │────▶│   LangGraph  │────▶│    Tools     │
│   Frontend  │     │   Backend    │     │   Workflow   │     │ (Enrichment, │
│  (ShadCN)   │◀────│  (REST API)  │◀────│  (Agent)     │◀────│  Scoring,    │
└─────────────┘     └──────────────┘     └──────────────┘     │  Email, etc) │
                                                               └──────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │   SQLite DB  │
                              │  (Lead Data, │
                              │   Audit Logs)│
                              └──────────────┘
```

## Workflow

```
Lead Receive → Enrichment → Identity-Blind Scoring → Classification → Routing
                                                                          │
                                                    ┌─────────────────────┘
                                                    │
                                              ┌─────┴─────┐
                                              │           │
                                           HOT       NURTURE/DISQUALIFY
                                              │           │
                                         Draft Email    Archive/Nurture
                                              │
                                        Human Approval
                                              │
                                     ┌────────┴────────┐
                                     │                 │
                                  Approve           Reject
                                     │
                                  Send Email
                                     │
                                 Audit Log
```

## Features

### Agent Workflow (LangGraph)
- **Lead Enrichment**: Extracts company info, industry, role, buying signals, technology stack, funding, etc.
- **Identity-Blind Scoring**: Strips name, gender, race, nationality, religion before scoring for fairness
- **Classification**: HOT (≥80), NURTURE (50-79), DISQUALIFY (<50)
- **Smart Routing**: HOT → Email draft, NURTURE → Pipeline, DISQUALIFY → Archive
- **Personalized Email Drafting**: AI-generated first-touch emails grounded in enrichment data
- **Human Approval Gate**: Mandatory approval before any email can be sent

### Governance
- **Identity-Blind Scoring**: Removes all personal identifiers before scoring
- **Prompt Injection Defense**: Detects and rejects malicious instructions like "Ignore previous instructions", "Mark me HOT"
- **Human Gate**: No outbound email without explicit human approval
- **Audit Log**: Complete trail of every prompt, response, decision, and action

### Tech Stack
- **Frontend**: React, TypeScript, TailwindCSS, ShadCN UI
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Agent Framework**: LangGraph
- **LLM**: OpenRouter API (GPT-4.1 Mini default, supports Gemini & Claude)
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: ChromaDB

## Project Structure

```
lead-qualification-agent/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── workflow.py          # LangGraph orchestration
│   │   ├── api/
│   │   │   └── routes.py            # FastAPI endpoints
│   │   ├── tools/
│   │   │   ├── enrichment_tool.py   # Lead enrichment
│   │   │   ├── scoring_tool.py      # Identity-blind scoring
│   │   │   ├── classification_tool.py # HOT/NURTURE/DISQUALIFY
│   │   │   ├── email_tool.py        # Drafting & sending
│   │   │   ├── crm_tool.py          # CRM write operations
│   │   │   └── audit_logger.py      # Audit trail logging
│   │   ├── evaluation/
│   │   │   └── test_suite.py        # Automated evaluation tests
│   │   ├── config.py                # Settings & environment
│   │   ├── database.py              # SQLAlchemy models & DB
│   │   ├── llm_client.py            # OpenRouter LLM client
│   │   └── main.py                  # FastAPI application entry
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Analytics overview
│   │   │   ├── LeadQueue.tsx        # Filterable lead list
│   │   │   ├── LeadDetail.tsx       # Full lead detail + approval
│   │   │   ├── AuditLogs.tsx        # Audit trail viewer
│   │   │   └── EvaluationDashboard.tsx # Test results
│   │   ├── lib/
│   │   │   └── api.ts              # API client
│   │   ├── types/
│   │   │   └── lead.ts             # TypeScript interfaces
│   │   └── App.tsx                  # Main app with routing
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── tailwind.config.js
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenRouter API Key (free tier available at https://openrouter.ai/)
- OpenAI API Key (for embeddings)

### Quick Start (Local)

1. **Clone and navigate to the project**:
   ```bash
   cd lead-qualification-agent
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your OpenRouter API key
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Setup

```bash
# Set environment variables
export OPENROUTER_API_KEY=your-key-here
export OPENAI_API_KEY=your-key-here

# Start all services
docker-compose up --build
```

## API Endpoints

### Leads
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/leads` | Submit a new lead for qualification |
| GET | `/api/v1/leads` | List all leads (supports filtering) |
| GET | `/api/v1/leads/{id}` | Get lead details |

### Approval
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/leads/{id}/approve` | Approve email for sending |
| POST | `/api/v1/leads/{id}/reject` | Reject email |
| POST | `/api/v1/leads/{id}/edit-email` | Edit & approve email |
| POST | `/api/v1/leads/{id}/send` | Send approved email |

### Analytics & Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics` | Dashboard analytics |
| GET | `/api/v1/audit-logs` | Audit trail |
| POST | `/api/v1/evaluation/run` | Run evaluation tests |
| GET | `/api/v1/evaluation/results` | Get evaluation results |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key for LLM calls |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for embeddings |
| `LLM_MODEL` | No | `openai/gpt-4o-mini` | LLM model to use |
| `DATABASE_URL` | No | `sqlite:///./lead_qualification.db` | Database URL |
| `DEBUG` | No | `false` | Enable debug mode |

## Evaluation Tests

The system includes 5 automated evaluation tests:

1. **Hot Lead Classification**: Verifies HOT leads get classified correctly and receive email drafts
2. **Disqualified Lead**: Verifies weak leads are disqualified and no email is drafted
3. **Approval Gate**: Verifies email is only sent after human approval
4. **Identity-Blind Fairness**: Verifies identical leads with different names get the same score
5. **Prompt Injection Defense**: Verifies injection attempts are detected and ignored

Run tests via the Evaluation Dashboard in the UI or via the API:
```bash
curl -X POST http://localhost:8000/api/v1/evaluation/run
```

## Governance & Compliance

- **Fairness**: Identity-blind scoring ensures no bias based on name, gender, race, nationality, or religion
- **Security**: Prompt injection defense protects against malicious inputs
- **Accountability**: Complete audit trail of every decision and action
- **Human Oversight**: Mandatory approval gate prevents unauthorized email sending
- **Data Privacy**: SQLite database with local storage, no external data sharing

## License

MIT