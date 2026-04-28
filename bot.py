import discord
from discord.ext import commands
import re
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="", intents=intents, help_command=None)

# Load the anime database on startup
DB_PATH = os.path.join(os.path.dirname(__file__), "myAnimeList.txt")

def load_database():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        entries = [line.strip() for line in f if line.strip()]
    return entries

ANIME_LIST = load_database()

def clean_hint(message: str) -> str:
    """Remove the 💡 Hint prefix and all backticks from the message."""
    # Remove the hint emoji + word (with optional surrounding spaces)
    cleaned = re.sub(r"💡\s*Hint\s*", "", message)
    # Remove all backticks
    cleaned = cleaned.replace("`", "")
    return cleaned.strip()

def build_pattern(hint: str) -> re.Pattern:
    """
    Convert a hint string like 'y__r l__ in __ril' into a regex.
    Each underscore matches exactly one character (any).
    Spaces are matched loosely.
    """
    # Escape everything except underscores, then replace _ with .
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

def search_database(hint: str) -> list[str]:
    """Search the anime list for entries matching the hint pattern."""
    try:
        pattern = build_pattern(hint)
    except re.error:
        return []

    matches = [entry for entry in ANIME_LIST if pattern.match(entry)]
    return matches

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Database loaded: {len(ANIME_LIST)} entries")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.strip()

    # Check if message starts with "hnt" (case-insensitive)
    if not re.match(r"^hnt\s+", content, re.IGNORECASE):
        return

    # Extract everything after "hnt "
    raw_hint = content[content.index(" "):].strip()

    # Clean the hint
    cleaned = clean_hint(raw_hint)

    if not cleaned:
        await message.reply("Please provide a hint after `hnt`.")
        return

    # Search the database
    matches = search_database(cleaned)

    if not matches:
        await message.reply(
            f"🔍 No matches found for: `{cleaned}`\n"
            f"*(Searched {len(ANIME_LIST):,} entries)*"
        )
    elif len(matches) == 1:
        await message.reply(f"✅ **{matches[0]}**")
    else:
        # Multiple matches
        match_list = "\n".join(f"• {m}" for m in matches[:10])
        footer = f"\n*...and {len(matches) - 10} more*" if len(matches) > 10 else ""
        await message.reply(f"🎯 Found {len(matches)} matches:\n{match_list}{footer}")

bot.run(os.environ["DISCORD_TOKEN"])
