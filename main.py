import os
import asyncio
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote, quote_plus
import io
import datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import pandas as pd
import yfinance as yf
import difflib
from duckduckgo_search import DDGS

try:  # optional candlestick support
    import mplfinance as mpf
    USE_CANDLES = True
except Exception:  # pragma: no cover - best effort
    mpf = None
    USE_CANDLES = False


TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0") or 0)
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "1395516484859723867") or 0)
ROLE_CHANGES_ID = int(os.getenv("ROLE_CHANGES_ID", "0") or 0)
ROLE_STATUS_ID = int(os.getenv("ROLE_STATUS_ID", "0") or 0)
ROLE_PICK_CHANNEL_ID = int(os.getenv("ROLE_PICK_CHANNEL_ID", "0") or 0)
PIPED_API_BASE = os.getenv("PIPED_API_BASE", "https://piped.video/api/v1").rstrip("/")
PIPED_FRONTEND_BASE = os.getenv("PIPED_FRONTEND_BASE", "https://piped.video").rstrip("/")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "").strip()
LAVENDER = 0xB57EDC

intents = discord.Intents.default()
intents.guilds = True
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

_http: aiohttp.ClientSession | None = None
DEFAULT_HEADERS = {"User-Agent": "homelab-discord-bot/1.0 (+github.com/you)"}

def now_utc_iso():
    return discord.utils.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def is_owner(inter: discord.Interaction) -> bool:
    return OWNER_ID and inter.user and inter.user.id == OWNER_ID


def use_ephemeral(inter: discord.Interaction) -> bool:
    """Use ephemeral replies only when invoked inside a guild."""
    return inter.guild is not None

def emb(title: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=LAVENDER)
    e.timestamp = discord.utils.utcnow()
    return e

async def reply_embed(inter: discord.Interaction, title: str, desc: str, *, ephemeral=True):
    ephemeral = ephemeral and use_ephemeral(inter)
    if inter.response.is_done():
        await inter.followup.send(embed=emb(title, desc), ephemeral=ephemeral)
    else:
        await inter.response.send_message(embed=emb(title, desc), ephemeral=ephemeral)

async def http_get_json(url: str, params: dict | None = None, timeout_sec: float = 10.0):
    global _http
    params = params or {}
    if _http is None or _http.closed:
        _http = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_sec), headers=DEFAULT_HEADERS)
    try:
        async with _http.get(url, params=params) as r:
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            return await r.json()
    except asyncio.TimeoutError:
        raise RuntimeError("timeout")
    except aiohttp.ClientError as e:
        raise RuntimeError(str(e) or "client error")

def hhmmss(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    try:
        seconds = int(seconds)
    except Exception:
        return "—"
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

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

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name="over homelab"))
    client.add_view(RolePicker())
    if not getattr(client, "synced", False):
        try:
            if GUILD_ID:
                await tree.sync(guild=discord.Object(id=GUILD_ID))
            synced = await tree.sync()
            print(f"Synced {len(synced)} command(s)")
            client.synced = True
        except Exception as e:
            print("Sync failed:", e)

@client.event
async def on_close():
    global _http
    if _http and not _http.closed:
        await _http.close()

cooldown_fast = app_commands.checks.cooldown(1, 3.0)
cooldown_medium = app_commands.checks.cooldown(2, 10.0)

@tree.command(name="rolesetup", description="Post the Notification Preferences role picker (owner only).")
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def rolesetup_cmd(inter: discord.Interaction):
    if not inter.guild:
        return await reply_embed(inter, "Not available", "This command can only be used in a server.")
    if not is_owner(inter):
        return await reply_embed(inter, "Denied", "Only the owner can do that.")
    await reply_embed(inter, "Working", "Posting role picker…", ephemeral=True)
    await send_role_picker_embed()
    await reply_embed(inter, "Done", "Role picker posted.", ephemeral=True)

@tree.command(name="status", description="Bot presence and latency.")
@cooldown_fast
@app_commands.default_permissions(use_application_commands=True)
async def status_cmd(inter: discord.Interaction):
    u = client.user
    desc = f"Bot: {u.mention if u else '—'}\nPresence: watching over homelab\nLatency: {round(client.latency * 1000)} ms\n{now_utc_iso()}"
    await reply_embed(inter, "Status", desc, ephemeral=True)

