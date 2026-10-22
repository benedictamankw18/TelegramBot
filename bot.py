"""
N3thunt3r Telegram Bot - Version 1.1

Features:
  - /start with a custom reply keyboard (main menu)
  - Commands and keyboard buttons that both work independently
  - "Hire N3thunt3r" enquiry flow (customers can send several enquiries)
  - View all your enquiries, cancel one, or cancel all
  - Owner notifications for new and cancelled enquiries
  - Global error handler and unknown command/text handlers

Run with:  python bot.py
"""

import html
import logging
import os

from dotenv import load_dotenv
from google import genai
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database

# ---------------------------------------------------------------------------
# Setup: environment variables and logging
# ---------------------------------------------------------------------------

# Load variables from the .env file (BOT_TOKEN, OWNER_CHAT_ID) into the environment.
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

# Contact channels shown by /contact and the 📩 Contact button (HTML formatted).
CONTACT_DETAILS = (
    "💬 <b>Telegram:</b> @Kali0Nethunter\n"
    '📢 <b>Telegram community:</b> <a href="https://t.me/n3thunt3rsocial">N3thunt3r Social</a>\n'
    '🟢 <b>WhatsApp:</b> <a href="https://wa.me/233594500785">Chat on WhatsApp</a>\n'
    "📞 <b>Phone:</b> +233594500785, 0550030318, 0543779868\n"
    '💼 <b>LinkedIn:</b> <a href="https://www.linkedin.com/in/benedict-amankwa-991a5635b/">Benedict Amankwa Osei</a>\n'
    '🐙 <b>GitHub:</b> <a href="https://github.com/benedictamankw18">benedictamankw18</a>'
)

# Your personal Telegram chat ID. Enquiry alerts are sent here.
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
BTN_MY_ENQUIRIES = "📋 My Enquiries"
BTN_HELP = "❓ Help"

# The main menu: a persistent reply keyboard that fits desktop and mobile.
MAIN_MENU = ReplyKeyboardMarkup(
    [
        [BTN_ABOUT, BTN_SERVICES],
        [BTN_PROJECTS, BTN_SKILLS],
        [BTN_PORTFOLIO, BTN_GITHUB],
        [BTN_CONTACT, BTN_HIRE],
        [BTN_MY_ENQUIRIES, BTN_HELP],
    ],
    resize_keyboard=True,  # keeps the buttons a comfortable size
    is_persistent=True,  # keeps the keyboard visible
    input_field_placeholder="Choose an option from the menu...",
)

# Limits
MAX_NAME_LENGTH = 100
MAX_NEED_LENGTH = 300
MAX_DESCRIPTION_LENGTH = 1000
MAX_ACTIVE_ENQUIRIES = 5  # active enquiries one person may have at a time
MAX_LISTED = 10  # most enquiries shown in the "My Enquiries" list

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
    "Send your question like this:\n"
    "<code>/ask What services do you offer?</code>"
)
AI_UNAVAILABLE_TEXT = (
    "🤖 The AI assistant is temporarily unavailable. "
    "Please try again later or use the menu to explore services, projects, and skills."
)

