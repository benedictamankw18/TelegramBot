# N3thunt3r Telegram Bot

This repository contains the N3thunt3r Telegram bot and its hire-enquiry flow.
The same Telegram application supports local polling and Render webhooks.

## Architecture

- `bot.py` contains the handlers, conversation flow, owner notifications, and
  `build_application()`.
- `database.py` uses PostgreSQL when `DATABASE_URL` is set and SQLite otherwise.
- `webhook_server.py` runs the aiohttp HTTP server used by Render.
- `render.yaml` describes the production web service.

## Prerequisites

- Python 3.11 or newer
- A Telegram bot token from BotFather
- For production: a Neon PostgreSQL database and a Render account

## Local installation and polling

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set `BOT_TOKEN` and, optionally, `OWNER_CHAT_ID` in `.env`. With no
`DATABASE_URL`, the bot stores local data in `n3thunt3r.db` (or `DB_PATH`).
Start polling with:

```powershell
python bot.py
```

Do not run polling at the same time as the production webhook.

## Configuration

| Variable | Required | Purpose |
|---|---:|---|
| `BOT_TOKEN` | Yes | Telegram BotFather token |
| `OWNER_CHAT_ID` | No | Chat receiving new/cancelled enquiry alerts |
| `DATABASE_URL` | Production | Neon PostgreSQL connection string |
| `DB_PATH` | No | Alternate SQLite path for local development |
| `WEBHOOK_SECRET` | Webhook | Secret checked against Telegram's header |
| `WEBHOOK_URL` | No | Full public webhook base URL; otherwise Render's URL is used |
| `PORT` | No | HTTP port; Render supplies this automatically |
| `RENDER_EXTERNAL_URL` | Render | Used automatically when `WEBHOOK_URL` is blank |

`OWNER_CHAT_Secert_ID` is not used by the source code and is intentionally not
included. Only `OWNER_CHAT_ID` is needed for owner notifications.

## Neon PostgreSQL

Create a Neon project and copy its pooled or direct connection string from the
Neon dashboard. Store it as `DATABASE_URL` in Render's environment settings,
not in source control. Neon connection strings normally include SSL settings;
psycopg supports them directly. Schema initialization is safe to run repeatedly.

Existing SQLite records are not automatically migrated or deleted. Export the
`enquiries` rows from `n3thunt3r.db` and import them into the Neon `enquiries`
table before switching production traffic. Preserve `id`, `user_id`, timestamps,
and statuses if users must retain their existing enquiry numbers.

## Render deployment

1. Push the `development` branch (or a deployment branch) to GitHub.
2. In Render, create a **Blueprint** from the repository, or create a Free Web
   Service manually.
3. Use build command `pip install -r requirements.txt` and start command
   `python webhook_server.py`.
4. Add these secrets manually in Render: `BOT_TOKEN`, `DATABASE_URL`, and a
   strong random `WEBHOOK_SECRET`. Add `OWNER_CHAT_ID` if owner alerts are
   wanted. `WEBHOOK_URL` is optional; leave it empty to derive the URL from
   `RENDER_EXTERNAL_URL`.
5. Deploy and wait for `/health` to report `{"status":"ok","telegram":true}`.

The server binds to `0.0.0.0`, registers
`<public-url>/telegram/webhook`, validates Telegram's
`X-Telegram-Bot-Api-Secret-Token` header, and places valid updates in the
python-telegram-bot update queue. Render's free service can sleep after
inactivity, so the first webhook request after sleeping may be delayed.

Check service logs in Render for startup, database, webhook registration, and
Telegram API errors. A missing `BOT_TOKEN`, `WEBHOOK_SECRET`, or database
connection is reported as a startup failure rather than being silently ignored.

## Health and webhook checks

```powershell
curl https://YOUR-RENDER-DOMAIN.onrender.com/health
```

Telegram should call the registered `/telegram/webhook` endpoint. A request
without the configured secret receives HTTP 401; malformed JSON receives HTTP
400. Send `/start` to the bot and confirm the response and the Render logs.
Telegram's `getWebhookInfo` (via Bot API tools) can also confirm the URL and
recent delivery errors.

## Commands

The bot preserves `/start`, `/about`, `/services`, `/projects`, `/skills`,
`/portfolio`, `/github`, `/contact`, `/ask`, `/help`, `/myhires`, `/cancelhire`,
`/cancelall`, `/myid`, and `/hire`, including the multi-step hire conversation.
`/cancel` stops an in-progress enquiry without saving it.

## Testing

Run syntax checks with:

```powershell
python -m compileall bot.py database.py webhook_server.py
```

Tests should use a fake Telegram token and temporary SQLite database. No real
Telegram token or production database is required for local validation.