@tree.command(name="purge", description="Bulk delete messages with optional filters.")
@app_commands.describe(
    amount="Max messages to scan (1–5000, default 200)",
    contains="Only delete messages containing this text",
    from_user="Only delete messages from this user",
    bots_only="Only delete messages sent by bots",
    dry_run="Show what would be deleted without removing"
)
@cooldown_medium
@app_commands.default_permissions(manage_messages=True, use_application_commands=True)
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def purge_cmd(
    inter: discord.Interaction,
    amount: app_commands.Range[int, 1, 5000] = 200,
    contains: str | None = None,
    from_user: discord.User | None = None,
    bots_only: bool = False,
    dry_run: bool = False,
):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        channel = inter.channel
        if not inter.guild or not isinstance(channel, discord.TextChannel):
            return await inter.followup.send(
                embed=emb("Purge", "This only works in server text channels."),
                ephemeral=use_ephemeral(inter),
            )

        scanned_msgs = [m async for m in channel.history(limit=amount)]
        scanned = len(scanned_msgs)
        substr = contains.lower() if contains else None
        targets: list[discord.Message] = []
        for m in scanned_msgs:
            if m.pinned or m.is_system():
                continue
            if substr and substr not in m.content.lower():
                continue
            if from_user and m.author.id != from_user.id:
                continue
            if bots_only and not m.author.bot:
                continue
            targets.append(m)

        cutoff = discord.utils.utcnow() - dt.timedelta(days=14)
        recent = [m for m in targets if m.created_at > cutoff]
        old = [m for m in targets if m.created_at <= cutoff]

        reason = f"/purge by {inter.user}"
        bulk_deleted = 0
        old_deleted = 0

        if not dry_run:
            for i in range(0, len(recent), 100):
                chunk = recent[i:i + 100]
                try:
                    await channel.delete_messages(chunk, reason=reason)
                    bulk_deleted += len(chunk)
                except discord.HTTPException:
                    await asyncio.sleep(2.0)
                    try:
                        await channel.delete_messages(chunk, reason=reason)
                        bulk_deleted += len(chunk)
                    except discord.HTTPException:
                        pass
                await asyncio.sleep(0.25)

            for m in old:
                try:
                    await m.delete(reason=reason)
                    old_deleted += 1
                    await asyncio.sleep(0.85)
                except discord.HTTPException:
                    await asyncio.sleep(1.75)
        else:
            bulk_deleted = len(recent)
            old_deleted = len(old)

        note = " This may take a while." if amount > 1000 else ""
        if dry_run:
            desc = f"Would purge {bulk_deleted} (bulk) + {old_deleted} (old) out of {scanned} scanned{note}"
        else:
            desc = f"Purged {bulk_deleted} (bulk) + {old_deleted} (old) out of {scanned} scanned{note}"
        await inter.followup.send(embed=emb("Purge", desc), ephemeral=use_ephemeral(inter))
    except Exception:
        await inter.followup.send(
            embed=emb("Purge", "Something went wrong while purging."),
            ephemeral=use_ephemeral(inter),
        )

@tree.command(name="help", description="Show available commands.")
@cooldown_fast
@app_commands.default_permissions(use_application_commands=True)
async def help_cmd(inter: discord.Interaction):
    lines = [
        "/status — bot presence + latency",
        "/purge — bulk delete messages with filters (requires Manage Messages)",
        "/yt <query> [limit] — search via Piped",
        "/wiki <query> — short summary",
        "/avatar [user] — show user's avatar",
        "/define <word> — dictionary lookup",
        "/search <query> — web search",
        "/image <query> — image search",
        "/dog — random dog picture",
        "/cat — random cat picture",
        "/weather <place> [unit] — current weather",
        "/stock <symbol> — show stock price & chart",
        "/rolesetup — post role picker (owner only)",
        "/resync <scope> — refresh commands (owner only)",
    ]
    await reply_embed(inter, "Commands", "\n".join(lines), ephemeral=True)

