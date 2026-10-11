<div align="center">

# Bloom

### India-first health companion. Cited answers, medicine context, and nearby care.

[![Live](https://img.shields.io/badge/Live-AWS_Sydney-0F6E56?style=for-the-badge)](https://dwa21x631l5fr.cloudfront.net)
[![Telegram](https://img.shields.io/badge/Telegram-bloom531134__bot-2AABEE?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/bloom531134_bot)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

<br/>

<a href="https://dwa21x631l5fr.cloudfront.net">
  <img src="https://img.shields.io/badge/Open_Bloom-0F6E56?style=for-the-badge&logo=amazonaws&logoColor=white" alt="Open Bloom" height="48"/>
</a>
&nbsp;
<a href="https://t.me/bloom531134_bot">
  <img src="https://img.shields.io/badge/Chat_on_Telegram-2AABEE?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram bot" height="48"/>
</a>

<br/>

**Site:** [https://dwa21x631l5fr.cloudfront.net](https://dwa21x631l5fr.cloudfront.net)

**Bot:** [https://t.me/bloom531134_bot](https://t.me/bloom531134_bot)

</div>

---

Bloom helps people in India understand health questions without pretending to be a doctor. Answers are educational, cited when they come from the library, and flagged when they sound urgent.

| | |
|---|---|
| Website | [dwa21x631l5fr.cloudfront.net](https://dwa21x631l5fr.cloudfront.net) |
| Telegram | [@bloom531134_bot](https://t.me/bloom531134_bot) |
| Webhook | `https://dwa21x631l5fr.cloudfront.net/api/telegram` |
| Region | Asia Pacific (Sydney) |
| Database | Neon Postgres |
| Search | Pinecone, 1024-d Jina embeddings |

> Bloom is not a diagnosis, a prescription, or a clinic booking system. Emergency symptoms should go to **112**, **108**, or Tele-MANAS **14416**.

---

## What you can do

| | |
|---|---|
| **Chat** | Ask a health question. Answers cite the library when retrieval is used, and a safety check runs first. |
| **Meds** | Look up composition, warnings, and interactions from the India monograph catalog, with a freshness date. |
| **Map** | Find nearby hospitals, doctors, and pharmacies. |
| **Labs** | Upload a lab PDF and get a plain-language explanation. |
| **Appointments** | Draft a call script and reminder. Bloom does not book the clinic for you. |
| **Voice** | Speak in the browser, or upload audio. Uploads are transcribed with Groq Whisper. |
| **Telegram** | Message [@bloom531134_bot](https://t.me/bloom531134_bot). The bot posts to the live site. |

---

## How it is built

```text
Browser / Telegram
        |
        v
Flask  -->  LangGraph supervisor
              |-- safety
              |-- intent
              |-- general / medication / symptom / lab / care / appointment
              |-- verify
        |
        +--> Pinecone (Jina 1024-d)
        +--> Neon Postgres
        +--> Google Places and Calendar
```

The container runs Gunicorn on ECS Fargate. CloudFront serves HTTPS. Secrets stay in the task environment, not in the image.

---

## Run it locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open [http://localhost:8080](http://localhost:8080).

Required keys in `.env`: `PINECONE_API_KEY`, `JINA_API_KEY`, and `OPENROUTER_API_KEY` or `GROQ_API_KEY`. See `.env.example` for maps, calendar, Langfuse, and Telegram. Do not commit `.env`.

Leave `DATABASE_URL` empty to use SQLite. Set it to the Neon pooled URL when you want the shared database.

---

## Deploy

The live service is account `061845526810` in `ap-southeast-2`.

```powershell
.\deploy\aws.ps1
```

That builds the image and pushes it to ECR. The running service is ECS service `bloom-web` on cluster `bloom`, behind the load balancer and CloudFront.

Production will not boot without `SECRET_KEY`, `DATABASE_URL`, `PINECONE_API_KEY`, `JINA_API_KEY`, and one model key.

After a new hostname exists, set:

- `APP_URL` to that HTTPS origin
- Google OAuth redirect to `https://<host>/calendar/callback`
- Telegram webhook to `https://<host>/api/telegram`

Current values:

- App: `https://dwa21x631l5fr.cloudfront.net`
- Calendar redirect: `https://dwa21x631l5fr.cloudfront.net/calendar/callback`
- Telegram webhook: `https://dwa21x631l5fr.cloudfront.net/api/telegram`

---

## License

MIT. See [LICENSE](LICENSE).
