import os
import asyncio
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# ===== config via env =====
TOKEN      = os.getenv("DISCORD_TOKEN", "").strip()
OWNER_ID   = int(os.getenv("DISCORD_OWNER_ID", "0") or 0)
GUILD_ID   = int(os.getenv("DISCORD_GUILD_ID", "0") or 0)

ROLE_CHANGES_ID      = int(os.getenv("ROLE_CHANGES_ID", "0") or 0)
ROLE_STATUS_ID       = int(os.getenv("ROLE_STATUS_ID", "0") or 0)
ROLE_PICK_CHANNEL_ID = int(os.getenv("ROLE_PICK_CHANNEL_ID", "0") or 0)

# single place to change the theme color (lavender)
LAVENDER = 0xB57EDC

# ===== client (slash-only) =====
intents = discord.Intents.default()
intents.guilds = True
client = commands.Bot(command_prefix="!", intents=intents)  # prefix unused; slash only
tree = client.tree

# global HTTP session
_http: aiohttp.ClientSession | None = None

# ===== helpers =====
def now_utc_iso():
    return discord.utils.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def is_owner(inter: discord.Interaction) -> bool:
    return OWNER_ID and inter.user and inter.user.id == OWNER_ID

def emb(title: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=LAVENDER)
    e.timestamp = discord.utils.utcnow()
    return e

async def reply_embed(inter: discord.Interaction, title: str, desc: str, *, ephemeral=True):
    if inter.response.is_done():
        await inter.followup.send(embed=emb(title, desc), ephemeral=ephemeral)
    else:
        await inter.response.send_message(embed=emb(title, desc), ephemeral=ephemeral)

async def http_get_json(url: str, params: dict | None = None, timeout_sec: float = 8.0):
    """Minimal JSON GET with sane timeouts and errors."""
    if params is None:
        params = {}
    global _http
    if _http is None or _http.closed:
        _http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_sec))
    try:
        async with _http.get(url, params=params) as r:
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            return await r.json()
    except asyncio.TimeoutError:
        raise RuntimeError("timeout")
    except aiohttp.ClientError as e:
        raise RuntimeError(str(e) or "client error")

# ===== role picker =====
class RolePicker(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Changes", style=discord.ButtonStyle.secondary, custom_id="rp_changes")
    async def btn_changes(self, inter: discord.Interaction, _button: discord.ui.Button):
        if not inter.guild:
            return await reply_embed(inter, "Not available", "This only works inside a server.")
        role = inter.guild.get_role(ROLE_CHANGES_ID)
        if not role:
            return await reply_embed(inter, "Role missing", "Couldn’t find the Changes role.")
        member: discord.Member = inter.user
        if role in member.roles:
            await member.remove_roles(role, reason="RolePicker toggle: remove Changes")
            return await reply_embed(inter, "Updated", "Removed Changes.", ephemeral=True)
        else:
            await member.add_roles(role, reason="RolePicker toggle: add Changes")
            return await reply_embed(inter, "Updated", "Added Changes.", ephemeral=True)

    @discord.ui.button(label="Status Alerts", style=discord.ButtonStyle.secondary, custom_id="rp_status")
    async def btn_status(self, inter: discord.Interaction, _button: discord.ui.Button):
        if not inter.guild:
            return await reply_embed(inter, "Not available", "This only works inside a server.")
        role = inter.guild.get_role(ROLE_STATUS_ID)
        if not role:
            return await reply_embed(inter, "Role missing", "Couldn’t find the Status Alerts role.")
        member: discord.Member = inter.user
        if role in member.roles:
            await member.remove_roles(role, reason="RolePicker toggle: remove Status")
            return await reply_embed(inter, "Updated", "Removed Status Alerts.", ephemeral=True)
        else:
            await member.add_roles(role, reason="RolePicker toggle: add Status")
            return await reply_embed(inter, "Updated", "Added Status Alerts.", ephemeral=True)

async def send_role_picker_embed():
    if not ROLE_PICK_CHANNEL_ID:
        return
    ch = client.get_channel(ROLE_PICK_CHANNEL_ID) or await client.fetch_channel(ROLE_PICK_CHANNEL_ID)
    desc = (
        "Choose what you want to be notified about.\n\n"
        "Changes — posts from the changelog\n"
        "Status Alerts — service up/down notes\n\n"
        "Click a button to toggle. No pings unless you opt in."
    )
    e = emb("Notification Preferences", desc)
    e.set_footer(text=f"Last posted {now_utc_iso()}")
    await ch.send(embed=e, view=RolePicker())

# ===== presence + sync + session =====
@client.event
async def on_ready():
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name="over homelab"),
    )
    client.add_view(RolePicker())
    try:
        if GUILD_ID:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
        else:
            await tree.sync()
        print(f"✅ Logged in as {client.user} — commands synced.")
    except Exception as e:
        print("Sync failed:", e)