@tree.command(name="yt", description="Search YouTube via your Piped instance.")
@app_commands.describe(query="Search terms", limit="Max links (1–5, default 3)")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def yt_cmd(inter: discord.Interaction, query: str, limit: app_commands.Range[int, 1, 5] = 3):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    results_url = f"{PIPED_FRONTEND_BASE}/results?search_query={quote_plus(query)}"
    lines = []
    enriched = False
    try:
        data = await http_get_json(f"{PIPED_API_BASE}/search", {"q": query, "region": "US"})
        if isinstance(data, list) and data:
            videos = [x for x in data if isinstance(x, dict) and (x.get("type") == "video" or "videoId" in x)]
            for i, v in enumerate(videos[:limit], 1):
                vid = v.get("videoId") or (v.get("url", "").split("v=")[-1] if v.get("url") else None)
                title = v.get("title") or "Untitled"
                ch = v.get("uploaderName") or v.get("uploader") or "Unknown"
                dur = hhmmss(v.get("duration"))
                watch = f"{PIPED_FRONTEND_BASE}/watch?v={vid}" if vid else results_url
                lines.append(f"{i}. [{title}]({watch}) — {ch} — {dur}")
            enriched = bool(lines)
    except RuntimeError:
        pass
    if not enriched:
        lines = [f"Open results: {results_url}"]
    await inter.followup.send(embed=emb("YouTube", "\n".join(lines)), ephemeral=use_ephemeral(inter))

@tree.command(name="wiki", description="Short Wikipedia summary.")
@app_commands.describe(query="Topic to search")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def wiki_cmd(inter: discord.Interaction, query: str):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        sr = await http_get_json("https://en.wikipedia.org/w/api.php", {"action": "opensearch", "search": query, "limit": 1, "namespace": 0, "format": "json"})
        title = (sr[1][0] if isinstance(sr, list) and len(sr) > 1 and sr[1] else "").strip()
    except RuntimeError as e:
        return await inter.followup.send(embed=emb("Wiki", f"Search failed: {e}"), ephemeral=use_ephemeral(inter))
    if not title:
        return await inter.followup.send(embed=emb("Wiki", "No results."), ephemeral=use_ephemeral(inter))
    slug = quote(title.replace(" ", "_"), safe="")
    try:
        js = await http_get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}")
        extract = (js.get("extract") or "No summary.").strip()
        url = js.get("content_urls", {}).get("desktop", {}).get("page", "")
        if len(extract) > 1000:
            extract = extract[:1000] + "…"
        body = f"{extract}\n\n{url}" if url else extract
        return await inter.followup.send(embed=emb("Wiki", body), ephemeral=use_ephemeral(inter))
    except RuntimeError as e:
        return await inter.followup.send(embed=emb("Wiki", f"Fetch failed: {e}"), ephemeral=use_ephemeral(inter))


@tree.command(name="avatar", description="Show a user's avatar.")
@app_commands.describe(user="User to display")
@cooldown_fast
@app_commands.default_permissions(use_application_commands=True)
async def avatar_cmd(inter: discord.Interaction, user: discord.User | None = None):
    target = user or inter.user
    embed = emb(f"Avatar | {target.display_name}", "")
    embed.set_image(url=target.display_avatar.url)
    await inter.response.send_message(embed=embed, ephemeral=use_ephemeral(inter))


@tree.command(name="define", description="Look up a word in the dictionary.")
@app_commands.describe(word="Word to define")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def define_cmd(inter: discord.Interaction, word: str):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        data = await http_get_json(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(word)}"
        )
        if not isinstance(data, list) or not data:
            raise RuntimeError("No definition found")
        first = data[0]
        meanings = first.get("meanings") or []
        meaning = meanings[0] if meanings else {}
        part = meaning.get("partOfSpeech", "")
        defs = meaning.get("definitions") or []
        definition = defs[0].get("definition") if defs else "No definition found."
        desc = f"{definition}"
        if part:
            desc = f"*{part}* — {desc}"
        await inter.followup.send(embed=emb(f"Define | {word}", desc), ephemeral=use_ephemeral(inter))
    except RuntimeError as e:
        await inter.followup.send(embed=emb("Define", f"Error: {e}"), ephemeral=use_ephemeral(inter))


