import os
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
LAVENDER = 0xB57EDC  # tweak this hex to adjust the look

# ===== client (slash-only) =====
intents = discord.Intents.default()
intents.guilds = True
client = commands.Bot(command_prefix="!", intents=intents)  # prefix unused; slash only
tree = client.tree

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
            return await reply_embed(inter, "Role missing", "Couldn’t find the **Changes** role.")
        member: discord.Member = inter.user
        if role in member.roles:
            await member.remove_roles(role, reason="RolePicker toggle: remove Changes")
            return await reply_embed(inter, "Updated", "Removed **Changes**.", ephemeral=True)
        else:
            await member.add_roles(role, reason="RolePicker toggle: add Changes")
            return await reply_embed(inter, "Updated", "Added **Changes**.", ephemeral=True)

    @discord.ui.button(label="Status Alerts", style=discord.ButtonStyle.secondary, custom_id="rp_status")
    async def btn_status(self, inter: discord.Interaction, _button: discord.ui.Button):
        if not inter.guild:
            return await reply_embed(inter, "Not available", "This only works inside a server.")
        role = inter.guild.get_role(ROLE_STATUS_ID)
        if not role:
            return await reply_embed(inter, "Role missing", "Couldn’t find the **Status Alerts** role.")
        member: discord.Member = inter.user
        if role in member.roles:
            await member.remove_roles(role, reason="RolePicker toggle: remove Status")
            return await reply_embed(inter, "Updated", "Removed **Status Alerts**.", ephemeral=True)
        else:
            await member.add_roles(role, reason="RolePicker toggle: add Status")
            return await reply_embed(inter, "Updated", "Added **Status Alerts**.", ephemeral=True)

async def send_role_picker_embed():
    if not ROLE_PICK_CHANNEL_ID:
        return
    ch = client.get_channel(ROLE_PICK_CHANNEL_ID) or await client.fetch_channel(ROLE_PICK_CHANNEL_ID)
    desc = (
        "Choose what you want to be notified about.\n\n"
        "**Changes** — posts from the changelog\n"
        "**Status Alerts** — service up/down notes\n\n"
        "_Click a button to toggle. No pings unless you opt in._"
    )
    e = emb("Notification Preferences", desc)
    e.set_footer(text=f"Last posted {now_utc_iso()}")
    await ch.send(embed=e, view=RolePicker())

# ===== presence + sync =====
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

# ===== cooldowns (“safe walls”) =====
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
        f"Presence: watching *over homelab*\n"
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
    client.run(TOKEN)
