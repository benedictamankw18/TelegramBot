"""
N3thunt3r Telegram Bot - Version 1

Features:
  - /start with a custom reply keyboard (main menu)
  - Commands and keyboard buttons that both work independently
  - A simple "Hire N3thunt3r" enquiry flow (no database yet)
  - Global error handler and unknown command/text handlers

Run with:  python bot.py
"""

import html
import logging
import os

from dotenv import load_dotenv
from telegram import BotCommand, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Setup: environment variables and logging
# ---------------------------------------------------------------------------

# Load variables from the .env file (BOT_TOKEN) into the environment.
load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
# The httpx library logs full request URLs, which contain the bot token.
# Keeping it at WARNING stops the token from appearing in your console.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("n3thunt3r")

# ---------------------------------------------------------------------------
# Configuration: edit the values below to change what the bot says
# ---------------------------------------------------------------------------

PORTFOLIO_URL = "http://n3thunt3r.me/portfolio/"
GITHUB_URL = "https://github.com/benedictamankw18"

# Replace this placeholder when you are ready to publish real contact details.
CONTACT_DETAILS = (
    "💬 <b>Telegram:</b> @Kali0Nethunter\n"
    '📢 <b>Telegram community:</b> <a href="https://t.me/n3thunt3rsocial">N3thunt3r Social</a>\n'
    '🟢 <b>WhatsApp:</b> <a href="https://wa.me/233594500785">Chat on WhatsApp</a>\n'
    "📞 <b>Phone:</b> +233594500785, +233550030318, +233543779868\n"
    '💼 <b>LinkedIn:</b> <a href="https://www.linkedin.com/in/benedict-amankwa-991a5635b/">Benedict Amankwa Osei</a>\n'
    '🐙 <b>GitHub:</b> <a href="https://github.com/benedictamankw18">benedictamankw18</a>'
)

OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")

# Keyboard button labels (defined once so keyboard and handlers always match).
BTN_ABOUT = "👤 About"
BTN_SERVICES = "🛠 Services"
BTN_PROJECTS = "💻 Projects"
BTN_SKILLS = "🧠 Skills"
BTN_PORTFOLIO = "🌐 Portfolio"
BTN_GITHUB = "🐙 GitHub"
BTN_CONTACT = "📩 Contact"
BTN_HIRE = "🚀 Hire N3thunt3r"
BTN_HELP = "❓ Help"

# The main menu: a persistent reply keyboard that fits desktop and mobile.
MAIN_MENU = ReplyKeyboardMarkup(
    [
        [BTN_ABOUT, BTN_SERVICES],
        [BTN_PROJECTS, BTN_SKILLS],
        [BTN_PORTFOLIO, BTN_GITHUB],
        [BTN_CONTACT, BTN_HIRE],
        [BTN_HELP],
    ],
    resize_keyboard=True,  # keeps the buttons a comfortable size
    is_persistent=True,  # keeps the keyboard visible
    input_field_placeholder="Choose an option from the menu...",
)

# Maximum characters stored per enquiry field (keeps messages under Telegram's limit).
MAX_NAME_LENGTH = 100
MAX_NEED_LENGTH = 300
MAX_DESCRIPTION_LENGTH = 1000

# ---------------------------------------------------------------------------
# Message texts (HTML formatting)
# ---------------------------------------------------------------------------

WELCOME_TEXT = (
    "👋 <b>Welcome to N3thunt3r!</b>\n\n"
    "I'm the N3thunt3r technology assistant.\n\n"
    "Explore my services, projects, technical skills, portfolio, "
    "or contact me about a project.\n\n"
    "What would you like to explore?"
)

ABOUT_TEXT = (
    "👤 <b>About N3thunt3r</b>\n\n"
    "N3thunt3r is the personal technology and developer brand of "
    "<b>Benedict Amankwa Osei</b>.\n\n"
    "The focus areas are:\n"
    "• Full-stack web development\n"
    "• Software development\n"
    "• Cybersecurity and ethical hacking\n"
    "• Backend and database systems\n"
    "• AI and emerging technologies\n"
    "• Custom digital solutions\n"
    "• Technology research and innovation"
)