@tree.command(name="search", description="Search the web via DuckDuckGo.")
@app_commands.describe(query="Search terms")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def search_cmd(inter: discord.Interaction, query: str):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        def ddg(q: str):
            with DDGS() as ddgs:
                results = list(ddgs.text(q, safesearch="Off", max_results=5))
                image = next(ddgs.images(q, safesearch="Off", max_results=1), None)
            return results, image
        results, image = await asyncio.to_thread(ddg, query)
        if not results:
            return await inter.followup.send(embed=emb("Search", "No results."), ephemeral=use_ephemeral(inter))
        lines = []
        for i, r in enumerate(results[:5], 1):
            title = r.get("title") or "Untitled"
            url = r.get("href") or r.get("url") or ""
            body = (r.get("body") or r.get("snippet") or "").strip()
            if len(body) > 150:
                body = body[:150] + "…"
            lines.append(f"{i}. [{title}]({url}) — {body}")
        e = emb(f"Search | {query}", "\n".join(lines))
        if image and image.get("image"):
            e.set_image(url=image["image"])
        await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))
    except Exception:
        await inter.followup.send(embed=emb("Search", "Something went wrong."), ephemeral=use_ephemeral(inter))


@tree.command(name="news", description="Search news via DuckDuckGo.")
@app_commands.describe(query="Search terms")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def news_cmd(inter: discord.Interaction, query: str):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        def ddg_news(q: str):
            with DDGS() as ddgs:
                return list(ddgs.news(q, safesearch="Off", max_results=5))
        results = await asyncio.to_thread(ddg_news, query)
        if not results:
            return await inter.followup.send(embed=emb("News", "No results."), ephemeral=use_ephemeral(inter))
        lines = []
        for i, r in enumerate(results[:5], 1):
            title = r.get("title") or "Untitled"
            url = r.get("url") or ""
            source = r.get("source") or ""
            date = r.get("date") or ""
            meta = " — ".join(filter(None, [source, date]))
            line = f"{i}. [{title}]({url})"
            if meta:
                line += f" — {meta}"
            lines.append(line)
        e = emb(f"News | {query}", "\n".join(lines))
        await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))
    except Exception:
        await inter.followup.send(embed=emb("News", "Something went wrong."), ephemeral=use_ephemeral(inter))


class ImageSearchView(discord.ui.View):
    def __init__(self, user_id: int, links: list[str], query: str):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.links = links
        self.query = query
        self.index = 0
        self.message: discord.Message | None = None

    def make_embed(self) -> discord.Embed:
        e = emb(f"Image | {self.query}", f"{self.index + 1}/{len(self.links)}")
        e.set_image(url=self.links[self.index])
        return e

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        return inter.user.id == self.user_id

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def prev(self, inter: discord.Interaction, _button: discord.ui.Button):
        self.index = (self.index - 1) % len(self.links)
        await inter.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, inter: discord.Interaction, _button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.links)
        await inter.response.edit_message(embed=self.make_embed(), view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)


@tree.command(name="image", description="Search images via Google.")
@app_commands.describe(query="Search terms")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def image_cmd(inter: discord.Interaction, query: str):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return await inter.followup.send(embed=emb("Image", "API not configured."), ephemeral=use_ephemeral(inter))
    try:
        data = await http_get_json(
            "https://www.googleapis.com/customsearch/v1",
            {"key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "q": query, "searchType": "image", "safe": "off", "num": 10},
        )
        items = data.get("items") or []
        links = [item.get("link") for item in items if item.get("link")]
        if not links:
            raise RuntimeError("No results")
    except RuntimeError as e:
        return await inter.followup.send(embed=emb("Image", f"Search failed: {e}"), ephemeral=use_ephemeral(inter))
    view = ImageSearchView(inter.user.id, links, query)
    msg = await inter.followup.send(embed=view.make_embed(), view=view, ephemeral=use_ephemeral(inter))
    view.message = msg


@tree.command(name="dog", description="Random dog picture.")
@cooldown_fast
@app_commands.default_permissions(use_application_commands=True)
async def dog_cmd(inter: discord.Interaction):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        js = await http_get_json("https://dog.ceo/api/breeds/image/random")
        url = js.get("message")
        if not url:
            raise RuntimeError("no image")
        e = emb("Dog", "Here you go 🐶")
        e.set_image(url=url)
        await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))
    except RuntimeError as e:
        await inter.followup.send(embed=emb("Dog", f"Error: {e}"), ephemeral=use_ephemeral(inter))


