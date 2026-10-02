# N3thunt3r Telegram Bot

A Telegram bot for the N3thunt3r technology/developer brand. Version 1 includes
the `/start` command, a main menu keyboard, all info commands, and a simple
"Hire N3thunt3r" project enquiry flow.

## Requirements

- Python 3.11 or newer
- A Telegram bot token from @BotFather

## Windows setup

1. Create the project folder (skip if you already have it):

```powershell
   mkdir n3thunt3r-telegram-bot
   cd n3thunt3r-telegram-bot
```

2. Put `bot.py`, `.env`, `.env.example`, `.gitignore`, `requirements.txt`
   and `README.md` in this folder.

3. Create a virtual environment:

```powershell
   python -m venv venv
```

4. Activate it:

```powershell
   venv\Scripts\activate
```

   You should now see `(venv)` at the start of your prompt.

5. Install dependencies:

```powershell
   pip install -r requirements.txt
```

## BotFather and your token

You already created the bot with **@BotFather** and received a bot token.
Open the `.env` file and paste the token:

```text
BOT_TOKEN=PASTE_MY_BOT_TOKEN_HERE
```

Replace `PASTE_MY_BOT_TOKEN_HERE` with your real token (no quotes, no spaces).

Never put the token in `bot.py`, and never commit `.env` to Git (it is already
listed in `.gitignore`). If the token is ever exposed, open @BotFather, choose
your bot, and use **API Token -> Revoke current token**.

## Run the bot

```powershell
python bot.py
```

Leave the terminal open while the bot runs. Press `Ctrl+C` to stop it.

## Test the bot in Telegram

1. Open Telegram and search for your bot's username (the one you chose in BotFather).
2. Press **Start**, or send `/start`.
3. You should see the welcome message and the menu keyboard.

| What to test | Expected result |
|---|---|
| `/start` | Welcome message + menu keyboard |
| `/about` or 👤 About | About N3thunt3r and Benedict Amankwa Osei |
| `/services` or 🛠 Services | List of services |
| `/projects` or 💻 Projects | Project list |
| `/skills` or 🧠 Skills | Technologies list |
| `/portfolio` or 🌐 Portfolio | Portfolio link |
| `/github` or 🐙 GitHub | GitHub profile link |
| `/contact` or 📩 Contact | Contact message with placeholder |
| `/hire` or 🚀 Hire N3thunt3r | Asks name, need, description, then shows a summary |
| `/cancel` (during hire) | Cancels the enquiry |
| `/ask` | "AI assistant coming soon" message |
| `/help` or ❓ Help | Commands and buttons overview |
| `/randomcommand` | Friendly "unknown command" reply |
| Any random text | Friendly "please use the menu" reply |

## Common errors

| Problem | Solution |
|---|---|
| `python` is not recognized | Install Python from python.org and tick "Add Python to PATH", or try `py -m venv venv`. |
| PowerShell blocks `venv\Scripts\activate` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. Or use Command Prompt. |
| `ModuleNotFoundError: No module named 'telegram'` | The venv is not active or dependencies are missing. Activate it and run `pip install -r requirements.txt`. |
| `BOT_TOKEN is missing` | Check that `.env` is in the same folder as `bot.py` and contains `BOT_TOKEN=your_token`. |
| `InvalidToken` / `Unauthorized` | The token is wrong or revoked. Copy it again from @BotFather. |
| `Conflict: terminated by other getUpdates request` | Another copy of the bot is running. Stop it, or close other terminals. |
| `TimedOut` / `NetworkError` | Check your internet connection and try again. |
| Menu keyboard not showing | Send `/start`. |
| Buttons do nothing | Make sure you did not edit the button labels in only one place. Use the `BTN_*` constants. |

## Extending later

- Database: replace the body of `save_enquiry()` in `bot.py`.
- AI assistant: replace the `ask()` handler.
- Contact details: edit `CONTACT_DETAILS` at the top of `bot.py`.
- New command: add a handler function, then add it to `COMMANDS` (and `BUTTONS` if it has a button).