@client.event
async def on_close():
    # discord.py doesn't always call this; but keep for cleanliness
    global _http
    if _http and not _http.closed:
        await _http.close()

# ===== cooldowns =====
cooldown_fast   = app_commands.checks.cooldown(1, 3.0)    # 1 use / 3s per user
cooldown_medium = app_commands.checks.cooldown(2, 10.0)   # 2 uses / 10s per user

# ===== commands =====

@tree.command(name="rolesetup", description="Post the Notification Preferences role picker (owner only).")
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def rolesetup_cmd(inter: discord.Interaction):
    if not is_owner(inter):
        return await reply_embed(inter, "Denied", "Only the owner can do that.")
    await reply_embed(inter, "Working", "Posting role picker…", ephemeral=True)
    await send_role_picker_embed()
    await reply_embed(inter, "Done", "Role picker posted.", ephemeral=True)

@tree.command(name="status", description="Bot presence and latency.")
@cooldown_fast
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def status_cmd(inter: discord.Interaction):
    u = client.user
    desc = (
        f"Bot: {u.mention if u else '—'}\n"
        f"Presence: watching over homelab\n"
        f"Latency: {round(client.latency * 1000)} ms\n"
        f"{now_utc_iso()}"
    )
    await reply_embed(inter, "Status", desc, ephemeral=True)

@tree.command(name="purge", description="Delete a number of recent messages in this channel.")
@app_commands.describe(count="How many messages to delete (1–100)")
@cooldown_medium
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def purge_cmd(inter: discord.Interaction, count: app_commands.Range[int, 1, 100]):
    await inter.response.defer(ephemeral=True, thinking=True)
    deleted = await inter.channel.purge(limit=count, bulk=True)  # type: ignore
    await inter.followup.send(embed=emb("Purge", f"Deleted {len(deleted)} messages."), ephemeral=True)

@tree.command(name="help", description="Show available commands.")
@cooldown_fast
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def help_cmd(inter: discord.Interaction):
    lines = [
        "/rolesetup — post role picker (owner only)",
        "/status — bot presence + latency",
        "/purge — delete recent messages (requires Manage Messages)",
        "/weather <place> [unit] — current weather",
        "/wiki <query> — short summary",
        "/help — this list",
        "/say — send an embed to a channel (owner only)",
    ]
    await reply_embed(inter, "Commands", "\n".join(lines), ephemeral=True)

@tree.command(name="say", description="Send a simple embed to a channel (owner only).")
@app_commands.describe(message="Text to send", channel="Target channel (optional)")
@cooldown_medium
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def say_cmd(inter: discord.Interaction, message: str, channel: discord.TextChannel | None = None):
    if not is_owner(inter):
        return await reply_embed(inter, "Denied", "Only the owner can do that.")
    target = channel or inter.channel
    await target.send(embed=emb("Message", message))
    await reply_embed(inter, "Sent", f"Posted in {target.mention}.", ephemeral=True)

# ===== web features =====