@tree.command(name="cat", description="Random cat picture.")
@cooldown_fast
@app_commands.default_permissions(use_application_commands=True)
async def cat_cmd(inter: discord.Interaction):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        js = await http_get_json("https://api.thecatapi.com/v1/images/search")
        url = js[0].get("url") if isinstance(js, list) and js else None
        if not url:
            raise RuntimeError("no image")
        e = emb("Cat", "Here you go 🐱")
        e.set_image(url=url)
        await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))
    except RuntimeError as e:
        await inter.followup.send(embed=emb("Cat", f"Error: {e}"), ephemeral=use_ephemeral(inter))


class WeatherStateButton(discord.ui.Button):
    def __init__(self, g: dict, choice: str):
        label = g.get("admin1") or "Unknown"
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.g = g
        self.choice = choice

    async def callback(self, inter: discord.Interaction):
        # Defer so we have time to fetch weather data before editing the message
        await inter.response.defer()
        await send_weather_from_geo(inter, self.g, self.choice, edit=True)


class WeatherStateView(discord.ui.View):
    def __init__(self, options: list[dict], choice: str):
        super().__init__(timeout=30)
        for g in options:
            self.add_item(WeatherStateButton(g, choice))


async def send_weather_from_geo(inter: discord.Interaction, g0: dict, choice: str, *, edit: bool = False):
    lat, lon = g0["latitude"], g0["longitude"]
    parts = [g0.get("name", ""), g0.get("admin1") or "", g0.get("country") or ""]
    display_name = ", ".join(p for p in parts if p)
    temp_unit = "fahrenheit" if choice == "imperial" else ("celsius" if choice == "metric" else ("fahrenheit" if (g0.get("country_code","") or "") == "US" else "celsius"))
    wind_unit = "mph" if temp_unit == "fahrenheit" else "ms"
    try:
        wx = await http_get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "temperature_unit": temp_unit,
                "windspeed_unit": wind_unit,
                "timezone": "auto",
            },
        )
        cur = (wx.get("current") or {})
        temp = cur.get("temperature_2m")
        wind = cur.get("wind_speed_10m")
        code = cur.get("weather_code")
        WMAP = {
            0: "Clear",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Rime fog",
            51: "Light drizzle",
            53: "Drizzle",
            55: "Heavy drizzle",
            61: "Light rain",
            63: "Rain",
            65: "Heavy rain",
            71: "Light snow",
            73: "Snow",
            75: "Heavy snow",
            80: "Light showers",
            81: "Showers",
            82: "Heavy showers",
            95: "Thunderstorm",
            96: "Thunderstorm w/ hail",
            99: "Severe thunderstorm",
        }
        cond = WMAP.get(code, "—")
        unit_sym = "°F" if temp_unit == "fahrenheit" else "°C"
        wind_sym = "mph" if wind_unit == "mph" else "m/s"
        if temp is None or wind is None:
            e = emb("Weather", "No data available.")
            if edit:
                await inter.followup.edit_message(inter.message.id, embed=e, view=None)
            else:
                await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))
            return
        desc = (
            f"Location - {display_name}\n"
            f"Temperature - {temp} {unit_sym}\n"
            f"Wind - {wind} {wind_sym}\n"
            f"Conditions - {cond}\n{now_utc_iso()}"
        )
        e = emb("Weather", desc)
        if edit:
            await inter.followup.edit_message(inter.message.id, embed=e, view=None)
        else:
            await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))
    except RuntimeError as ex:
        e = emb("Weather", f"Fetch failed: {ex}")
        if edit:
            await inter.followup.edit_message(inter.message.id, embed=e, view=None)
        else:
            await inter.followup.send(embed=e, ephemeral=use_ephemeral(inter))


