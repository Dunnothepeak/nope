import discord
from discord.ext import commands
import re
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="\x00", intents=intents, help_command=None)

DB_PATH = os.path.join(os.path.dirname(__file__), "myAnimeList-062020.txt")
HINT_BOT_ID = 429656936435286016

def load_database():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        entries = [line.strip() for line in f if line.strip()]
    return entries

ANIME_LIST = load_database()

def clean_hint(text: str) -> str:
    cleaned = re.sub(r"💡\s*Hint\s*", "", text)
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
    return re.compile(f"^{''.join(parts)}$", re.IGNORECASE)

def search_database(hint: str) -> list:
    try:
        pattern = build_pattern(hint)
    except re.error:
        return []
    return [entry for entry in ANIME_LIST if pattern.match(entry)]

def extract_hint_from_message(message: discord.Message):
    """Try to extract hint text from a message (content or components)."""
    # Check plain content first
    candidates = []
    if message.content:
        candidates.append(message.content)

    # Check components (Components V2 / containers)
    for component in message.components:
        # Walk nested components
        stack = [component]
        while stack:
            comp = stack.pop()
            if hasattr(comp, "components"):
                stack.extend(comp.components)
            if hasattr(comp, "content") and comp.content:
                candidates.append(comp.content)

    for text in candidates:
        if "💡" in text or "Hint" in text:
            return clean_hint(text)

    return None

async def send_answer(message: discord.Message, hint: str):
    matches = search_database(hint)

    if not matches:
        text = "No matches found."
    elif len(matches) == 1:
        text = matches[0]
    else:
        text = "\n".join(matches[:10])
        if len(matches) > 10:
            text += f"\n...and {len(matches) - 10} more"

    embed = discord.Embed(description=text)
    await message.reply(embed=embed, mention_author=False)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Database loaded: {len(ANIME_LIST)} entries")

@bot.event
async def on_message(message: discord.Message):
    # Auto-reply to the hint bot
    if message.author.id == HINT_BOT_ID:
        print(f"CONTENT: {repr(message.content)}")
        print(f"EMBEDS: {message.embeds}")
        print(f"COMPONENTS: {message.components}")
        for c in message.components:
            print(f"  COMP: {repr(c)}")
    return
    if message.author.bot:
        return

    # Manual hnt command
    content = message.content.strip()
    if not re.match(r"^hnt\s+", content, re.IGNORECASE):
        return

    raw_hint = content[content.index(" "):].strip()
    cleaned = clean_hint(raw_hint)
    if not cleaned:
        return

    await send_answer(message, cleaned)

bot.run(os.environ["DISCORD_TOKEN"])
