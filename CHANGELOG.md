# Changelog

## [2.0.0] - 2026-06-15

### 🚀 Major: Serverless Transformation

Complete rewrite for 100% free, serverless-ready deployment on Vercel and other platforms.

### ⚠️ Breaking Changes
- **Pinecone index dimension changed**: 384 → 768. You MUST delete and recreate the `medicalbot` index, then re-run `store_index.py`.
- **Embeddings**: Switched from local `sentence-transformers` (1.5GB) to API-based Jina AI + HuggingFace Inference.
- **Database**: SQLite replaced with Neon PostgreSQL for production. SQLite remains as local dev fallback.
- **New environment variables required**: `JINA_API_KEY`, `DATABASE_URL` (production), `GROQ_API_KEY` (optional).

### Added
- `src/embeddings.py` — Multi-provider API embedding system (Jina AI primary, HuggingFace backup)
- `src/llm_providers.py` — Multi-LLM system (OpenRouter primary, Groq backup)
- `config.py` — Environment-based configuration (dev/production)
- `api/index.py` — Vercel serverless entry point
- `vercel.json` — Vercel deployment configuration
- `.vercelignore` — Exclude unnecessary files from deployment
- `runtime.txt` — Python version specification for Vercel
- `migrate_to_postgres.py` — One-time SQLite → Neon PostgreSQL migration script
- Rate limiting via Flask-Limiter (20 req/min on chat endpoint)
- Health check endpoint at `/health`
- Structured logging (console-based, serverless-friendly)
- Error handlers for 429 and 500 status codes

### Changed
- `requirements.txt` — Complete rewrite with correct, compatible versions
- `app.py` — Refactored for config system, API embeddings, LLM manager, production features
- `models.py` — Fixed deprecated `datetime.utcnow` usage
- `store_index.py` — Uses API embeddings, dimension updated to 768
- `src/helper.py` — Backward-compatible wrapper around new embedding system
- `.env.example` — Updated with all new environment variables
- `test_setup.py` — Updated for new provider system
- `Dockerfile` — Updated for new dependencies

### Removed
- `sentence-transformers` dependency (saved ~1.5GB)
- `torch` dependency (no longer needed)
- `langchain_experimental` (unused)
- `grpcio-tools`, `protobuf`, `googleapis-common-protos` (unnecessary transitive deps)
- `setup.py` (incompatible with Vercel's `-e .`)
- Local model downloads (all embeddings now API-based)
- Gemini Flash LLM (not needed)
- HuggingFace local LLM backup (not needed)

### Security
- Session cookies: HTTPOnly, SameSite=Lax, Secure (production)
- Rate limiting on all endpoints
- Input sanitization (existing, preserved)
- Environment-based secret key management

## [1.0.0] - Previous

Initial release with local sentence-transformers, SQLite, and OpenRouter LLM.