@tree.command(name="weather", description="Current weather for a place.")
@app_commands.describe(place="City or place name (e.g., Chicago, IL or London)", unit="Units: auto, metric, imperial")
@app_commands.choices(unit=[app_commands.Choice(name="auto", value="auto"), app_commands.Choice(name="metric (°C, m/s)", value="metric"), app_commands.Choice(name="imperial (°F, mph)", value="imperial")])
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def weather_cmd(inter: discord.Interaction, place: str, unit: app_commands.Choice[str] | None = None):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        geo = await http_get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": place, "count": 10, "language": "en", "format": "json"},
        )
        results = geo.get("results") if geo else None
        if not results:
            return await inter.followup.send(embed=emb("Weather", "Location not found."), ephemeral=use_ephemeral(inter))
    except RuntimeError as e:
        return await inter.followup.send(embed=emb("Weather", f"Geocoding failed: {e}"), ephemeral=use_ephemeral(inter))

    choice = unit.value if unit else "auto"
    us_matches = [g for g in results if g.get("country_code") == "US" and (g.get("name", "").lower() == place.lower())]
    if len(us_matches) > 1:
        view = WeatherStateView(us_matches, choice)
        return await inter.followup.send(
            embed=emb("Weather", "Multiple matches found. Choose a state."),
            view=view,
            ephemeral=use_ephemeral(inter),
        )

    g0 = us_matches[0] if us_matches else results[0]
    await send_weather_from_geo(inter, g0, choice)

@tree.command(name="resync", description="Refresh slash commands (owner only).")
@app_commands.describe(scope="Where to sync")
@app_commands.choices(scope=[app_commands.Choice(name="guild", value="guild"), app_commands.Choice(name="global", value="global"), app_commands.Choice(name="guild-clear-then-global", value="guild_clear")])
@cooldown_fast
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def resync_cmd(inter: discord.Interaction, scope: app_commands.Choice[str]):
    if not is_owner(inter):
        return await reply_embed(inter, "Denied", "Only the owner can do that.")
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        if scope.value == "guild":
            if not GUILD_ID:
                return await inter.followup.send(embed=emb("Resync", "No GUILD_ID set."), ephemeral=use_ephemeral(inter))
            synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
            return await inter.followup.send(embed=emb("Resync", f"Guild sync OK ({len(synced)} commands)."), ephemeral=use_ephemeral(inter))
        elif scope.value == "global":
            synced = await tree.sync()
            return await inter.followup.send(embed=emb("Resync", f"Global sync OK ({len(synced)} commands)."), ephemeral=use_ephemeral(inter))
        elif scope.value == "guild_clear":
            if not GUILD_ID:
                return await inter.followup.send(embed=emb("Resync", "No GUILD_ID set."), ephemeral=use_ephemeral(inter))
            tree.clear_commands(guild=discord.Object(id=GUILD_ID))
            tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
            synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
            return await inter.followup.send(embed=emb("Resync", f"Cleared & copied global → guild ({len(synced)} commands)."), ephemeral=use_ephemeral(inter))
        else:
            return await inter.followup.send(embed=emb("Resync", "Unknown scope."), ephemeral=use_ephemeral(inter))
    except Exception as e:
        return await inter.followup.send(embed=emb("Resync", f"Failed: {e}"), ephemeral=use_ephemeral(inter))

# quick fuzzy ticker autocorrect
def normalize_symbol(s: str) -> str:
    fixes = {
        "APPL": "AAPL",
        "TESLA": "TSLA",
        "MICROSOFT": "MSFT",
        "GOOGLE": "GOOGL",
        "AMAZON": "AMZN",
        "FACEBOOK": "META",
        "NVIDIA": "NVDA",
        "NETFLIX": "NFLX",
        "INTEL": "INTC",
    }
    s = s.strip().upper()
    s = fixes.get(s, s)
    tickers = [
        "AAPL",
        "TSLA",
        "MSFT",
        "GOOGL",
        "AMZN",
        "META",
        "NVDA",
        "NFLX",
        "AMD",
        "INTC",
    ]
    if s in tickers:
        return s
    match = difflib.get_close_matches(s, tickers, n=1, cutoff=0.6)
    return match[0] if match else s