HELP_TEXT = (
    "❓ <b>Help</b>\n\n"
    "You can use the menu buttons or type a command:\n\n"
    "/start - Show the main menu\n"
    "/about - About N3thunt3r\n"
    "/services - Services offered\n"
    "/projects - Project examples\n"
    "/skills - Technologies and skills\n"
    "/portfolio - Portfolio link\n"
    "/github - GitHub profile\n"
    "/contact - Contact information\n"
    "/hire - Send a project enquiry (you can send more than one)\n"
    "/myhires - View all your enquiries\n"
    "/showallhire - Owner: view all enquiries\n"
    "/cancelhire - Cancel one enquiry (for example /cancelhire 7)\n"
    "/cancelall - Cancel all your active enquiries\n"
    "/ask <question> - Ask the AI assistant\n"
    "/help - Show this help message\n"
    "/cancel - Stop the enquiry form you are filling in"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def reply(update: Update, text: str, markup=MAIN_MENU) -> None:
    """Send an HTML-formatted reply (with the main menu by default)."""
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


def describe_sender(update: Update) -> str:
    """Return a clickable description of who triggered the update."""
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


def shorten(text: str, limit: int) -> str:
    """Trim long text so lists stay under Telegram's message size limit."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# Simple command / button handlers (each works from a command OR a button)
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
    question = " ".join(context.args).strip()
    if not question:
        await reply(update, ASK_TEXT)
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not configured.")
        await reply(update, AI_UNAVAILABLE_TEXT)
        return

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    prompt = (
        "You are the N3thunt3r technology assistant. Answer clearly and briefly. "
        "Only claim services, projects, skills, or contact details that are "
        "consistent with the bot's menu. If the question is unrelated, politely "
        "redirect the user to N3thunt3r's technology services.\n\n"
        f"User question: {question}"
    )
    try:
        client = genai.Client(api_key=api_key)
        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
        )
        answer = (response.text or "").strip()
    except Exception:
        logger.exception("Gemini request failed.")
        await reply(update, AI_UNAVAILABLE_TEXT)
        return

    if not answer:
        logger.warning("Gemini returned an empty response.")
        await reply(update, AI_UNAVAILABLE_TEXT)
        return

    await reply(update, f"🤖 <b>Ask N3thunt3r</b>\n\n{html.escape(answer)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply(update, HELP_TEXT)


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tells you your chat ID so you can set OWNER_CHAT_ID in .env."""
    await reply(update, f"Your chat ID is: <code>{update.effective_chat.id}</code>")


# ---------------------------------------------------------------------------
# Hire flow: name -> what they need -> short description
# Each completed flow is saved as a separate enquiry in the database.
# ---------------------------------------------------------------------------

ASK_NAME, ASK_NEED, ASK_DESCRIPTION = range(3)


async def hire_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if user and database.count_active(user.id) >= MAX_ACTIVE_ENQUIRIES:
        await reply(
            update,
            f"You already have {MAX_ACTIVE_ENQUIRIES} active enquiries, which is "
            "the maximum at one time.\n"
            "Use /myhires to review them or /cancelhire to cancel one.",
        )
        return ConversationHandler.END

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
    user = update.effective_user
    enquiry = context.user_data.pop("enquiry", {})
    description = update.effective_message.text.strip()[:MAX_DESCRIPTION_LENGTH]

    if user is None or "name" not in enquiry or "need" not in enquiry:
        await reply(update, "Sorry, something went wrong. Please start again with /hire.")
        return ConversationHandler.END

    # Save to the database and get the enquiry number.
    enquiry_id = database.add_enquiry(
        user_id=user.id,
        username=user.username,
        name=enquiry["name"],
        need=enquiry["need"],
        description=description,
    )
    logger.info("Enquiry #%s saved for user %s", enquiry_id, user.id)

    # Alert the owner.
    delivered = await notify_owner(
        context,
        f"🔔 <b>New enquiry #{enquiry_id}</b>\n\n"
        f"<b>From:</b> {describe_sender(update)}\n"
        f"<b>Name:</b> {html.escape(enquiry['name'])}\n"
        f"<b>Need:</b> {html.escape(enquiry['need'])}\n"
        f"<b>Description:</b> {html.escape(description)}",
    )

    if delivered:
        closing = "Your enquiry has been sent to N3thunt3r, who will get back to you."
    else:
        closing = (
            "Your enquiry is saved, but I couldn't alert N3thunt3r automatically. "
            "Please also use the /contact channels to make sure it is seen."
        )

    await reply(
        update,
        f"✅ <b>Enquiry #{enquiry_id} received. Thank you!</b>\n\n"
        f"<b>Name:</b> {html.escape(enquiry['name'])}\n"
        f"<b>Need:</b> {html.escape(enquiry['need'])}\n"
        f"<b>Description:</b> {html.escape(description)}\n\n"
        f"{closing}\n\n"
        "<b>What would you like to do next?</b>\n"
        "🚀 Send another enquiry with /hire\n"
        "📋 View your enquiries with /myhires\n"
        "📩 Contact N3thunt3r with /contact",
    )
    return ConversationHandler.END


async def hire_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/cancel while filling in the form: nothing has been sent or saved yet."""
    context.user_data.pop("enquiry", None)
    await reply(update, "❌ Form cancelled. Nothing was sent. You are back at the main menu.")
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/cancel when the user is not currently filling in the hire form."""
    if context.user_data.pop("enquiry", None) is None:
        await reply(update, "There is no active enquiry form to cancel. Send /hire to start one.")
        return
    await reply(update, "❌ Form cancelled. Nothing was sent. You are back at the main menu.")


# ---------------------------------------------------------------------------
# My enquiries: view, cancel one, cancel all
# ---------------------------------------------------------------------------


def format_enquiry(enquiry: dict) -> str:
    """One enquiry as a short block of text."""
    is_active = enquiry["status"] == "active"
    icon, status = ("🟢", "Active") if is_active else ("⚪", "Cancelled")
    return (
        f"{icon} <b>#{enquiry['id']}</b> · {status} · {enquiry['created_at'][:10]}\n"
        f"<b>Need:</b> {html.escape(shorten(enquiry['need'], 80))}\n"
        f"<b>Details:</b> {html.escape(shorten(enquiry['description'], 120))}"
    )


def confirm_cancel_all_markup(count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"✅ Yes, cancel all ({count})", callback_data="cancelall_yes"
                ),
                InlineKeyboardButton("↩️ No, keep them", callback_data="cancelall_no"),
            ]
        ]
    )


