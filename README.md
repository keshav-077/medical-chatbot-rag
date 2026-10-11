<div align="center">

<img src="docs/brand/bloom-logo.svg" width="120" alt="bloom animated logo"/>

# bloom

### India-first health companion · cited answers · care nearby · Telegram

<br/>

<table>
<tr>
<td align="center" width="50%">

### 🌐 Live website

<a href="https://dwa21x631l5fr.cloudfront.net">
<img src="https://img.shields.io/badge/OPEN_LIVE_APP-FF4D8D?style=for-the-badge&labelColor=E3256B&color=FF4D8D&logo=amazonaws&logoColor=white" height="56" alt="Open live app"/>
</a>

<br/>

**https://dwa21x631l5fr.cloudfront.net**

</td>
<td align="center" width="50%">

### 💬 Telegram bot

<a href="https://t.me/bloom531134_bot">
<img src="https://img.shields.io/badge/CHAT_ON_TELEGRAM-2AABEE?style=for-the-badge&logo=telegram&logoColor=white" height="56" alt="Telegram bot"/>
</a>

<br/>

**[@bloom531134_bot](https://t.me/bloom531134_bot)**

</td>
</tr>
</table>

<br/>

| | Link |
|---|---|
| **Production URL** | [dwa21x631l5fr.cloudfront.net](https://dwa21x631l5fr.cloudfront.net) |
| **Telegram webhook** | `https://dwa21x631l5fr.cloudfront.net/api/telegram` |
| **Google OAuth redirect** | `https://dwa21x631l5fr.cloudfront.net/calendar/callback` |
| **Health check** | […/health](https://dwa21x631l5fr.cloudfront.net/health) |
| **AWS region** | `ap-southeast-2` (Sydney) |
| **GitHub** | [keshav-077/medical-chatbot-rag](https://github.com/keshav-077/medical-chatbot-rag) |

<br/>

<img src="docs/brand/bloom-mark.svg" width="28" alt="bloom mark"/> **Tab icon** — five-petal bloom mark (same identity as the animated logo)

[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask_3-000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-supervisor-121212?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![AWS](https://img.shields.io/badge/AWS-ECS_%2B_CloudFront-232F3E?style=flat-square&logo=amazonaws&logoColor=white)](https://aws.amazon.com)
[![Neon](https://img.shields.io/badge/Neon-Postgres-00E599?style=flat-square)](https://neon.tech)
[![Pinecone](https://img.shields.io/badge/Pinecone-1024--d-000?style=flat-square)](https://pinecone.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

> **Disclaimer:** bloom is for **education and navigation**, not diagnosis or prescribing. In an emergency, call **112**, **108**, or Tele-MANAS **14416**.

---

## Demo preview

<p align="center">
  <img src="docs/demo-preview.svg" width="720" alt="Animated demo preview of bloom chat"/>
</p>

<p align="center">
  <a href="https://dwa21x631l5fr.cloudfront.net"><strong>Open the live app →</strong></a>
  &nbsp;·&nbsp;
  <a href="https://t.me/bloom531134_bot"><strong>Message on Telegram →</strong></a>
</p>

---

## What bloom does

| Module | What users get |
|--------|----------------|
| **Chat** | Safety triage first, then LangGraph-routed answers with citations when RAG is used |
| **Meds** | India monograph catalog — composition, warnings, interactions, freshness dates |
| **Care map** | Nearby hospitals, doctors, pharmacies (Google Places) |
| **Labs** | Upload PDF → plain-language explanation (not a diagnosis) |
| **Appointments** | Call script + reminder drafts (no clinic API booking) |
| **Voice** | Browser speech + Groq Whisper for uploads |
| **Telegram** | Same brain via [@bloom531134_bot](https://t.me/bloom531134_bot) |
| **Share / PDF** | Read-only share links and visit PDF export |

---

## Architecture (production)

<p align="center">
  <img src="docs/diagrams/architecture.svg" width="960" alt="AWS architecture diagram"/>
</p>

```text
Users / Telegram
       │
       ▼
 CloudFront (HTTPS)
       │
       ▼
 Application Load Balancer  ──►  /health
       │
       ▼
 ECS Fargate (Gunicorn → Flask → LangGraph)
       │
       ├── Neon Postgres (accounts, chats, meds, appointments)
       ├── Pinecone + Jina embeddings (1024-d RAG index)
       ├── OpenRouter (primary LLM) · Groq (fallback + Whisper)
       ├── Google Maps / Places · Calendar OAuth
       └── Langfuse traces (optional)
```

---

## System design (one chat turn)

<p align="center">
  <img src="docs/diagrams/system-design.svg" width="960" alt="LangGraph system design"/>
</p>

1. **Safety** — emergency patterns, India helplines, disclaimer  
2. **Intent** — general, medication, symptom, lab, care map, appointment  
3. **Specialist path** — tools (RAG, drugs JSON, Places, lab parser, …)  
4. **Verify** — citation check, dose guardrails, freshness badge  
5. **Persist** — message + `citations_json`, `risk_level`, `trace_id`  

---

## Tech stack

### Application

| Layer | Technology |
|-------|------------|
| Web | Flask 3, Jinja2, Tailwind (CDN), Tabler icons |
| Auth | Flask-Login, Bcrypt, Flask-Limiter |
| Orchestration | **LangGraph** supervisor graph |
| RAG | LangChain retriever → Pinecone `medicalbot` |
| Embeddings | **Jina** `jina-embeddings-v3` (**1024-d only**) |
| LLM | **OpenRouter** (primary), **Groq** (fallback) |
| Voice | Web Speech API + **Groq Whisper** (uploads) |
| PDF | ReportLab (visit export) |
| Observability | Langfuse, optional OpenTelemetry |

### Data & content

| Store | Role |
|-------|------|
| **Neon PostgreSQL** | Users, conversations, health profile, meds, favorites, labs |
| **Pinecone** | Medical book / document vectors |
| **Local JSON** | India drug monographs + safety notices (ingest pipeline) |

### Infrastructure (live)

| Service | Use |
|---------|-----|
| **Amazon ECR** | Container image `bloom:latest` |
| **Amazon ECS Fargate** | Service `bloom-web`, port **8080** |
| **Application Load Balancer** | HTTP → targets |
| **Amazon CloudFront** | Public HTTPS URL |
| **CloudWatch Logs** | `/ecs/bloom` |

App Runner is blocked by org SCP on this account; ECS + ALB + CloudFront is the production path.

---

## Brand assets

| File | Use |
|------|-----|
| [`static/brand/bloom-logo.svg`](static/brand/bloom-logo.svg) | Animated logo (README + site) |
| [`static/favicon.svg`](static/favicon.svg) | Browser tab identity mark |
| [`docs/brand/bloom-mark.svg`](docs/brand/bloom-mark.svg) | Same mark for docs |

The web app uses the **same animated SVG** in headers and on the sign-in card ([`templates/partials/bloom_logo.html`](templates/partials/bloom_logo.html)).

---

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open [http://localhost:8080](http://localhost:8080). Required: `PINECONE_API_KEY`, `JINA_API_KEY`, and `OPENROUTER_API_KEY` or `GROQ_API_KEY`.

```powershell
pytest tests/evals/test_platform.py
```

---

## Deploy to AWS

```powershell
.\deploy\aws.ps1
```

Then update the ECS service (or use your CI) so `bloom-web` pulls the new image. Set production env vars on the task — never bake `.env` into the image.

| Variable | Required in prod |
|----------|------------------|
| `FLASK_ENV=production` | Yes |
| `SECRET_KEY` | Yes |
| `DATABASE_URL` | Yes (Neon pooled URL) |
| `PINECONE_API_KEY`, `JINA_API_KEY` | Yes |
| `OPENROUTER_API_KEY` or `GROQ_API_KEY` | Yes |
| `APP_URL` | Set to your CloudFront URL |
| Maps, OAuth, Telegram, Langfuse | Optional but enabled on live |

---

## Project layout

```text
app.py                 Flask routes + health
orchestration/         LangGraph graphs (main supervisor)
tools/                 RAG, drugs, places
routes/platform.py     Map, meds, labs, calendar, telegram, worker
services/              voice, calendar, langfuse, storage, pdf
ingestion/             India medicine seed pipeline
deploy/aws.ps1         Build + push ECR (Sydney)
templates/             UI (clay / organic care theme)
tests/evals/           Platform eval cases
```

---

## License

MIT — see [LICENSE](LICENSE).

<div align="center">

**[Live app](https://dwa21x631l5fr.cloudfront.net)** · **[Telegram](https://t.me/bloom531134_bot)** · **[Health](https://dwa21x631l5fr.cloudfront.net/health)**

© 2026 bloom — Empowering healthcare with empathic companions

</div>
