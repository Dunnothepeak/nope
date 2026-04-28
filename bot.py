import discord
import re
import os

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

# Load the anime database on startup
DB_PATH = os.path.join(os.path.dirname(__file__), "myAnimeList-062020.txt")

def load_database():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        entries = [line.strip() for line in f if line.strip()]
    return entries

ANIME_LIST = load_database()

def clean_hint(message: str) -> str:
    cleaned = re.sub(r"💡\s*Hint\s*", "", message)
    cleaned = cleaned.replace("`", "")
    return cleaned.strip()

def build_pattern(hint: str) -> re.Pattern:
    parts = []
    for char in hint:
        if char == "_":
            parts.append(".")
        elif char == " ":
            parts.append(r"\s")
        else:
            parts.append(re.escape(char))
    pattern = "".join(parts)
    return re.compile(f"^{pattern}$", re.IGNORECASE)

def search_database(hint: str) -> list:
    try:
        pattern = build_pattern(hint)
    except re.error:
        return []
    return [entry for entry in ANIME_LIST if pattern.match(entry)]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Database loaded: {len(ANIME_LIST)} entries")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.strip()

    if not re.match(r"^hnt\s+", content, re.IGNORECASE):
        return

    raw_hint = content[content.index(" "):].strip()
    cleaned = clean_hint(raw_hint)

    if not cleaned:
        return

    matches = search_database(cleaned)

    if not matches:
        text = f"-# No matches found."
    elif len(matches) == 1:
        text = f"## {matches[0]}"
    else:
        lines = "\n".join(f"-# {m}" for m in matches[:10])
        extra = f"\n-# ...and {len(matches) - 10} more" if len(matches) > 10 else ""
        text = lines + extra

    container = discord.ui.Container(
        discord.ui.TextDisplay(text)
    )

    view = discord.ui.LayoutView()
    view.add_item(container)

    await message.reply(view=view)

bot.run(os.environ["DISCORD_TOKEN"])
