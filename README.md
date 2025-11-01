[![Discord](https://img.shields.io/discord/997761163020488815?color=7289DA&label=Discord&style=for-the-badge&logo=discord)](https://discord.gg/7hAUKKTyTd)
[![DockerHub](https://img.shields.io/badge/Docker-Hub-%23099cec?style=for-the-badge&logo=docker)](https://hub.docker.com/r/yoruio/membarr)
![Docker Pulls](https://img.shields.io/docker/pulls/yoruio/membarr?color=099cec&style=for-the-badge)
[![docker-sync](https://github.com/Yoruio/Membarr/actions/workflows/docker-sync.yml/badge.svg)](https://github.com/Yoruio/Membarr/actions/workflows/docker-sync.yml)

Quantum Invites 
=================

Quantum Invites is a polished fork of Invitarr that invites Discord users to Plex, Emby, and Jellyfin for the Quantum Streams community. You can automate adds/removals by role, manage timed subscriptions with reminders, or add users manually.  

### Features

- Invite users to Plex, Emby, and Jellyfin directly from Discord
- Fully automated onboarding/offboarding driven by Quantum Streams roles
- Timed subscriptions with configurable reminders, grace periods, and automatic revocation
- Renewal reminders via Discord DMs with optional SMTP email delivery
- In-discord database and subscription management slash commands for admins
- Optional alert channel/owner pings so you never miss a renewal window

Commands: 

```
/plex invite <email>
This command is used to add an email to plex
/plex remove <email>
This command is used to remove an email from plex
/jellyfin invite <jellyfin username>
This command is used to add a user to Jellyfin.
/jellyfin remove <jellyfin username>
This command is used to remove a user from Jellyfin.
/emby invite <emby username>
This command is used to add a user to Emby.
/emby remove <emby username>
This command is used to remove a user from Emby.
/quantum dbls
This command lists the Quantum Invites database with service status and expiry dates
/quantum dbadd <@user> <optional: plex email> <optional: jellyfin username> <optional: emby username>
This command is used to add existing plex emails, jellyfin users, emby users and discord id to the DB.
/quantum dbrm <position>
This command is used to remove a record from the Db. Use /quantum dbls to determine record position. ex: /quantum dbrm 1
/quantum ping
Quick health check that confirms the bot is online and reports latency.
/quantum setexpiry <@user> <optional: days> <optional: expires_on>
Set or replace a member's subscription expiry (defaults to configured length if days is omitted).
/quantum extendexpiry <@user> <days>
Extend an existing subscription by the specified number of days.
/quantum clearexpiry <@user>
Clear a member's subscription expiry record.
/quantum expiryinfo <@user>
View the stored expiry date and status for a member.
/quantum listexpiring <optional: within_days>
List members whose subscriptions expire within the given window (default 14 days).
/subscriptionsettings show
Display current subscription defaults, reminders, grace period, and alert destination.
/subscriptionsettings setdefault <days>
Update the default subscription length applied when users are auto-onboarded.
/subscriptionsettings setreminders <comma separated days>
Update reminder offsets (e.g. `7,3,1` sends notices 7, 3, and 1 day before expiry).
/subscriptionsettings setgrace <days>
Update the number of grace days after expiry before access is revoked.
/subscriptionsettings setemailserver <host> <port> <from email> <use_tls>
Configure the SMTP server used for subscription reminder mail.
/subscriptionsettings setemailcredentials <optional: username> <optional: password>
Set SMTP authentication (leave blank to clear).
/subscriptionsettings setemailenabled <true|false>
Toggle SMTP reminder emails on or off (DMs stay enabled either way).
/subscriptionsettings setalertchannel <#channel>
Send subscription alerts to a specific channel instead of the configured owner DM.
/subscriptionsettings clearalertchannel
Stop sending subscription alerts to a channel and fall back to owner DMs.
```
# Creating Discord Bot
1. Create the discord server that your users will get member roles or use an existing discord that you can assign roles from
2. Log into https://discord.com/developers/applications and click 'New Application'
3. (Optional) Add a short description and an icon for the bot. Save changes.
4. Go to 'Bot' section in the side menu
5. Uncheck 'Public Bot' under Authorization Flow
6. Check all 3 boxes under Privileged Gateway Intents: Presence Intent, Server Members Intent, Message Content Intent. Save changes.
7. Copy the token under the username or reset it to copy. This is the token used in the docker image.
8. Go to 'OAuth2' section in the side menu, then 'URL Generator'
9. Under Scopes, check 'bot' and applications.commands
10. Copy the 'Generated URL' and paste into your browser and add it to your discord server from Step 1.
11. The bot will come online after the docker container is running with the correct Bot Token


# Unraid Installation
> For Manual an Docker setup, see below

1. Ensure you have the Community Applications plugin installed.
2. Inside the Community Applications app store, search for Quantum Invites (formerly Membarr).
3. Click the Install Button.
4. Add discord bot token.
5. Click apply
6. Finish setting up using [Setup Commands](#after-bot-has-started)

# Manual Setup (For Docker, see below)

**1. Enter discord bot token in bot.env**

**2. Install requirements**

```
pip3 install -r requirements.txt 
```
**3. Start the bot**
```
python3 Run.py
```

# Docker Setup & Start
To run Quantum Invites in Docker, run the following command, replacing [path to config] with the absolute path to your bot config folder:
```
docker run -d --restart unless-stopped --name membarr -v /[path to config]:/app/app/config -e "token=YOUR_DISCORD_TOKEN_HERE" yoruio/membarr:latest
```

# After bot has started 

# Plex Setup Commands: 

```
/plexsettings setup <username> <password> <server name>
This command is used to setup plex login. 
/plexsettings addrole <@role>
These role(s) will be used as the role(s) to automatically invite user to plex
/plexsettings removerole <@role>
This command is used to remove a role that is being used to automatically invite uses to plex
/plexsettings setuplibs <libraries>
This command is used to setup plex libraries. Default is set to all. Libraries is a comma separated list.
/plexsettings enable
This command enables the Plex integration (currently only enables auto-add / auto-remove)
/plexsettings disable
This command disables the Plex integration (currently only disables auto-add / auto-remove)
```

# Jellyfin Setup Commands:
```
/jellyfinsettings setup <server url> <api key> <optional: external server url (default: server url)>
This command is used to setup the Jellyfin server. The external server URL is the URL that is sent to users to log into your Jellyfin server.
/jellyfinsettings addrole <@role>
These role(s) will be used as the role(s) to automatically invite user to Jellyfin
/jellyfinsettings removerole <@role>
This command is used to remove a role that is being used to automatically invite uses to Jellyfin
/jellyfinsettings setuplibs <libraries>
This command is used to setup Jellyfin libraries. Default is set to all. Libraries is a comma separated list.
/jellyfinsettings enable
This command enables the Jellyfin integration (currently only enables auto-add / auto-remove)
/jellyfinsettings disable
This command disables the Jellyfin integration (currently only disables auto-add / auto-remove)
```

# Emby Setup Commands:
```
/embysettings setup <server url> <api key> <optional: external server url (default: server url)>
This command is used to setup the Emby server. The external server URL is the URL that is sent to users to log into your Emby server.
/embysettings addrole <@role>
These role(s) will be used as the role(s) to automatically invite user to Emby
/embysettings removerole <@role>
This command is used to remove a role that is being used to automatically invite users to Emby
/embysettings setuplibs <libraries>
This command is used to setup Emby libraries. Default is set to all. Libraries is a comma separated list.
/embysettings enable
This command enables the Emby integration (currently only enables auto-add / auto-remove)
/embysettings disable
This command disables the Emby integration (currently only disables auto-add / auto-remove)
```

# Subscription Commands

Timed access is now first-class in Quantum Invites. Use the `/quantum` membership commands to set, extend, clear, or inspect individual expiries, and `/subscriptionsettings` to adjust global defaults, reminder cadence, grace period, or alert destination without touching the config file. The bot automatically DMs members, pings your chosen alert channel (or owner), and removes Plex/Emby/Jellyfin access once the grace window closes.

## Email Reminder Setup

1. Run `/subscriptionsettings setemailserver` with your SMTP host, port, sender address, and TLS preference.
2. (Optional) Provide auth details via `/subscriptionsettings setemailcredentials`.
3. Enable mailing with `/subscriptionsettings setemailenabled true`.

Once configured, every reminder/overdue/expiry notice is sent via Discord DM *and* email to the stored Plex address, giving members redundant prompts to renew.

# Migration from Invitarr
Invitarr does not require the applications.commands scope, so you will need to kick and reinvite your Discord bot to your server, making sure to tick both the "bot" and "applications.commands" scopes in the Oauth URL generator.

Quantum Invites uses a slightly different database table than Invitarr. Quantum Invites will automatically update the Invitarr db table to the current Quantum Invites table format, but the new table will no longer be compatible with Invitarr, so backup your app.db before running Quantum Invites!

# Migration to Invitarr
As mentioned in [Migration from Invitarr](#Migration-From-Invitarr), Quantum Invites has a slightly different db table than Invitarr. To switch back to Invitarr, you will have to manually change the table format back. Open app.db in a sqlite cli tool or browser like DB Browser, then remove the "jellyfin_username" and "emby_username" columns, and make the "email" column non-nullable.

# Contributing
We appreciate any and all contributions made to the project, whether that be new features, bugfixes, or even fixed typos! If you would like to contribute to the project, simply fork the development branch, make your changes, and open a pull request. *Pull requests that are not based on the development branch will be rejected.*

# Other stuff
**Enable Intents else bot will not Dm users after they get the role.**
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents
**Discord Bot requires Bot and application.commands permission to fully function.**