SERVICES_TEXT = (
    "🛠 <b>Services</b>\n\n"
    "• Web Application Development\n"
    "• Software Development\n"
    "• Backend/API Development\n"
    "• Database Systems\n"
    "• Cybersecurity\n"
    "• Automation\n"
    "• AI-Powered Solutions\n"
    "• Custom Digital Solutions\n\n"
    "Interested? Tap <b>🚀 Hire N3thunt3r</b> or send /hire."
)

PROJECTS_TEXT = (
    "💻 <b>Projects</b>\n\n"
    "• <b>Multi-Shop POS</b> - a point-of-sale system for multiple shops\n"
    "• <b>Multi-Shop Inventory</b> - an inventory management system for multiple shops\n"
    "• <b>Dementia Care Mobile Application</b> - Design and Development of a Dementia Care Mobile Application for Patient and Caregiver Support\n"
    "• <b>AgriSmart AI</b> - an AI project in the agriculture space\n"
    "• <b>DementiaCareApp</b> - an application focused on dementia care\n"
    "• <b>School LMS</b> - a learning management system for schools\n"
    "• <b>Other projects</b> - more software and technology work\n\n"
    f"See more on the portfolio: {PORTFOLIO_URL}\n"
    f"or on GitHub: {GITHUB_URL}"
)

SKILLS_TEXT = (
    "🧠 <b>Skills &amp; Technologies</b>\n\n"
    "<b>Languages:</b> JavaScript, TypeScript, Python, PHP, Java, C#, HTML/CSS\n"
    "<b>Frameworks &amp; runtimes:</b> React, Node.js\n"
    "<b>Databases &amp; platforms:</b> MySQL, Firebase\n"
    "<b>Tools:</b> Git/GitHub\n"
    "<b>Security:</b> Cybersecurity"
)

PORTFOLIO_TEXT = f"🌐 <b>Portfolio</b>\n\nView my work here:\n{PORTFOLIO_URL}"

GITHUB_TEXT = f"🐙 <b>GitHub</b>\n\nBrowse my code and repositories:\n{GITHUB_URL}"

CONTACT_TEXT = (
    "📩 <b>Contact N3thunt3r</b>\n\n"
    "For project enquiries, collaboration, or technical discussions, "
    "please use any of the channels below.\n\n"
    f"{CONTACT_DETAILS}\n\n"
    "Or tap <b>🚀 Hire N3thunt3r</b> to send a quick project enquiry."
)

ASK_TEXT = (
    "🤖 <b>Ask N3thunt3r</b>\n\n"
    "The AI assistant will be added in a future version.\n"
    "For now, use the menu to explore services, projects, and skills."
)

HELP_TEXT = (
    "❓ <b>Help</b>\n\n"
    "You can use the menu buttons or type a command:\n\n"
    "/start - Show the main menu\n"
    "/myid - Show your Telegram user ID\n"
    "/about - About N3thunt3r\n"
    "/services - Services offered\n"
    "/projects - Project examples\n"
    "/skills - Technologies and skills\n"
    "/portfolio - Portfolio link\n"
    "/github - GitHub profile\n"
    "/contact - Contact information\n"
    "/hire - Start a project enquiry\n"
    "/ask - AI assistant (coming soon)\n"
    "/help - Show this help message\n"
    "/cancel - Cancel the current enquiry"
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def reply(update: Update, text: str, with_menu: bool = True) -> None:
    """Send an HTML-formatted reply, optionally attaching the main menu."""
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=MAIN_MENU if with_menu else None,
    )


# ---------------------------------------------------------------------------
# Command / button handlers (each one works from a command OR a button)
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, WELCOME_TEXT)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, ABOUT_TEXT)


async def services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, SERVICES_TEXT)


async def projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, PROJECTS_TEXT)


async def skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, SKILLS_TEXT)


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, PORTFOLIO_TEXT)