def build_enquiry_list(
    user_id: int, notice: str = ""
) -> tuple[str, InlineKeyboardMarkup | None]:
    """Build the text and cancel buttons for a user's enquiry list."""
    prefix = f"{notice}\n\n" if notice else ""
    enquiries = database.get_user_enquiries(user_id)

    if not enquiries:
        return (
            prefix + "📋 You haven't sent any enquiries yet.\n"
            "Tap <b>🚀 Hire N3thunt3r</b> to send one.",
            None,
        )

    active = [e for e in enquiries if e["status"] == "active"]
    cancelled = [e for e in enquiries if e["status"] != "active"]

    # Always show every active enquiry, then fill the rest with recent cancelled ones.
    shown = sorted(
        active + cancelled[: max(0, MAX_LISTED - len(active))],
        key=lambda e: e["id"],
        reverse=True,
    )

    text = (
        prefix
        + f"📋 <b>Your enquiries</b> ({len(active)} active, {len(enquiries)} total)\n\n"
        + "\n\n".join(format_enquiry(e) for e in shown)
    )
    if len(shown) < len(enquiries):
        text += "\n\n<i>Older cancelled enquiries are not shown.</i>"

    buttons = [
        [InlineKeyboardButton(f"❌ Cancel #{e['id']}", callback_data=f"cancel:{e['id']}")]
        for e in active
    ]
    if len(active) > 1:
        buttons.append([InlineKeyboardButton("🗑 Cancel all", callback_data="cancelall")])

    return text, (InlineKeyboardMarkup(buttons) if buttons else None)


def format_owner_enquiry(enquiry: dict) -> str:
    """Format an enquiry with its sender details for the owner."""
    username = f"@{html.escape(enquiry['username'])}" if enquiry["username"] else "no username"
    return (
        f"{format_enquiry(enquiry)}\n"
        f"<b>From:</b> {html.escape(enquiry['name'])} "
        f"({username}, ID: {enquiry['user_id']})"
    )


