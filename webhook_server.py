"""aiohttp entrypoint for running the Telegram bot on Render."""

import asyncio
import logging
import os
from typing import Any

from aiohttp import web
from telegram import Update

import bot
import database

logger = logging.getLogger("n3thunt3r.webhook")
WEBHOOK_PATH = "/telegram/webhook"
DEFAULT_PORT = 8080


def webhook_url() -> str:
    """Return the public webhook URL, normalizing a configured base URL."""
    base_url = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").strip()
    if not base_url:
        raise RuntimeError("WEBHOOK_URL or RENDER_EXTERNAL_URL must be configured")
    if base_url.rstrip("/").endswith(WEBHOOK_PATH):
        return base_url.rstrip("/")
    return f"{base_url.rstrip('/')}{WEBHOOK_PATH}"


def create_web_app(application: Any) -> web.Application:
    """Create the HTTP application without starting either server."""
    web_app = web.Application()
    web_app["telegram_application"] = application
    web_app["ready"] = False

    async def index(request: web.Request) -> web.Response:
        return web.Response(text="N3thunt3r Telegram bot is running.\n")

    async def health(request: web.Request) -> web.Response:
        ready = bool(request.app["ready"])
        return web.json_response(
            {"status": "ok" if ready else "starting", "telegram": ready},
            status=200 if ready else 503,
        )

    async def telegram_webhook(request: web.Request) -> web.Response:
        expected_secret = os.getenv("WEBHOOK_SECRET")
        received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not expected_secret or received_secret != expected_secret:
            return web.json_response({"error": "unauthorized"}, status=401)

        try:
            payload = await request.json()
            update = Update.de_json(payload, application.bot)
        except (ValueError, TypeError):
            return web.json_response({"error": "malformed JSON"}, status=400)
        except Exception:
            logger.exception("Could not parse Telegram webhook update")
            return web.json_response({"error": "invalid update"}, status=400)

        if update is None:
            return web.json_response({"error": "invalid update"}, status=400)

        try:
            await application.update_queue.put(update)
        except Exception:
            logger.exception("Could not queue Telegram webhook update")
            return web.json_response({"error": "service unavailable"}, status=503)
        return web.json_response({"ok": True})

    web_app.router.add_get("/", index)
    web_app.router.add_get("/health", health)
    web_app.router.add_post(WEBHOOK_PATH, telegram_webhook)
    return web_app


async def run_server() -> None:
    if not os.getenv("WEBHOOK_SECRET"):
        raise RuntimeError("WEBHOOK_SECRET must be configured for webhook mode")

    application = bot.build_application()
    database.init_db()
    await application.initialize()
    await bot.post_init(application)
    await application.start()

    runner = web.AppRunner(create_web_app(application))
    try:
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", DEFAULT_PORT)))
        await site.start()
        await application.bot.set_webhook(
            url=webhook_url(),
            secret_token=os.environ["WEBHOOK_SECRET"],
            allowed_updates=Update.ALL_TYPES,
        )
        runner.app["ready"] = True
        logger.info(
            "Webhook server is listening on 0.0.0.0:%s",
            os.getenv("PORT", DEFAULT_PORT),
        )
        await asyncio_event()
    finally:
        runner.app["ready"] = False
        await runner.cleanup()
        await application.stop()
        await application.shutdown()


async def asyncio_event() -> None:
    """Wait indefinitely until the process receives a shutdown signal."""
    await asyncio.Event().wait()


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=logging.INFO,
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