def fetch_price_and_chart(symbol: str):
    sym = normalize_symbol(symbol)
    end = dt.datetime.utcnow()
    # fetch a bit more than 90 days to ensure enough data for MA20
    hist = yf.download(
        sym,
        period="120d",
        interval="1d",
        progress=False,
        auto_adjust=True,
    )
    if hist is None or hist.empty:
        return None, None, None, None, None

    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)

    # trim to last 90 days if available
    hist = hist.tail(90).copy()
    hist["MA20"] = hist["Close"].rolling(20).mean()

    closes = hist["Close"].dropna()

    # intraday for freshest price fallback
    intraday = yf.download(sym, period="1d", interval="1m", progress=False, auto_adjust=True)
    if intraday is not None and not intraday.empty:
        if isinstance(intraday.columns, pd.MultiIndex):
            intraday.columns = intraday.columns.get_level_values(0)
        last_price = float(intraday["Close"].dropna().iloc[-1])
    else:
        last_price = float(closes.iloc[-1])

    # daily and monthly change percentages
    prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else last_price
    month_close = float(closes.iloc[-21]) if len(closes) >= 21 else closes.iloc[0]
    day_change_pct = ((last_price / prev_close) - 1) * 100 if prev_close else 0.0
    month_change_pct = ((last_price / month_close) - 1) * 100 if month_close else 0.0

    arrow = "▲" if day_change_pct >= 0 else "▼"
    title = f"{sym}  {arrow} {abs(day_change_pct):.2f}%  •  Last price ${last_price:,.2f}"

    buf = io.BytesIO()
    if USE_CANDLES and {"Open", "High", "Low", "Close"}.issubset(hist.columns):
        addplots = [
            mpf.make_addplot(hist["MA20"], color="orange", width=1.2),
            mpf.make_addplot(
                pd.Series(last_price, index=[hist.index[-1]]),
                type="scatter",
                color="white",
                markersize=40,
            ),
        ]
        fig, axes = mpf.plot(
            hist,
            type="candle",
            style="charcoal",
            addplot=addplots,
            returnfig=True,
            figsize=(7, 3.8),
        )
        ax = axes[0]
        locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.2f}"))
        ax.set_title(title)
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
    else:
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(7, 3.8), dpi=200)
        ax.plot(hist.index, hist["Close"], color="#4CB391", linewidth=2)
        ax.fill_between(hist.index, hist["Close"], color="#4CB391", alpha=0.2)
        ax.plot(hist.index, hist["MA20"], color="#FFE066", linewidth=1.5)
        ax.scatter(
            hist.index[-1],
            last_price,
            color="white",
            edgecolors="black",
            zorder=5,
            s=20,
        )
        locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.2f}"))
        ax.grid(color="gray", alpha=0.3)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)

    buf.seek(0)
    return sym, last_price, day_change_pct, month_change_pct, buf

@tree.command(name="stock", description="Show current price and chart for a stock")
@app_commands.describe(symbol="Ticker (e.g., AAPL, TSLA)")
@cooldown_medium
@app_commands.default_permissions(use_application_commands=True)
async def stock(inter: discord.Interaction, symbol: str):
    await inter.response.defer(ephemeral=use_ephemeral(inter), thinking=True)
    try:
        sym, last_price, day_change_pct, month_change_pct, img = await asyncio.to_thread(
            fetch_price_and_chart, symbol
        )
        if sym is None:
            return await inter.followup.send(
                embed=emb("Stock", f"Couldn't find data for `{symbol}`."), ephemeral=use_ephemeral(inter)
            )

        arrow_day = "▲" if day_change_pct >= 0 else "▼"
        arrow_month = "▲" if month_change_pct >= 0 else "▼"
        desc = (
            f"**Last Price:** ${last_price:,.2f}\n"
            f"**Day Change:** {arrow_day} {abs(day_change_pct):.2f}%\n"
            f"**Month Change:** {arrow_month} {abs(month_change_pct):.2f}%\n"
            "🟢 Price • 🟡 20-day moving average • ⚪ Latest price"
            f"\n\nhttps://www.tradingview.com/symbols/{sym}"
        )
        file = discord.File(img, filename=f"{sym}.png")
        embed = emb(f"Stocks | {sym}", desc)
        embed.set_image(url=f"attachment://{sym}.png")
        await inter.followup.send(embed=embed, file=file, ephemeral=use_ephemeral(inter))
    except Exception as e:
        await inter.followup.send(embed=emb("Stock", f"Error: {e}"), ephemeral=use_ephemeral(inter))

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
    raise error

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN")
    try:
        client.run(TOKEN)
    finally:
        if _http and not _http.closed:
            asyncio.run(_http.close())