async def show_all_hires(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show every enquiry to the configured owner only."""
    user = update.effective_user
    if user is None or not OWNER_CHAT_ID or str(user.id) != OWNER_CHAT_ID.strip():
        await reply(update, "This command is only available to the bot owner.")
        return

    enquiries = database.get_all_enquiries()
    if not enquiries:
        await reply(update, "📋 There are no hire enquiries yet.")
        return

    active_count = sum(enquiry["status"] == "active" for enquiry in enquiries)
    header = (
        f"📋 <b>All hire enquiries</b> "
        f"({active_count} active, {len(enquiries)} total)\n\n"
    )
    blocks: list[str] = []
    current = header
    for enquiry in enquiries:
        block = format_owner_enquiry(enquiry)
        if len(current) + len(block) + 2 > 3900 and current != header:
            blocks.append(current)
            current = ""
        current += block + "\n\n"
    if current.strip():
        blocks.append(current.rstrip())

    for block in blocks:
        await reply(update, block)


async def cancel_one(
    update: Update, context: ContextTypes.DEFAULT_TYPE, enquiry_id: int
) -> str:
    """Cancel one enquiry for the current user. Returns a message for them."""
    user = update.effective_user
    enquiry = database.get_enquiry(user.id, enquiry_id)

    if enquiry is None:
        return f"I couldn't find an enquiry #{enquiry_id} on your account."
    if enquiry["status"] != "active":
        return f"Enquiry #{enquiry_id} is already cancelled."
    if not database.cancel_enquiry(user.id, enquiry_id):
        return f"Enquiry #{enquiry_id} could not be cancelled. Please try again."

    await notify_owner(
        context,
        f"⚠️ <b>Enquiry #{enquiry_id} cancelled</b>\n\n"
        f"<b>From:</b> {describe_sender(update)}\n"
        f"<b>Need:</b> {html.escape(enquiry['need'])}",
    )
    return f"❌ Enquiry #{enquiry_id} has been cancelled."


async def cancel_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Cancel every active enquiry for the current user."""
    ids = database.cancel_all(update.effective_user.id)
    if not ids:
        return "You have no active enquiries to cancel."

    numbers = ", ".join(f"#{i}" for i in ids)
    await notify_owner(
        context,
        f"⚠️ <b>{len(ids)} enquiries cancelled</b>\n\n"
        f"<b>From:</b> {describe_sender(update)}\n"
        f"<b>Enquiries:</b> {numbers}",
    )
    return f"🗑 Cancelled {len(ids)} enquiries: {numbers}"


async def my_hires(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/myhires and the 📋 My Enquiries button."""
    text, markup = build_enquiry_list(update.effective_user.id)
    await reply(update, text, markup=markup or MAIN_MENU)


async def cancel_hire_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """/cancelhire 7 cancels #7. Without a number it shows the cancel buttons."""
    user_id = update.effective_user.id

    if context.args:
        number = context.args[0].lstrip("#")
        if not number.isdigit():
            await reply(update, "Please include the enquiry number, for example: /cancelhire 7")
            return
        notice = await cancel_one(update, context, int(number))
    elif database.count_active(user_id):
        notice = "Tap ❌ next to the enquiry you want to cancel."
    else:
        notice = ""

    text, markup = build_enquiry_list(user_id, notice)
    await reply(update, text, markup=markup or MAIN_MENU)


async def cancel_all_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """/cancelall asks for confirmation before cancelling everything."""
    count = database.count_active(update.effective_user.id)
    if count == 0:
        await reply(update, "You have no active enquiries to cancel.")
        return
    await reply(
        update,
        f"⚠️ <b>Cancel all {count} active enquiries?</b>",
        markup=confirm_cancel_all_markup(count),
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles taps on the inline buttons under the enquiry list."""
    query = update.callback_query
    user = update.effective_user
    if query is None or user is None:
        return
    await query.answer()  # stops the loading spinner on the button
    data = query.data or ""

    if data.startswith("cancel:"):
        notice = await cancel_one(update, context, int(data.split(":", 1)[1]))
        text, markup = build_enquiry_list(user.id, notice)

    elif data == "cancelall":
        count = database.count_active(user.id)
        if count == 0:
            text, markup = build_enquiry_list(user.id, "You have no active enquiries to cancel.")
        else:
            text = f"⚠️ <b>Cancel all {count} active enquiries?</b>"
            markup = confirm_cancel_all_markup(count)

    elif data == "cancelall_yes":
        notice = await cancel_all(update, context)
        text, markup = build_enquiry_list(user.id, notice)

    elif data == "cancelall_no":
        text, markup = build_enquiry_list(user.id, "👍 Nothing was cancelled.")

    else:
        return

    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


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
    "myhires": my_hires,
    "cancelhire": cancel_hire_command,
    "cancelall": cancel_all_command,
    "cancel": cancel_command,
    "showallhire": show_all_hires,
    "showallhires": show_all_hires,
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
    BTN_MY_ENQUIRIES: my_hires,
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
            BotCommand("hire", "Send a project enquiry"),
            BotCommand("myhires", "View my enquiries"),
            BotCommand("showallhire", "Owner: view all enquiries"),
            BotCommand("cancelhire", "Cancel one enquiry"),
            BotCommand("cancelall", "Cancel all my enquiries"),
            BotCommand("ask", "Ask the AI assistant"),
            BotCommand("help", "Show help"),
        ]
    )


def _get_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token or token in ("YOUR_TELEGRAM_BOT_TOKEN", "PASTE_MY_BOT_TOKEN_HERE"):
        raise SystemExit(
            "BOT_TOKEN is missing. Open the .env file and set your BotFather token, "
            "for example: BOT_TOKEN=123456:ABC..."
        )
    return token

def build_application() -> Application:
    """Build and configure the Telegram application without starting it."""
    application = Application.builder().token(_get_token()).post_init(post_init).build()
    # Text that should NOT be treated as an answer inside the hire flow:
    # commands and menu button presses still work while an enquiry form is open.
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
        allow_reentry=True,  # pressing "Hire" again restarts the form
    )
    application.add_handler(hire_conversation)

    # 2) Slash commands.
    for command_name, handler in COMMANDS.items():
        application.add_handler(CommandHandler(command_name, handler))

    # 3) Keyboard buttons (exact text match).
    for label, handler in BUTTONS.items():
        application.add_handler(MessageHandler(filters.Text([label]), handler))

    # 4) Inline buttons under the enquiry list (cancel one / cancel all).
    application.add_handler(
        CallbackQueryHandler(
            button_callback, pattern=r"^(cancel:\d+|cancelall|cancelall_yes|cancelall_no)$"
        )
    )

    # 5) Anything else: unknown commands first, then unknown plain text.
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    # 6) Global error handler.
    application.add_error_handler(error_handler)

    return application


def main() -> None:
    """Run the bot with polling for local development."""
    database.init_db()
    logger.info("N3thunt3r bot is running in polling mode. Press Ctrl+C to stop.")
    build_application().run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()