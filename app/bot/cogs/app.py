import asyncio
from datetime import datetime, timedelta, timezone

import app.bot.helper.embyhelper as emby
import app.bot.helper.db as db
import app.bot.helper.emailhelper as emailhelper
import app.bot.helper.jellyfinhelper as jelly
import app.bot.helper.plexhelper as plexhelper
import discord
import texttable
from discord import app_commands
from discord.ext import commands, tasks
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer

from app.bot.helper.confighelper import *
from app.bot.helper.message import *
from app.bot.helper.textformat import bcolors

CONFIG_PATH = 'app/config/config.ini'
BOT_SECTION = 'bot_envs'

plex_configured = True
jellyfin_configured = True
emby_configured = True

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

plex_token_configured = True
try:
    PLEX_TOKEN = config.get(BOT_SECTION, 'plex_token')
    PLEX_BASE_URL = config.get(BOT_SECTION, 'plex_base_url')
except:
    print("No Plex auth token details found")
    plex_token_configured = False

# Get Plex config
try:
    PLEXUSER = config.get(BOT_SECTION, 'plex_user')
    PLEXPASS = config.get(BOT_SECTION, 'plex_pass')
    PLEX_SERVER_NAME = config.get(BOT_SECTION, 'plex_server_name')
except:
    print("No Plex login info found")
    if not plex_token_configured:
        print("Could not load plex config")
        plex_configured = False

# Get Plex roles config
try:
    plex_roles = config.get(BOT_SECTION, 'plex_roles')
except:
    plex_roles = None
if plex_roles:
    plex_roles = list(plex_roles.split(','))
else:
    plex_roles = []

# Get Plex libs config
try:
    Plex_LIBS = config.get(BOT_SECTION, 'plex_libs')
except:
    Plex_LIBS = None
if Plex_LIBS is None:
    Plex_LIBS = ["all"]
else:
    Plex_LIBS = list(Plex_LIBS.split(','))
    
# Get Jellyfin config
try:
    JELLYFIN_SERVER_URL = config.get(BOT_SECTION, 'jellyfin_server_url')
    JELLYFIN_API_KEY = config.get(BOT_SECTION, "jellyfin_api_key")
except:
    jellyfin_configured = False

# Get Jellyfin roles config
try:
    jellyfin_roles = config.get(BOT_SECTION, 'jellyfin_roles')
except:
    jellyfin_roles = None
if jellyfin_roles:
    jellyfin_roles = list(jellyfin_roles.split(','))
else:
    jellyfin_roles = []

# Get Jellyfin libs config
try:
    jellyfin_libs = config.get(BOT_SECTION, 'jellyfin_libs')
except:
    jellyfin_libs = None
if jellyfin_libs is None:
    jellyfin_libs = ["all"]
else:
    jellyfin_libs = list(jellyfin_libs.split(','))

# Get Emby config
try:
    EMBY_SERVER_URL = config.get(BOT_SECTION, 'emby_server_url')
    EMBY_API_KEY = config.get(BOT_SECTION, "emby_api_key")
    if not EMBY_SERVER_URL or not EMBY_API_KEY:
        raise ValueError
except:
    emby_configured = False

try:
    EMBY_EXTERNAL_URL = config.get(BOT_SECTION, "emby_external_url")
    if not EMBY_EXTERNAL_URL:
        EMBY_EXTERNAL_URL = EMBY_SERVER_URL
except:
    EMBY_EXTERNAL_URL = EMBY_SERVER_URL
    print("Could not get Emby external url. Defaulting to server url.")

# Get Emby roles config
try:
    emby_roles = config.get(BOT_SECTION, 'emby_roles')
except:
    emby_roles = None
if emby_roles:
    emby_roles = list(emby_roles.split(','))
else:
    emby_roles = []

# Get Emby libs config
try:
    emby_libs = config.get(BOT_SECTION, 'emby_libs')
except:
    emby_libs = None
if emby_libs is None:
    emby_libs = ["all"]
else:
    emby_libs = list(emby_libs.split(','))

# Get Enable config
try:
    USE_JELLYFIN = config.get(BOT_SECTION, 'jellyfin_enabled')
    USE_JELLYFIN = USE_JELLYFIN.lower() == "true"
except:
    USE_JELLYFIN = False

try:
    USE_PLEX = config.get(BOT_SECTION, "plex_enabled")
    USE_PLEX = USE_PLEX.lower() == "true"
except:
    USE_PLEX = False

try:
    USE_EMBY = config.get(BOT_SECTION, "emby_enabled")
    USE_EMBY = USE_EMBY.lower() == "true"
except:
    USE_EMBY = False

try:
    JELLYFIN_EXTERNAL_URL = config.get(BOT_SECTION, "jellyfin_external_url")
    if not JELLYFIN_EXTERNAL_URL:
        JELLYFIN_EXTERNAL_URL = JELLYFIN_SERVER_URL
except:
    JELLYFIN_EXTERNAL_URL = JELLYFIN_SERVER_URL
    print("Could not get Jellyfin external url. Defaulting to server url.")