async def github(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, GITHUB_TEXT)


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, CONTACT_TEXT)


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder: an AI assistant can be connected here in a later version.
    await reply(update, ASK_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, HELP_TEXT)

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tells you your chat ID so you can set OWNER_CHAT_ID in .env."""
    await reply(
        update,
        f"Your chat ID is: <code>{update.effective_chat.id}</code>",
    )

# ---------------------------------------------------------------------------
# Hire flow: a small step-by-step conversation
#   1. name  ->  2. what they need  ->  3. short project description
# ---------------------------------------------------------------------------

ASK_NAME, ASK_NEED, ASK_DESCRIPTION = range(3)


def save_enquiry(enquiry: dict) -> None:
    """
    Store a completed enquiry.

    Version 1 only logs it. Later, replace the body of this function with
    a database insert (SQLite, MySQL, PostgreSQL, Firebase, ...). The rest
    of the bot does not need to change.
    """
    logger.info("New enquiry received: %s", enquiry)

def describe_sender(update: Update) -> str:
    """Return a clickable description of who sent the enquiry."""
    user = update.effective_user
    if user is None:
        return "Unknown user"
    name = html.escape(user.full_name)
    handle = f"@{html.escape(user.username)}" if user.username else "no username"
    return f'<a href="tg://user?id={user.id}">{name}</a> ({handle}, ID: {user.id})'


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    """Send an alert to the bot owner. Returns True if it was delivered."""
    if not OWNER_CHAT_ID:
        logger.warning("OWNER_CHAT_ID is not set, so no owner notification was sent.")
        return False
    try:
        await context.bot.send_message(
            chat_id=int(OWNER_CHAT_ID),
            text=text,
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception:
        # Never let a failed alert break the user's conversation.
        logger.exception("Could not notify the owner.")
        return False

async def hire_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["enquiry"] = {}
    await reply(
        update,
        "🚀 <b>Hire N3thunt3r</b>\n\n"
        "Let's start your project enquiry. You can send /cancel at any time.\n\n"
        "<b>Step 1 of 3:</b> What is your name?",
    )
    return ASK_NAME


async def hire_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("enquiry", {})["name"] = (
        update.effective_message.text.strip()[:MAX_NAME_LENGTH]
    )
    await reply(
        update,
        "<b>Step 2 of 3:</b> What do you need?\n"
        "<i>(for example: a website, a mobile app, a security review)</i>",
    )
    return ASK_NEED


async def hire_need(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.setdefault("enquiry", {})["need"] = (
        update.effective_message.text.strip()[:MAX_NEED_LENGTH]
    )
    await reply(
        update,
        "<b>Step 3 of 3:</b> Please give a short description of your project.",
    )
    return ASK_DESCRIPTION


async def hire_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    enquiry = context.user_data.setdefault("enquiry", {})
    enquiry["description"] = update.effective_message.text.strip()[
        :MAX_DESCRIPTION_LENGTH
    ]

    user = update.effective_user
    enquiry["telegram_user_id"] = user.id if user else None
    enquiry["telegram_username"] = user.username if user else None

    save_enquiry(enquiry)

    # Alert the owner about the new enquiry.
    delivered = await notify_owner(
        context,
        "🔔 <b>New enquiry received</b>\n\n"
        f"<b>From:</b> {describe_sender(update)}\n"
        f"<b>Name:</b> {html.escape(enquiry['name'])}\n"
        f"<b>Need:</b> {html.escape(enquiry['need'])}\n"
        f"<b>Description:</b> {html.escape(enquiry['description'])}",
    )

    if delivered:
        closing = "Your enquiry has been sent to N3thunt3r, who will get back to you."
    else:
        closing = (
            "I couldn't forward this automatically, so please also use the "
            "/contact channels to make sure your request reaches N3thunt3r."
        )

    await reply(
        update,
        "✅ <b>Thank you! Your enquiry summary:</b>\n\n"
        f"<b>Name:</b> {html.escape(enquiry['name'])}\n"
        f"<b>Need:</b> {html.escape(enquiry['need'])}\n"
        f"<b>Description:</b> {html.escape(enquiry['description'])}\n\n"
        f"{closing}",
    )
    context.user_data.pop("enquiry", None)
    return ConversationHandler.END


async def hire_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    enquiry = context.user_data.pop("enquiry", {})

    # Alert the owner, including whatever the person had filled in so far.
    partial = "\n".join(
        f"<b>{label}:</b> {html.escape(enquiry[key])}"
        for key, label in (("name", "Name"), ("need", "Need"))
        if key in enquiry
    ) or "<i>Nothing entered yet</i>"
    await notify_owner(
        context,
        "⚠️ <b>Enquiry cancelled</b>\n\n"
        f"<b>From:</b> {describe_sender(update)}\n"
        f"{partial}",
    )

    await reply(update, "❌ Enquiry cancelled. You are back at the main menu.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Fallback handlers and the global error handler
# ---------------------------------------------------------------------------


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(
        update,
        "🤔 Sorry, I don't recognise that command.\n"
        "Send /help to see everything I can do.",
    )


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(
        update,
        "I didn't quite understand that. Please choose an option from the "
        "menu below, or send /help.",
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log any unexpected error and tell the user instead of crashing."""
    logger.error("Unhandled exception while processing an update:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong on my side. Please try again in a moment."
        )


