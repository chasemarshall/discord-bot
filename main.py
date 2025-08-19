import os
import discord
from discord import app_commands
from discord.ext import commands

# ===== env config =====
TOKEN      = os.getenv("DISCORD_TOKEN", "").strip()
OWNER_ID   = int(os.getenv("DISCORD_OWNER_ID", "0") or 0)
GUILD_ID   = int(os.getenv("DISCORD_GUILD_ID", "0") or 0)

ROLE_CHANGES_ID      = int(os.getenv("ROLE_CHANGES_ID", "0") or 0)
ROLE_STATUS_ID       = int(os.getenv("ROLE_STATUS_ID", "0") or 0)
ROLE_PICK_CHANNEL_ID = int(os.getenv("ROLE_PICK_CHANNEL_ID", "0") or 0)

# ===== client (slash-only; no message_content) =====
intents = discord.Intents.default()
intents.guilds = True
client = commands.Bot(command_prefix="!", intents=intents)  # prefix unused; slash only
tree = client.tree

# ===== helpers =====
def now_utc_iso():
    return discord.utils.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def is_owner(inter: discord.Interaction) -> bool:
    return OWNER_ID and inter.user and inter.user.id == OWNER_ID

async def owner_only(inter: discord.Interaction):
    await inter.response.send_message("nope.", ephemeral=True)

def emb(title: str, desc: str, color: int) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color)
    e.timestamp = discord.utils.utcnow()
    return e

# ===== role picker =====
class RolePicker(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Get Changes", style=discord.ButtonStyle.success, custom_id="rp_changes", emoji="🛠️")
    async def btn_changes(self, inter: discord.Interaction, _button: discord.ui.Button):
        if not inter.guild:
            return await inter.response.send_message("Not in a server.", ephemeral=True)
        role = inter.guild.get_role(ROLE_CHANGES_ID)
        if not role:
            return await inter.response.send_message("Role not found (Changes).", ephemeral=True)
        member: discord.Member = inter.user  # provided on interactions
        if role in member.roles:
            await member.remove_roles(role, reason="RolePicker toggle: remove Changes")
            await inter.response.send_message("Removed **Changes** role.", ephemeral=True)
        else:
            await member.add_roles(role, reason="RolePicker toggle: add Changes")
            await inter.response.send_message("Added **Changes** role.", ephemeral=True)

    @discord.ui.button(label="Get Status Alerts", style=discord.ButtonStyle.primary, custom_id="rp_status", emoji="📡")
    async def btn_status(self, inter: discord.Interaction, _button: discord.ui.Button):
        if not inter.guild:
            return await inter.response.send_message("Not in a server.", ephemeral=True)
        role = inter.guild.get_role(ROLE_STATUS_ID)
        if not role:
            return await inter.response.send_message("Role not found (Status).", ephemeral=True)
        member: discord.Member = inter.user
        if role in member.roles:
            await member.remove_roles(role, reason="RolePicker toggle: remove Status")
            await inter.response.send_message("Removed **Status** role.", ephemeral=True)
        else:
            await member.add_roles(role, reason="RolePicker toggle: add Status")
            await inter.response.send_message("Added **Status** role.", ephemeral=True)

async def send_role_picker_embed():
    if not ROLE_PICK_CHANNEL_ID:
        return
    ch = client.get_channel(ROLE_PICK_CHANNEL_ID) or await client.fetch_channel(ROLE_PICK_CHANNEL_ID)
    desc = (
        "**Choose what you want notifications for:**\n\n"
        "**Changes** — Updates from the changelog channel\n"
        "**Status Alerts** — When services go up or down\n\n"
        "_Click a button to toggle. No pings unless you opt in._"
    )
    e = emb("Notification Preferences", desc, 0x57F287)
    e.set_footer(text=f"Last posted {now_utc_iso()}")
    await ch.send(embed=e, view=RolePicker())

# ===== presence + sync =====
@client.event
async def on_ready():
    # presence (like your old one)
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name="over homelab"),
    )
    # persistent buttons
    client.add_view(RolePicker())

    # guild-scoped sync for instant updates
    try:
        if GUILD_ID:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
        else:
            await tree.sync()
        print(f"✅ Logged in as {client.user} — commands synced.")
    except Exception as e:
        print("Sync failed:", e)

# ===== cooldowns (“safe walls”) =====
# use per-user cooldowns; feel free to adjust seconds/rate
cooldown_user_fast   = app_commands.checks.cooldown(1, 3.0)   # 1 use / 3 sec
cooldown_user_medium = app_commands.checks.cooldown(2, 10.0)  # 2 uses / 10 sec

# ===== commands =====

@tree.command(name="rolesetup", description="Post the Notification Preferences role-picker (owner only).")
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def rolesetup_cmd(inter: discord.Interaction):
    if not is_owner(inter):
        return await owner_only(inter)
    await inter.response.send_message("Posting role picker…", ephemeral=True)
    await send_role_picker_embed()
    await inter.followup.send("Done.", ephemeral=True)

@tree.command(name="status", description="Show the bot status/presence info.")
@cooldown_user_fast
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def status_cmd(inter: discord.Interaction):
    u = client.user
    desc = (
        f"**Bot:** {u.mention if u else '—'}\n"
        f"**Presence:** Watching *over homelab*\n"
        f"**Latency:** `{round(client.latency * 1000)} ms`\n"
        f"*{now_utc_iso()}*"
    )
    await inter.response.send_message(embed=emb("📈 Status", desc, 0x3498DB), ephemeral=True)

@tree.command(name="purge", description="Delete a number of recent messages in this channel.")
@app_commands.describe(count="How many messages to delete (1–100)")
@cooldown_user_medium
@app_commands.default_permissions(manage_messages=True)  # UI shows required perms
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def purge_cmd(inter: discord.Interaction, count: app_commands.Range[int, 1, 100]):
    await inter.response.defer(ephemeral=True, thinking=True)
    deleted = await inter.channel.purge(limit=count, bulk=True)  # type: ignore
    await inter.followup.send(f"🧹 Deleted **{len(deleted)}** messages.", ephemeral=True)

@tree.command(name="help", description="Show available commands.")
@cooldown_user_fast
@app_commands.guilds(discord.Object(id=GUILD_ID)) if GUILD_ID else (lambda f: f)
async def help_cmd(inter: discord.Interaction):
    lines = [
        "**/rolesetup** — Post role picker (owner only)",
        "**/status** — Bot presence + latency",
        "**/purge** — Delete recent messages (requires Manage Messages)",
        "**/help** — This help",
    ]
    await inter.response.send_message(embed=emb("📝 Commands", "\n".join(lines), 0x5865F2), ephemeral=True)

# ===== error handling =====
@tree.error
async def on_app_command_error(inter: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        return await inter.response.send_message(
            f"Slow down. Try again in `{error.retry_after:.1f}s`.", ephemeral=True
        )
    if isinstance(error, app_commands.MissingPermissions):
        return await inter.response.send_message("You’re missing permissions for that.", ephemeral=True)
    if isinstance(error, app_commands.BotMissingPermissions):
        return await inter.response.send_message("I’m missing permissions for that.", ephemeral=True)
    try:
        if inter.response.is_done():
            await inter.followup.send("Something went wrong.", ephemeral=True)
        else:
            await inter.response.send_message("Something went wrong.", ephemeral=True)
    except Exception:
        pass
    raise error  # still log to console

# ===== run =====
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN")
    client.run(TOKEN)