@tree.command(name="weather", description="Current weather for a place.")
@app_commands.describe(place="City or place name (e.g., Chicago, IL or London)", unit="Units: auto, metric, imperial")
@app_commands.choices(unit=[
    app_commands.Choice(name="auto", value="auto"),
    app_commands.Choice(name="metric (°C, m/s)", value="metric"),
    app_commands.Choice(name="imperial (°F, mph)", value="imperial"),
])
@cooldown_medium
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def weather_cmd(inter: discord.Interaction, place: str, unit: app_commands.Choice[str] | None = None):
    await inter.response.defer(ephemeral=True, thinking=True)

    # geocode via Open-Meteo (no key)
    try:
        geo = await http_get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": place, "count": 1, "language": "en", "format": "json"}
        )
        if not geo or not geo.get("results"):
            return await inter.followup.send(embed=emb("Weather", "Location not found."))
        g0 = geo["results"][0]
        lat, lon = g0["latitude"], g0["longitude"]
        display_name = f"{g0.get('name','')} {g0.get('admin1','') or ''} {g0.get('country','') or ''}".strip()
    except RuntimeError as e:
        return await inter.followup.send(embed=emb("Weather", f"Geocoding failed: {e}"))

    # units
    choice = (unit.value if unit else "auto")
    temp_unit = "fahrenheit" if choice == "imperial" else ("celsius" if choice == "metric" else "fahrenheit" if "US" in (g0.get("country_code","") or "") else "celsius")
    wind_unit = "mph" if temp_unit == "fahrenheit" else "ms"

    # forecast via Open-Meteo
    try:
        wx = await http_get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": lat, "longitude": lon,
                "current_weather": "true",
                "hourly": "temperature_2m,precipitation_probability",
                "temperature_unit": "fahrenheit" if temp_unit == "fahrenheit" else "celsius",
                "windspeed_unit": "mph" if wind_unit == "mph" else "ms",
            }
        )
        cur = wx.get("current_weather", {})
        if not cur:
            return await inter.followup.send(embed=emb("Weather", "No data available."))
        temp = cur.get("temperature")
        wind = cur.get("windspeed")
        code = cur.get("weathercode")
        # quick code -> text map (minimal)
        WMAP = {
            0:"Clear", 1:"Mainly clear", 2:"Partly cloudy", 3:"Overcast",
            45:"Fog", 48:"Depositing rime fog", 51:"Light drizzle", 53:"Drizzle", 55:"Heavy drizzle",
            61:"Light rain", 63:"Rain", 65:"Heavy rain",
            71:"Light snow", 73:"Snow", 75:"Heavy snow",
            80:"Light showers", 81:"Showers", 82:"Heavy showers",
            95:"Thunderstorm", 96:"Thunderstorm w/ hail", 99:"Severe thunderstorm"
        }
        cond = WMAP.get(code, "—")
        unit_sym = "°F" if temp_unit == "fahrenheit" else "°C"
        wind_sym = "mph" if wind_unit == "mph" else "m/s"
        desc = (
            f"Location: {display_name}\n"
            f"Temperature: {temp} {unit_sym}\n"
            f"Wind: {wind} {wind_sym}\n"
            f"Conditions: {cond}\n"
            f"{now_utc_iso()}"
        )
        await inter.followup.send(embed=emb("Weather", desc), ephemeral=True)
    except RuntimeError as e:
        await inter.followup.send(embed=emb("Weather", f"Fetch failed: {e}"), ephemeral=True)

@tree.command(name="wiki", description="Short Wikipedia summary.")
@app_commands.describe(query="Topic to search")
@cooldown_medium
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def wiki_cmd(inter: discord.Interaction, query: str):
    await inter.response.defer(ephemeral=True, thinking=True)
    try:
        # first, get best title via opensearch
        sr = await http_get_json("https://en.wikipedia.org/w/api.php", {
            "action":"opensearch", "search":query, "limit":1, "namespace":0, "format":"json"
        })
        title = (sr[1][0] if isinstance(sr, list) and sr and len(sr) > 1 and sr[1] else "").replace(" ", "_")
        if not title:
            return await inter.followup.send(embed=emb("Wiki", "No results found."), ephemeral=True)

        # then fetch summary
        js = await http_get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}")
        extract = js.get("extract") or "No summary."
        url = js.get("content_urls", {}).get("desktop", {}).get("page", "")
        if len(extract) > 1000:
            extract = extract[:1000] + "…"
        desc = f"{extract}\n\n{url}" if url else extract
        await inter.followup.send(embed=emb("Wiki", desc), ephemeral=True)
    except RuntimeError as e:
        await inter.followup.send(embed=emb("Wiki", f"Fetch failed: {e}"), ephemeral=True)

# ===== unified error handling =====
@tree.error
async def on_app_command_error(inter: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        return await reply_embed(inter, "Slow down", f"Try again in {error.retry_after:.1f}s.", ephemeral=True)
    if isinstance(error, app_commands.MissingPermissions):
        return await reply_embed(inter, "Insufficient permissions", "You don’t have permission for that.", ephemeral=True)
    if isinstance(error, app_commands.BotMissingPermissions):
        return await reply_embed(inter, "Missing bot permissions", "I’m missing required permissions.", ephemeral=True)
    try:
        await reply_embed(inter, "Error", "Something went wrong.", ephemeral=True)
    except Exception:
        pass
    raise error  # still log

# ===== run =====
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN")
    try:
        client.run(TOKEN)
    finally:
        # ensure HTTP session closes on shutdown
        if _http and not _http.closed:
            asyncio.run(_http.close())