# ---------------------------------------------------------------------------
# Registering handlers and running the bot
# ---------------------------------------------------------------------------

# Slash commands -> handler functions (/hire is handled by the conversation).
COMMANDS = {
    "start": start,
    "about": about,
    "services": services,
    "projects": projects,
    "skills": skills,
    "portfolio": portfolio,
    "github": github,
    "contact": contact,
    "ask": ask,
    "help": help_command,
    "myid": my_id,
}

# Keyboard button labels -> the same handler functions.
BUTTONS = {
    BTN_ABOUT: about,
    BTN_SERVICES: services,
    BTN_PROJECTS: projects,
    BTN_SKILLS: skills,
    BTN_PORTFOLIO: portfolio,
    BTN_GITHUB: github,
    BTN_CONTACT: contact,
    BTN_HELP: help_command,
}


async def post_init(application: Application) -> None:
    """Runs once at startup: fills Telegram's blue "Menu" command list."""
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Show the main menu"),
            BotCommand("about", "About N3thunt3r"),
            BotCommand("services", "Services offered"),
            BotCommand("projects", "Project examples"),
            BotCommand("skills", "Technologies and skills"),
            BotCommand("portfolio", "Portfolio link"),
            BotCommand("github", "GitHub profile"),
            BotCommand("contact", "Contact information"),
            BotCommand("hire", "Start a project enquiry"),
            BotCommand("ask", "AI assistant (coming soon)"),
            BotCommand("help", "Show help"),
        ]
    )


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token or token in ("YOUR_TELEGRAM_BOT_TOKEN", "PASTE_MY_BOT_TOKEN_HERE"):
        raise SystemExit(
            "BOT_TOKEN is missing. Open the .env file and set your BotFather token, "
            "for example: BOT_TOKEN=123456:ABC..."
        )

    application = Application.builder().token(token).post_init(post_init).build()

    # Text that should NOT be treated as an answer inside the hire flow:
    # commands and menu button presses still work while an enquiry is open.
    menu_labels = list(BUTTONS) + [BTN_HIRE]
    answer_filter = filters.TEXT & ~filters.COMMAND & ~filters.Text(menu_labels)

    # 1) The hire conversation (registered first so it gets priority).
    hire_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("hire", hire_start),
            MessageHandler(filters.Text([BTN_HIRE]), hire_start),
        ],
        states={
            ASK_NAME: [MessageHandler(answer_filter, hire_name)],
            ASK_NEED: [MessageHandler(answer_filter, hire_need)],
            ASK_DESCRIPTION: [MessageHandler(answer_filter, hire_description)],
        },
        fallbacks=[CommandHandler("cancel", hire_cancel)],
        allow_reentry=True,  # pressing "Hire" again restarts the flow
    )
    application.add_handler(hire_conversation)

    # 2) Slash commands.
    for command_name, handler in COMMANDS.items():
        application.add_handler(CommandHandler(command_name, handler))

    # 3) Keyboard buttons (exact text match).
    for label, handler in BUTTONS.items():
        application.add_handler(MessageHandler(filters.Text([label]), handler))

    # 4) Anything else: unknown commands first, then unknown plain text.
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    # 5) Global error handler.
    application.add_error_handler(error_handler)

    logger.info("N3thunt3r bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()