if USE_PLEX and plex_configured:
    try:
        print("Connecting to Plex......")
        if plex_token_configured and PLEX_TOKEN and PLEX_BASE_URL:
            print("Using Plex auth token")
            plex = PlexServer(PLEX_BASE_URL, PLEX_TOKEN)
        else:
            print("Using Plex login info")
            account = MyPlexAccount(PLEXUSER, PLEXPASS)
            plex = account.resource(PLEX_SERVER_NAME).connect()  # returns a PlexServer instance
        print('Logged into plex!')
    except Exception as e:
        # probably rate limited.
        print('Error with plex login. Please check Plex authentication details. If you have restarted the bot multiple times recently, this is most likely due to being ratelimited on the Plex API. Try again in 10 minutes.')
        print(f'Error: {e}')
else:
    print(f"Plex {'disabled' if not USE_PLEX else 'not configured'}. Skipping Plex login.")

if not (USE_EMBY and emby_configured):
    print(f"Emby {'disabled' if not USE_EMBY else 'not configured'}. Skipping Emby integration.")


class app(commands.Cog):
    # App command groups
    plex_commands = app_commands.Group(name="plex", description="Quantum Streams Plex commands")
    jellyfin_commands = app_commands.Group(name="jellyfin", description="Quantum Streams Jellyfin commands")
    emby_commands = app_commands.Group(name="emby", description="Quantum Streams Emby commands")
    quantum_commands = app_commands.Group(name="quantum", description="Quantum Invites general commands")

    def __init__(self, bot):
        self.bot = bot
        self._cached_owner = None
        self.subscription_monitor_loop.start()

    def cog_unload(self):
        self.subscription_monitor_loop.cancel()
        try:
            self.bot.tree.remove_command("quantum")
        except Exception:
            pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('------')
        print("{:^41}".format(f"{BRAND_BOT_NAME.upper()} V {MEMBARR_VERSION}"))
        print(f'Powered for {BRAND_SERVER_NAME}')
        print(f'Logged in as {self.bot.user} (ID: {self.bot.user.id})')
        print('------')

        # TODO: Make these debug statements work. roles are currently empty arrays if no roles assigned.
        if plex_roles is None:
            print('Configure Plex roles to enable auto invite to Plex after a role is assigned.')
        if jellyfin_roles is None:
            print('Configure Jellyfin roles to enable auto invite to Jellyfin after a role is assigned.')
        if emby_roles is None:
            print('Configure Emby roles to enable auto invite to Emby after a role is assigned.')

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

    @staticmethod
    def _format_datetime(dt):
        return dt.astimezone(timezone.utc).isoformat()

    def _find_member(self, user_id):
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                return member, guild
        return None, None

    async def _get_owner(self):
        if not OWNER_ID:
            return None
        try:
            owner_id = int(OWNER_ID)
        except ValueError:
            return None
        if self._cached_owner and self._cached_owner.id == owner_id:
            return self._cached_owner
        owner = self.bot.get_user(owner_id)
        if not owner:
            try:
                owner = await self.bot.fetch_user(owner_id)
            except Exception as exc:
                print(f"Unable to fetch owner user: {exc}")
                return None
        self._cached_owner = owner
        return owner

    async def _get_alert_channel(self):
        if not SUBSCRIPTION_ALERT_CHANNEL_ID:
            return None
        try:
            channel_id = int(SUBSCRIPTION_ALERT_CHANNEL_ID)
        except ValueError:
            print("subscription_alert_channel_id is not a valid integer.")
            return None
        channel = self.bot.get_channel(channel_id)
        if channel:
            return channel
        try:
            channel = await self.bot.fetch_channel(channel_id)
            return channel
        except Exception as exc:
            print(f"Unable to fetch alert channel: {exc}")
            return None

    async def _send_embed(self, recipient, title, description, color=discord.Color.blurple(), ephemeral=False):
        embed = discord.Embed(title=title, description=description, color=color)
        try:
            if isinstance(recipient, discord.InteractionResponse):
                await recipient.send_message(embed=embed, ephemeral=ephemeral)
            else:
                try:
                    await recipient.send(embed=embed, ephemeral=ephemeral)
                except TypeError:
                    await recipient.send(embed=embed)
        except Exception as exc:
            print(f"Unable to send message to {getattr(recipient, 'name', recipient)}: {exc}")

    async def _notify_management(self, title, description):
        channel = await self._get_alert_channel()
        if channel:
            await self._send_embed(channel, title, description, color=discord.Color.orange(), ephemeral=False)
            return
        owner = await self._get_owner()
        if owner:
            await self._send_embed(owner, title, description, color=discord.Color.orange(), ephemeral=False)

    @staticmethod
    def _get_member_email(user_id: str):
        email = db.get_useremail(user_id)
        if not isinstance(email, str):
            return None
        normalized = email.strip()
        if normalized in ("", "No email found", "error in fetching from db"):
            return None
        return normalized

    async def _send_subscription_email(self, member: discord.Member, subject: str, body: str):
        if not emailhelper.is_email_configured():
            return False
        email_address = self._get_member_email(str(member.id))
        if not email_address:
            return False
        success = emailhelper.send_email(subject, body, email_address)
        if not success:
            await self._notify_management(
                f"Email delivery failed for {member.display_name}",
                f"Could not email {email_address} regarding subscription update."
            )
        return success

    async def _maybe_set_default_subscription(self, user_id):
        if SUBSCRIPTION_DEFAULT_DAYS <= 0:
            return
        info = db.get_subscription(user_id)
        if info and info.get("expires_at"):
            return
        expires_at = datetime.now(timezone.utc) + timedelta(days=SUBSCRIPTION_DEFAULT_DAYS)
        db.set_subscription(user_id, self._format_datetime(expires_at))
        print(f"Subscription for {user_id} set to default expiry on {expires_at.date()}.")

    async def _handle_subscription_reminder(self, member, expires_at, days_until):
        formatted_date = expires_at.strftime('%Y-%m-%d')
        await self._send_embed(
            member,
            f"{BRAND_SERVER_NAME} subscription reminder",
            f"Hey {member.name}, your access to {BRAND_SERVER_NAME} expires in **{days_until} day(s)** on **{formatted_date}**. "
            f"Please renew to keep enjoying the library.",
            color=discord.Color.gold()
        )
        await self._notify_management(
            f"Subscription reminder for {member.display_name}",
            f"{member.mention} expires in {days_until} day(s) on {formatted_date}."
        )
        await self._send_subscription_email(
            member,
            f"{BRAND_SERVER_NAME} subscription reminder",
            (
                f"Hello {member.name},\n\n"
                f"This is a friendly reminder that your {BRAND_SERVER_NAME} access expires in {days_until} day(s) "
                f"on {formatted_date}. Please renew with the Quantum Streams team to keep streaming without interruption.\n\n"
                f"- {BRAND_BOT_NAME}"
            )
        )

    async def _handle_subscription_overdue(self, member, expires_at, grace_ends):
        formatted_expired = expires_at.strftime('%Y-%m-%d')
        formatted_grace = grace_ends.strftime('%Y-%m-%d')
        await self._send_embed(
            member,
            f"{BRAND_SERVER_NAME} subscription overdue",
            f"Hi {member.name}, your {BRAND_SERVER_NAME} subscription expired on **{formatted_expired}**. "
            f"Please renew before **{formatted_grace}** to avoid losing access.",
            color=discord.Color.orange()
        )
        await self._notify_management(
            f"{member.display_name} is overdue",
            f"{member.mention}'s subscription expired on {formatted_expired}. Grace ends {formatted_grace}."
        )
        await self._send_subscription_email(
            member,
            f"{BRAND_SERVER_NAME} subscription overdue",
            (
                f"Hello {member.name},\n\n"
                f"Your {BRAND_SERVER_NAME} subscription expired on {formatted_expired}. "
                f"You have until {formatted_grace} to renew before your access is removed. "
                f"Please reach out to the Quantum Streams staff if you need assistance.\n\n"
                f"- {BRAND_BOT_NAME}"
            )
        )

    async def _revoke_member_access(self, member):
        user_id = str(member.id)
        removed_roles = []
        target_roles = set()
        if plex_roles:
            target_roles.update(plex_roles)
        if jellyfin_roles:
            target_roles.update(jellyfin_roles)
        if emby_roles:
            target_roles.update(emby_roles)

        for role_name in target_roles:
            role = discord.utils.get(member.guild.roles, name=role_name)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role, reason=f"{BRAND_BOT_NAME} subscription expired")
                    removed_roles.append(role.name)
                except Exception as exc:
                    print(f"Failed to remove role {role_name} from {member.display_name}: {exc}")

        if USE_PLEX and plex_configured:
            email = db.get_useremail(user_id)
            if email not in ("No email found", "error in fetching from db"):
                try:
                    plexhelper.plexremove(plex, email)
                    db.remove_email(user_id)
                except Exception as exc:
                    print(f"Failed to revoke Plex for {member.display_name}: {exc}")

        if USE_JELLYFIN and jellyfin_configured:
            jellyfin_username = db.get_jellyfin_username(user_id)
            if jellyfin_username not in ("No users found", "error in fetching from db"):
                if jelly.remove_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, jellyfin_username):
                    db.remove_jellyfin(user_id)

        if USE_EMBY and emby_configured:
            emby_username = db.get_emby_username(user_id)
            if emby_username not in ("No users found", "error in fetching from db"):
                if emby.remove_user(EMBY_SERVER_URL, EMBY_API_KEY, emby_username):
                    db.remove_emby(user_id)

        return removed_roles

    async def _handle_subscription_expired(self, member, expires_at):
        await self._send_embed(
            member,
            f"{BRAND_SERVER_NAME} access revoked",
            f"Your subscription expired on **{expires_at.strftime('%Y-%m-%d')}** and the grace period has ended. "
            "Access roles have been removed. Reach out to renew and regain access.",
            color=discord.Color.red()
        )
        removed_roles = await self._revoke_member_access(member)
        db.clear_subscription(str(member.id))
        await self._notify_management(
            f"{member.display_name} access revoked",
            f"Removed roles {', '.join(removed_roles) if removed_roles else 'none'} from {member.mention} after subscription expiry."
        )
        await self._send_subscription_email(
            member,
            f"{BRAND_SERVER_NAME} access revoked",
            (
                f"Hello {member.name},\n\n"
                f"Your {BRAND_SERVER_NAME} subscription expired on {expires_at.strftime('%Y-%m-%d')} and the grace period has now ended. "
                "Your access roles have been removed. Contact the Quantum Streams team when you're ready to renew.\n\n"
                f"- {BRAND_BOT_NAME}"
            )
        )

    @tasks.loop(hours=1)
    async def subscription_monitor_loop(self):
        if not self.bot.is_ready():
            return

        now = datetime.now(timezone.utc)
        reminder_days = SUBSCRIPTION_REMINDER_DAYS if SUBSCRIPTION_REMINDER_DAYS else []

        for record in db.list_subscriptions():
            user_key = record.get("discord_username")
            if not user_key:
                continue
            try:
                user_id = int(user_key)
            except (TypeError, ValueError):
                continue

            expires_at = self._parse_datetime(record.get("expires_at"))
            if not expires_at:
                continue

            member, guild = self._find_member(user_id)
            if not member or not guild:
                continue

            reminder_flags = {flag.strip() for flag in record.get("reminder_flags", "").split(',') if flag.strip()}
            delta = expires_at - now

            if delta.total_seconds() > 0:
                days_until = int(delta.total_seconds() // 86400)
                for day in reminder_days:
                    if day < 0:
                        continue
                    if str(day) in reminder_flags:
                        continue
                    if days_until == day:
                        await self._handle_subscription_reminder(member, expires_at, day)
                        db.mark_reminder_sent(str(user_id), day, self._format_datetime(now))
                        break
            else:
                grace_ends = expires_at + timedelta(days=SUBSCRIPTION_GRACE_DAYS)
                if now < grace_ends:
                    if "overdue" not in reminder_flags:
                        await self._handle_subscription_overdue(member, expires_at, grace_ends)
                        db.mark_reminder_sent(str(user_id), "overdue", self._format_datetime(now))
                else:
                    await self._handle_subscription_expired(member, expires_at)

    @subscription_monitor_loop.before_loop
    async def before_subscription_monitor(self):
        await self.bot.wait_until_ready()
    
    async def getemail(self, after):
        email = None
        await embedinfo(after, f"Welcome to {BRAND_SERVER_NAME}! Please reply with the email you use for Plex so we can invite you to {PLEX_SERVER_NAME or 'Plex'}.")
        await embedinfo(after, "If you do not respond within 24 hours, the request will be cancelled, and the team will need to add you manually.")
        while(email == None):
            def check(m):
                return m.author == after and not m.guild
            try:
                email = await self.bot.wait_for('message', timeout=86400, check=check)
                if(plexhelper.verifyemail(str(email.content))):
                    return str(email.content)
                else:
                    email = None
                    message = "The email you provided is invalid, please respond only with the email you used to sign up for Plex."
                    await embederror(after, message)
                    continue
            except asyncio.TimeoutError:
                message = "Timed out. Please contact the server admin directly."
                await embederror(after, message)
                return None
    
    async def getusername(self, after):
        username = None
        await embedinfo(after, f"Welcome to {BRAND_SERVER_NAME}! Please reply with the username you would like to use on Jellyfin.")
        await embedinfo(after, "If you do not respond within 24 hours, the request will be cancelled, and the team will need to add you manually.")
        while (username is None):
            def check(m):
                return m.author == after and not m.guild
            try:
                username = await self.bot.wait_for('message', timeout=86400, check=check)
                if(jelly.verify_username(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, str(username.content))):
                    return str(username.content)
                else:
                    username = None
                    message = "This username is already choosen. Please select another username."
                    await embederror(after, message)
                    continue
            except asyncio.TimeoutError:
                message = "Timed out. Please contact the server admin directly."
                print("Jellyfin user prompt timed out")
                await embederror(after, message)
                return None
            except Exception as e:
                await embederror(after, "Something went wrong. Please try again with another username.")
                print (e)
                username = None

    async def get_emby_username(self, after):
        username = None
        await embedinfo(after, f"Welcome to {BRAND_SERVER_NAME}! Please reply with the username you would like to use on Emby.")
        await embedinfo(after, "If you do not respond within 24 hours, the request will be cancelled, and the team will need to add you manually.")
        while username is None:
            def check(m):
                return m.author == after and not m.guild
            try:
                response = await self.bot.wait_for('message', timeout=86400, check=check)
                candidate = str(response.content).strip()
                if emby.verify_username(EMBY_SERVER_URL, EMBY_API_KEY, candidate):
                    return candidate
                await embederror(after, "This username is already chosen. Please select another username.")
                username = None
            except asyncio.TimeoutError:
                message = "Timed out. Please contact the server admin directly."
                print("Emby user prompt timed out")
                await embederror(after, message)
                return None
            except Exception as e:
                print(e)
                await embederror(after, "Something went wrong. Please try again with another username.")
                username = None


    async def addtoplex(self, email, response):
        if(plexhelper.verifyemail(email)):
            if plexhelper.plexadd(plex,email,Plex_LIBS):
                await embedinfo(response, 'This email address has been added to plex')
                return True
            else:
                await embederror(response, 'There was an error adding this email address. Check logs.')
                return False
        else:
            await embederror(response, 'Invalid email.')
            return False

    async def removefromplex(self, email, response):
        if(plexhelper.verifyemail(email)):
            if plexhelper.plexremove(plex,email):
                await embedinfo(response, 'This email address has been removed from plex.')
                return True
            else:
                await embederror(response, 'There was an error removing this email address. Check logs.')
                return False
        else:
            await embederror(response, 'Invalid email.')
            return False
    
    async def addtojellyfin(self, username, password, response):
        if not jelly.verify_username(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
            await embederror(response, f'An account with username {username} already exists.')
            return False

        if jelly.add_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username, password, jellyfin_libs):
            return True
        else:
            await embederror(response, 'There was an error adding this user to Jellyfin. Check logs for more info.')
            return False

    async def removefromjellyfin(self, username, response):
        if jelly.verify_username(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
            await embederror(response, f'Could not find account with username {username}.')
            return
        
        if jelly.remove_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username):
            await embedinfo(response, f'Successfully removed user {username} from Jellyfin.')
            return True
        else:
            await embederror(response, f'There was an error removing this user from Jellyfin. Check logs for more info.')
            return False

    async def addtoemby(self, username, password, response):
        if not emby.verify_username(EMBY_SERVER_URL, EMBY_API_KEY, username):
            await embederror(response, f'An account with username {username} already exists.')
            return False

        if emby.add_user(EMBY_SERVER_URL, EMBY_API_KEY, username, password, emby_libs):
            return True
        await embederror(response, 'There was an error adding this user to Emby. Check logs for more info.')
        return False

    async def removefromemby(self, username, response):
        if emby.verify_username(EMBY_SERVER_URL, EMBY_API_KEY, username):
            await embederror(response, f'Could not find account with username {username}.')
            return False

        if emby.remove_user(EMBY_SERVER_URL, EMBY_API_KEY, username):
            await embedinfo(response, f'Successfully removed user {username} from Emby.')
            return True
        await embederror(response, f'There was an error removing this user from Emby. Check logs for more info.')
        return False

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if plex_roles is None and jellyfin_roles is None:
            return
        roles_in_guild = after.guild.roles
        role = None

        plex_processed = False
        jellyfin_processed = False
        emby_processed = False

        # Check Plex roles
        if plex_configured and USE_PLEX:
            for role_for_app in plex_roles:
                for role_in_guild in roles_in_guild:
                    if role_in_guild.name == role_for_app:
                        role = role_in_guild

                    # Plex role was added
                    if role is not None and (role in after.roles and role not in before.roles):
                        email = await self.getemail(after)
                        if email is not None:
                            await embedinfo(after, "Got it we will be adding your email to plex shortly!")
                            if plexhelper.plexadd(plex,email,Plex_LIBS):
                                db.save_user_email(str(after.id), email)
                                await self._maybe_set_default_subscription(str(after.id))
                                await asyncio.sleep(5)
                                await embedinfo(after, 'You have Been Added To Plex! Login to plex and accept the invite!')
                            else:
                                await embedinfo(after, 'There was an error adding this email address. Message Server Admin.')
                        plex_processed = True
                        break

                    # Plex role was removed
                    elif role is not None and (role not in after.roles and role in before.roles):
                        try:
                            user_id = after.id
                            email = db.get_useremail(user_id)
                            plexhelper.plexremove(plex,email)
                            deleted = db.remove_email(user_id)
                            if deleted:
                                print("Removed Plex email {} from db".format(after.name))
                                #await secure.send(plexname + ' ' + after.mention + ' was removed from plex')
                            else:
                                print("Cannot remove Plex from this user.")
                            await embedinfo(after, "You have been removed from Plex")
                        except Exception as e:
                            print(e)
                            print("{} Cannot remove this user from plex.".format(email))
                        plex_processed = True
                        break
                if plex_processed:
                    break

        role = None
        # Check Jellyfin roles
        if jellyfin_configured and USE_JELLYFIN:
            for role_for_app in jellyfin_roles:
                for role_in_guild in roles_in_guild:
                    if role_in_guild.name == role_for_app:
                        role = role_in_guild

                    # Jellyfin role was added
                    if role is not None and (role in after.roles and role not in before.roles):
                        print("Jellyfin role added")
                        username = await self.getusername(after)
                        print("Username retrieved from user")
                        if username is not None:
                            await embedinfo(after, "Got it we will be creating your Jellyfin account shortly!")
                            password = jelly.generate_password(16)
                            if jelly.add_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username, password, jellyfin_libs):
                                db.save_user_jellyfin(str(after.id), username)
                                await self._maybe_set_default_subscription(str(after.id))
                                await asyncio.sleep(5)
                                await embedcustom(after, "You have been added to Jellyfin!", {'Username': username, 'Password': f"||{password}||"})
                                await embedinfo(after, f"Go to {JELLYFIN_EXTERNAL_URL} to log in!")
                            else:
                                await embedinfo(after, 'There was an error adding this user to Jellyfin. Message Server Admin.')
                        jellyfin_processed = True
                        break

                    # Jellyfin role was removed
                    elif role is not None and (role not in after.roles and role in before.roles):
                        print("Jellyfin role removed")
                        try:
                            user_id = after.id
                            username = db.get_jellyfin_username(user_id)
                            jelly.remove_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, username)
                            deleted = db.remove_jellyfin(user_id)
                            if deleted:
                                print("Removed Jellyfin from {}".format(after.name))
                                #await secure.send(plexname + ' ' + after.mention + ' was removed from plex')
                            else:
                                print("Cannot remove Jellyfin from this user")
                            await embedinfo(after, "You have been removed from Jellyfin")
                        except Exception as e:
                            print(e)
                            print("{} Cannot remove this user from Jellyfin.".format(username))
                        jellyfin_processed = True
                        break
                if jellyfin_processed:
                    break

        role = None
        # Check Emby roles
        if emby_configured and USE_EMBY:
            for role_for_app in emby_roles:
                for role_in_guild in roles_in_guild:
                    if role_in_guild.name == role_for_app:
                        role = role_in_guild

                    # Emby role was added
                    if role is not None and (role in after.roles and role not in before.roles):
                        print("Emby role added")
                        username = await self.get_emby_username(after)
                        if username is not None:
                            await embedinfo(after, "Got it we will be creating your Emby account shortly!")
                            password = emby.generate_password(16)
                            if emby.add_user(EMBY_SERVER_URL, EMBY_API_KEY, username, password, emby_libs):
                                db.save_user_emby(str(after.id), username)
                                await self._maybe_set_default_subscription(str(after.id))
                                await asyncio.sleep(5)
                                await embedcustom(after, "You have been added to Emby!", {'Username': username, 'Password': f"||{password}||"})
                                if EMBY_EXTERNAL_URL:
                                    await embedinfo(after, f"Go to {EMBY_EXTERNAL_URL} to log in!")
                            else:
                                await embedinfo(after, 'There was an error adding this user to Emby. Message Server Admin.')
                        emby_processed = True
                        break

                    # Emby role was removed
                    elif role is not None and (role not in after.roles and role in before.roles):
                        print("Emby role removed")
                        try:
                            user_id = after.id
                            username = db.get_emby_username(user_id)
                            if username in ("No users found", "error in fetching from db") or not username:
                                print(f"No Emby username stored for {after.name}")
                            else:
                                emby.remove_user(EMBY_SERVER_URL, EMBY_API_KEY, username)
                                deleted = db.remove_emby(user_id)
                                if deleted:
                                    print(f"Removed Emby from {after.name}")
                                else:
                                    print("Cannot remove Emby from this user")
                            await embedinfo(after, "You have been removed from Emby")
                        except Exception as e:
                            print(e)
                            print(f"{username} Cannot remove this user from Emby.")
                        emby_processed = True
                        break
                if emby_processed:
                    break

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if USE_PLEX and plex_configured:
            email = db.get_useremail(member.id)
            plexhelper.plexremove(plex,email)
        
        if USE_JELLYFIN and jellyfin_configured:
            jellyfin_username = db.get_jellyfin_username(member.id)
            jelly.remove_user(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY, jellyfin_username)

        if USE_EMBY and emby_configured:
            emby_username = db.get_emby_username(member.id)
            if emby_username not in ("No users found", "error in fetching from db") and emby_username:
                emby.remove_user(EMBY_SERVER_URL, EMBY_API_KEY, emby_username)
                db.remove_emby(member.id)
            
        deleted = db.delete_user(member.id)
        if deleted:
            print(f"Removed {member.name} from db because user left discord server.")

    @app_commands.checks.has_permissions(administrator=True)
    @plex_commands.command(name="invite", description="Invite a user to Plex")
    async def plexinvite(self, interaction: discord.Interaction, email: str):
        await self.addtoplex(email, interaction.response)
    
    @app_commands.checks.has_permissions(administrator=True)
    @plex_commands.command(name="remove", description="Remove a user from Plex")
    async def plexremove(self, interaction: discord.Interaction, email: str):
        await self.removefromplex(email, interaction.response)
    
    @app_commands.checks.has_permissions(administrator=True)
    @jellyfin_commands.command(name="invite", description="Invite a user to Jellyfin")
    async def jellyfininvite(self, interaction: discord.Interaction, username: str):
        password = jelly.generate_password(16)
        if await self.addtojellyfin(username, password, interaction.response):
            await embedcustom(interaction.response, "Jellyfin user created!", {'Username': username, 'Password': f"||{password}||"})

    @app_commands.checks.has_permissions(administrator=True)
    @jellyfin_commands.command(name="remove", description="Remove a user from Jellyfin")
    async def jellyfinremove(self, interaction: discord.Interaction, username: str):
        await self.removefromjellyfin(username, interaction.response)

    @app_commands.checks.has_permissions(administrator=True)
    @emby_commands.command(name="invite", description="Invite a user to Emby")
    async def embyinvite(self, interaction: discord.Interaction, username: str):
        password = emby.generate_password(16)
        if await self.addtoemby(username, password, interaction.response):
            fields = {'Username': username, 'Password': f"||{password}||"}
            if EMBY_EXTERNAL_URL:
                fields['Login URL'] = EMBY_EXTERNAL_URL
            await embedcustom(interaction.response, "Emby user created!", fields)

    @app_commands.checks.has_permissions(administrator=True)
    @emby_commands.command(name="remove", description="Remove a user from Emby")
    async def embyremove(self, interaction: discord.Interaction, username: str):
        await self.removefromemby(username, interaction.response)
    
    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="dbadd", description="Add a user to the Quantum Invites database")
    async def dbadd(self, interaction: discord.Interaction, member: discord.Member, email: str = "", jellyfin_username: str = "", emby_username: str = ""):
        email = email.strip()
        jellyfin_username = jellyfin_username.strip()
        emby_username = emby_username.strip()
        
        # Check email if provided
        if email and not plexhelper.verifyemail(email):
            await embederror(interaction.response, "Invalid email.")
            return

        try:
            db.save_user_all(str(member.id), email=email or None, jellyfin_username=jellyfin_username or None, emby_username=emby_username or None)
            await embedinfo(interaction.response,'User was added to the database.')
        except Exception as e:
            await embedinfo(interaction.response, f'There was an error adding this user to database. Check {BRAND_BOT_NAME} logs for more info')
            print(e)

    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="dbls", description="View Quantum Invites database")
    async def dbls(self, interaction: discord.Interaction):

        embed = discord.Embed(title=f'{BRAND_BOT_NAME} Database.')
        all = db.read_all()
        table = texttable.Texttable()
        table.set_cols_dtype(["t", "t", "t", "t", "t", "t"])
        table.set_cols_align(["c", "c", "c", "c", "c", "c"])
        header = ("#", "Name", "Email", "Jellyfin", "Emby", "Expires")
        table.add_row(header)
        for index, peoples in enumerate(all):
            index = index + 1
            id = int(peoples[1])
            dbuser = self.bot.get_user(id)
            dbemail = peoples[2] if peoples[2] else "No Plex"
            dbjellyfin = peoples[3] if peoples[3] else "No Jellyfin"
            dbemby = peoples[4] if len(peoples) > 4 and peoples[4] else "No Emby"
            raw_expiry = peoples[5] if len(peoples) > 5 and peoples[5] else None
            expiry_display = "No expiry"
            if raw_expiry:
                parsed = self._parse_datetime(raw_expiry)
                expiry_display = parsed.strftime('%Y-%m-%d') if parsed else raw_expiry
            try:
                username = dbuser.name
            except:
                username = "User Not Found."
            embed.add_field(
                name=f"**{index}. {username}**",
                value=f"{dbemail}\n{dbjellyfin}\n{dbemby}\nExpiry: {expiry_display}\n",
                inline=False
            )
            table.add_row((index, username, dbemail, dbjellyfin, dbemby, expiry_display))
        
        total = str(len(all))
        if(len(all)>25):
            f = open("db.txt", "w")
            f.write(table.draw())
            f.close()
            await interaction.response.send_message("Database too large! Total: {total}".format(total = total),file=discord.File('db.txt'), ephemeral=True)
        else:
            await interaction.response.send_message(embed = embed, ephemeral=True)
        
            
    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="dbrm", description="Remove user from Quantum Invites database")
    async def dbrm(self, interaction: discord.Interaction, position: int):
        embed = discord.Embed(title=f'{BRAND_BOT_NAME} Database.')
        all = db.read_all()
        for index, peoples in enumerate(all):
            index = index + 1
            id = int(peoples[1])
            dbuser = self.bot.get_user(id)
            dbemail = peoples[2] if peoples[2] else "No Plex"
            dbjellyfin = peoples[3] if peoples[3] else "No Jellyfin"
            dbemby = peoples[4] if len(peoples) > 4 and peoples[4] else "No Emby"
            raw_expiry = peoples[5] if len(peoples) > 5 and peoples[5] else None
            expiry_display = "No expiry"
            if raw_expiry:
                parsed = self._parse_datetime(raw_expiry)
                expiry_display = parsed.strftime('%Y-%m-%d') if parsed else raw_expiry
            try:
                username = dbuser.name
            except:
                username = "User Not Found."
            embed.add_field(
                name=f"**{index}. {username}**",
                value=f"{dbemail}\n{dbjellyfin}\n{dbemby}\nExpiry: {expiry_display}\n",
                inline=False
            )

        try:
            position = int(position) - 1
            id = all[position][1]
            discord_user = await self.bot.fetch_user(id)
            username = discord_user.name
            deleted = db.delete_user(id)
            if deleted:
                print("Removed {} from db".format(username))
                await embedinfo(interaction.response,"Removed {} from db".format(username))
            else:
                await embederror(interaction.response,"Cannot remove this user from db.")
        except Exception as e:
            print(e)

    @quantum_commands.command(name="ping", description="Check if Quantum Invites is responding")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000, 2)
        await embedinfo(
            interaction.response,
            f"{BRAND_BOT_NAME} is online! Latency: {latency_ms} ms",
            ephemeral=True
        )

    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="setexpiry", description="Set subscription expiry for a member")
    async def setexpiry(self, interaction: discord.Interaction, member: discord.Member, days: app_commands.Range[int, 1, 3650] = None, expires_on: str = None):
        await interaction.response.defer(ephemeral=True)
        if days is None and not expires_on:
            days = SUBSCRIPTION_DEFAULT_DAYS if SUBSCRIPTION_DEFAULT_DAYS > 0 else 30

        if expires_on:
            try:
                target_date = datetime.strptime(expires_on, "%Y-%m-%d")
                expires_at = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
            except ValueError:
                await self._send_embed(interaction.followup, "Invalid date", "Use YYYY-MM-DD for the expires_on value.", color=discord.Color.red(), ephemeral=True)
                return
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(days=days)

        db.set_subscription(str(member.id), self._format_datetime(expires_at))
        summary = f"{member.mention} now expires on **{expires_at.strftime('%Y-%m-%d')}**."
        await self._send_embed(interaction.followup, "Subscription updated", summary, color=discord.Color.green(), ephemeral=True)
        await self._send_embed(
            member,
            f"{BRAND_SERVER_NAME} subscription updated",
            f"Your access has been extended through **{expires_at.strftime('%Y-%m-%d')}**. Thank you for supporting {BRAND_SERVER_NAME}!",
            color=discord.Color.green()
        )
        await self._notify_management(
            f"Subscription set for {member.display_name}",
            f"{member.mention} expires on {expires_at.strftime('%Y-%m-%d')}."
        )

    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="extendexpiry", description="Extend an existing subscription by N days")
    async def extendexpiry(self, interaction: discord.Interaction, member: discord.Member, days: app_commands.Range[int, 1, 3650]):
        await interaction.response.defer(ephemeral=True)
        info = db.get_subscription(str(member.id))
        current_expiry = self._parse_datetime(info["expires_at"]) if info and info.get("expires_at") else datetime.now(timezone.utc)
        new_expiry = current_expiry + timedelta(days=days)
        db.set_subscription(str(member.id), self._format_datetime(new_expiry))
        await self._send_embed(
            interaction.followup,
            "Subscription extended",
            f"{member.mention} extended by **{days}** day(s). New expiry: **{new_expiry.strftime('%Y-%m-%d')}**.",
            color=discord.Color.green(),
            ephemeral=True
        )
        await self._send_embed(
            member,
            f"{BRAND_SERVER_NAME} subscription extended",
            f"Your subscription is now valid through **{new_expiry.strftime('%Y-%m-%d')}**.",
            color=discord.Color.green()
        )
        await self._notify_management(
            f"Subscription extended for {member.display_name}",
            f"{member.mention}'s subscription extended by {days} day(s) to {new_expiry.strftime('%Y-%m-%d')}."
        )

    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="clearexpiry", description="Clear a member's subscription expiry")
    async def clearexpiry(self, interaction: discord.Interaction, member: discord.Member):
        info = db.get_subscription(str(member.id))
        if not info or not info.get("expires_at"):
            await embedinfo(interaction.response, f"{member.mention} does not have an active expiry recorded.", ephemeral=True)
            return
        db.clear_subscription(str(member.id))
        await embedinfo(interaction.response, f"Cleared subscription expiry for {member.mention}.", ephemeral=True)
        await self._send_embed(
            member,
            f"{BRAND_SERVER_NAME} subscription cleared",
            "Your subscription expiry record has been cleared. Contact the team if this was unexpected.",
            color=discord.Color.orange()
        )

    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="expiryinfo", description="Show subscription status for a member")
    async def expiryinfo(self, interaction: discord.Interaction, member: discord.Member):
        info = db.get_subscription(str(member.id))
        if not info or not info.get("expires_at"):
            await embedinfo(interaction.response, f"{member.mention} does not have an expiry set.", ephemeral=True)
            return
        expires_at = self._parse_datetime(info.get("expires_at"))
        if not expires_at:
            await embedinfo(interaction.response, f"{member.mention} has an expiry record but it could not be parsed.", ephemeral=True)
            return
        now = datetime.now(timezone.utc)
        delta = expires_at - now
        status = "active" if delta.total_seconds() >= 0 else "expired"
        days = int(abs(delta.total_seconds()) // 86400)
        message = f"Expires on **{expires_at.strftime('%Y-%m-%d')}** ({status}, {days} day(s) {'left' if status == 'active' else 'ago'})."
        await embedinfo(interaction.response, f"{member.mention}: {message}", ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @quantum_commands.command(name="listexpiring", description="List subscriptions expiring soon")
    async def listexpiring(self, interaction: discord.Interaction, within_days: app_commands.Range[int, 1, 90] = 14):
        await interaction.response.defer(ephemeral=True)
        now = datetime.now(timezone.utc)
        rows = []
        for record in db.list_subscriptions():
            user_key = record.get("discord_username")
            expires_at = self._parse_datetime(record.get("expires_at"))
            if not user_key or not expires_at:
                continue
            delta_days = (expires_at - now).days
            if delta_days < 0 or delta_days > within_days:
                continue
            rows.append((user_key, expires_at, delta_days))
        if not rows:
            await embedinfo(interaction.followup, f"No subscriptions expiring within {within_days} day(s).", ephemeral=True)
            return
        rows.sort(key=lambda row: row[1])
        description = "\n".join(
            f"<@{user_id}> - {expires.strftime('%Y-%m-%d')} ({days} day(s) left)"
            for user_id, expires, days in rows
        )
        await self._send_embed(
            interaction.followup,
            f"Expiring in next {within_days} day(s)",
            description,
            color=discord.Color.gold(),
            ephemeral=True
        )

async def setup(bot):
    cog = app(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.remove_command("quantum")
    except Exception:
        pass
    bot.tree.add_command(cog.quantum_commands)
