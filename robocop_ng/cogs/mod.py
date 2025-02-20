import discord
from discord.ext import commands
from discord.ext.commands import Cog
import config
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.userlogs import userlog
from helpers.restrictions import add_restriction, remove_restriction
import io


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_if_target_is_staff(self, target):
        return any(r.id in config.staff_role_ids for r in target.roles)

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def setguildicon(self, ctx, url):
        """Changes guild icon, bot manager only."""
        img_bytes = await self.bot.aiogetbytes(url)
        await ctx.guild.edit(icon=img_bytes, reason=str(ctx.author))
        await ctx.send(f"Done!")

        log_channel = self.bot.get_channel(config.modlog_channel)
        log_msg = (
            f"✏️ **Guild Icon Update**: {ctx.author} changed the guild icon."
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        img_filename = url.split("/")[-1].split("#")[0]  # hacky
        img_file = discord.File(io.BytesIO(img_bytes), filename=img_filename)
        await log_channel.send(log_msg, file=img_file)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def mute(self, ctx, target: discord.Member, *, reason: str = ""):
        """Mutes a user, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I can't mute this user as they're a member of staff."
            )

        userlog(target.id, ctx.author, reason, "mutes", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were muted!"
        if reason:
            dm_message += f' The given reason is: "{reason}".'

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            pass

        mute_role = ctx.guild.get_role(config.mute_role)

        await target.add_roles(mute_role, reason=str(ctx.author))

        chan_message = (
            f"🔇 **Muted**: {str(ctx.author)} muted "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future, "
                "it is recommended to use `.mute <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{target.mention} can no longer speak.")
        add_restriction(target.id, config.mute_role)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unmute(self, ctx, target: discord.Member):
        """Unmutes a user, staff only."""
        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        mute_role = ctx.guild.get_role(config.mute_role)
        await target.remove_roles(mute_role, reason=str(ctx.author))

        chan_message = (
            f"🔈 **Unmuted**: {str(ctx.author)} unmuted "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{target.mention} can now speak again.")
        remove_restriction(target.id, config.mute_role)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def kick(self, ctx, target: discord.Member, *, reason: str = ""):
        """Kicks a user, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I can't kick this user as they're a member of staff."
            )

        userlog(target.id, ctx.author, reason, "kicks", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were kicked from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += (
            "\n\nYou are able to rejoin the server,"
            " but please be sure to behave when participating again."
        )

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.kick(reason=f"{ctx.author}, reason: {reason}")
        chan_message = (
            f"👢 **Kick**: {str(ctx.author)} kicked "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.kick <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"👢 {safe_name}, 👍.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx, target: discord.Member, *, reason: str = ""):
        """Bans a user, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            if target.id == 181627658520625152:
                return await ctx.send(
                    "https://cdn.discordapp.com/attachments/286612533757083648/403080855402315796/rehedge.PNG"
                )
            return await ctx.send("hedgeberg#7337 is now b&. 👍")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        userlog(target.id, ctx.author, reason, "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were banned from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += "\n\nThis ban does not expire."

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents ban issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.ban(
            reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Ban**: {str(ctx.author)} banned "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.ban <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{safe_name} is now b&. 👍")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    async def bandel(
        self, ctx, day_count: int, target: discord.Member, *, reason: str = ""
    ):
        """Bans a user for a given number of days, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            if target.id == 181627658520625152:
                return await ctx.send(
                    "https://cdn.discordapp.com/attachments/286612533757083648/403080855402315796/rehedge.PNG"
                )
            return await ctx.send("hedgeberg#7337 is now b&. 👍")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        if day_count < 0 or day_count > 7:
            return await ctx.send(
                "Message delete day count needs to be between 0 and 7 days."
            )

        userlog(target.id, ctx.author, reason, "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were banned from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += "\n\nThis ban does not expire."

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents ban issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.ban(
            reason=f"{ctx.author}, days of message deletions: {day_count}, reason: {reason}",
            delete_message_days=day_count,
        )
        chan_message = (
            f"⛔ **Ban**: {str(ctx.author)} banned with {day_count} of messages deleted "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.bandel <daycount> <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(
            f"{safe_name} is now b&, with {day_count} days of messages deleted. 👍"
        )

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["softban"])
    async def hackban(self, ctx, target: int, *, reason: str = ""):
        """Bans a user with their ID, doesn't message them, staff only."""
        target_user = await self.bot.fetch_user(target)
        target_member = ctx.guild.get_member(target)
        # Hedge-proofing the code
        if target == ctx.author.id:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif target_member and self.check_if_target_is_staff(target_member):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        userlog(target, ctx.author, reason, "bans", target_user.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.ban(
            target_user, reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Hackban**: {str(ctx.author)} banned "
            f"{target_user.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.hackban <user> [reason]`."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{safe_name} is now b&. 👍")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def massban(self, ctx, *, targets: str):
        """Bans users with their IDs, doesn't message them, staff only."""
        targets_int = [int(target) for target in targets.strip().split(" ")]
        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.guild.get_member(target)
            # Hedge-proofing the code
            if target == ctx.author.id:
                await ctx.send(f"(re: {target}) You can't do mod actions on yourself.")
                continue
            elif target == self.bot.user:
                await ctx.send(
                    f"(re: {target}) I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
                )
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(
                    f"(re: {target}) I can't ban this user as they're a member of staff."
                )
                continue

            userlog(target, ctx.author, f"massban", "bans", target_user.name)

            safe_name = await commands.clean_content(escape_markdown=True).convert(
                ctx, str(target)
            )

            await ctx.guild.ban(
                target_user,
                reason=f"{ctx.author}, reason: massban",
                delete_message_days=0,
            )
            chan_message = (
                f"⛔ **Massban**: {str(ctx.author)} banned "
                f"{target_user.mention} | {safe_name}\n"
                f"🏷 __User ID__: {target}\n"
                "Please add an explanation below."
            )

            chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

            log_channel = self.bot.get_channel(config.modlog_channel)
            await log_channel.send(chan_message)
        await ctx.send(f"All {len(targets_int)} users are now b&. 👍")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def unban(self, ctx, target: int, *, reason: str = ""):
        """Unbans a user with their ID, doesn't message them, staff only."""
        target_user = await self.bot.fetch_user(target)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.unban(target_user, reason=f"{ctx.author}, reason: {reason}")
        chan_message = (
            f"⚠️ **Unban**: {str(ctx.author)} unbanned "
            f"{target_user.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use "
                "`.unban <user id> [reason]`."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)
        await ctx.send(f"{safe_name} is now unb&.")

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def silentban(self, ctx, target: discord.Member, *, reason: str = ""):
        """Bans a user, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I can't ban this user as they're a member of staff.")

        userlog(target.id, ctx.author, reason, "bans", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await target.ban(
            reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Silent ban**: {str(ctx.author)} banned "
            f"{target.mention} | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.ban <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_message += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        log_channel = self.bot.get_channel(config.modlog_channel)
        await log_channel.send(chan_message)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def approve(self, ctx, target: discord.Member, role: str = "community"):
        """Add a role to a user (default: community), staff only."""
        if role not in config.named_roles:
            return await ctx.send(
                "No such role! Available roles: " + ",".join(config.named_roles)
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        target_role = ctx.guild.get_role(config.named_roles[role])

        if target_role in target.roles:
            return await ctx.send("Target already has this role.")

        await target.add_roles(target_role, reason=str(ctx.author))

        await ctx.send(f"Approved {target.mention} to `{role}` role.")

        await log_channel.send(
            f"✅ Approved: {str(ctx.author)} added"
            f" {role} to {target.mention}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["unapprove"])
    async def revoke(self, ctx, target: discord.Member, role: str = "community"):
        """Remove a role from a user (default: community), staff only."""
        if role not in config.named_roles:
            return await ctx.send(
                "No such role! Available roles: " + ",".join(config.named_roles)
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        target_role = ctx.guild.get_role(config.named_roles[role])

        if target_role not in target.roles:
            return await ctx.send("Target doesn't have this role.")

        await target.remove_roles(target_role, reason=str(ctx.author))

        await ctx.send(f"Un-approved {target.mention} from `{role}` role.")

        await log_channel.send(
            f"❌ Un-approved: {str(ctx.author)} removed"
            f" {role} from {target.mention}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.command(aliases=["giverole"])
    async def addrole(self, ctx, member: discord.Member, role: discord.Role):
      """Adds a role to a member. Staff only."""

      author_top_role = ctx.author.roles.reverse()[0]
      target_top_role = member.roles.reverse()[0]

      if author_top_role.position < target_top_role.position or author_top_role.position < role.position:
        return await ctx.send("This action can't be done because of role hierarchy.")

      await member.add_roles(role)
      await ctx.send(f"Role {role.name} is added to {member.mention}.")
      
      log_channel = self.bot.get_channel(config.modlog_channel)
      await log_channel.send(
        f"✅️ Role '{role.name}' have been added to {member},"
        f"by {ctx.message.author}."
      )
      
    @commands.guild_only()  
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.command(aliases=["takerole"])
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
      """Removes a role from a member. Staff only."""

      author_top_role = ctx.author.roles.reverse()[0]
      target_top_role = member.roles.reverse()[0]

      if author_top_role.position < target_top_role.position or author_top_role.position < role.position:
        return await ctx.send("This action can't be done because of role hierarchy.")
        
      await member.remove_roles(role)
      await ctx.send(f"Role {role.name} is removed from {member.mention}.")
      
      log_channel = self.bot.get_channel(config.modlog_channel)
      await log_channel.send(
        f"❌️ Role '{role.name}' have been removed from {member},"
        f"by {ctx.message.author}."
      )

    @commands.guild_only() 
    @commands.check(check_if_staff)
    @commands.command(aliases=["clear"])
    async def purge(self, ctx, limit: int, channel: discord.TextChannel = None):
        """Clears a given number of messages, staff only."""
        log_channel = self.bot.get_channel(config.modlog_channel)
        if not channel:
            channel = ctx.channel
        await channel.purge(limit=limit)
        msg = (
            f"🗑 **Purged**: {str(ctx.author)} purged {limit} "
            f"messages in {channel.mention}."
        )
        await log_channel.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def warn(self, ctx, target: discord.Member, *, reason: str = ""):
        """Warns a user, staff only."""
        # Hedge-proofing the code
        if target == ctx.author:
            return await ctx.send("You can't do mod actions on yourself.")
        elif target == self.bot.user:
            return await ctx.send(
                f"I'm sorry {ctx.author.mention}, I'm afraid I can't do that."
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send(
                "I can't warn this user as they're a member of staff."
            )

        log_channel = self.bot.get_channel(config.modlog_channel)
        warn_count = userlog(target.id, ctx.author, reason, "warns", target.name)

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        chan_msg = (
            f"⚠️ **Warned**: {str(ctx.author)} warned "
            f"{target.mention} (warn #{warn_count}) "
            f"| {safe_name}\n"
        )

        msg = f"You were warned on {ctx.guild.name}."
        if reason:
            msg += " The given reason is: " + reason
        msg += (
            f"\n\nPlease read the rules in {config.rules_url}. "
            f"This is warn #{warn_count}."
        )
        if warn_count == 2:
            msg += " __The next warn will automatically kick.__"
        if warn_count == 3:
            msg += (
                "\n\nYou were kicked because of this warning. "
                "This is your final warning. "
                "You can join again, but "
                "**one more warn will result in a ban**."
            )
            chan_msg += "**This resulted in an auto-kick.**\n"
        if warn_count == 4:
            msg += "\n\nYou were automatically banned due to four warnings."
            chan_msg += "**This resulted in an auto-ban.**\n"
        try:
            await target.send(msg)
        except discord.errors.Forbidden:
            # Prevents log issues in cases where user blocked bot
            # or has DMs disabled
            pass
        if warn_count == 3:
            await target.kick()
        if warn_count >= 4:  # just in case
            await target.ban(reason="exceeded warn limit", delete_message_days=0)
        await ctx.send(
            f"{target.mention} warned. " f"User has {warn_count} warning(s)."
        )

        if reason:
            chan_msg += f'✏️ __Reason__: "{reason}"'
        else:
            chan_msg += (
                "Please add an explanation below. In the future"
                ", it is recommended to use `.warn <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        chan_msg += f"\n🔗 __Jump__: <{ctx.message.jump_url}>"

        await log_channel.send(chan_msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setnick", "nick"])
    async def nickname(self, ctx, target: discord.Member, *, nick: str = ""):
        """Sets a user's nickname, staff only.

        Just send .nickname <user> to wipe the nickname."""

        try:
            if nick:
                await target.edit(nick=nick, reason=str(ctx.author))
            else:
                await target.edit(nick=None, reason=str(ctx.author))

            await ctx.send("Successfully set nickname.")
        except discord.errors.Forbidden:
            await ctx.send(
                "I don't have the permission to set that user's nickname.\n"
                "User's top role may be above mine, or I may lack Manage Nicknames permission."
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["echo"])
    async def say(self, ctx, *, the_text: str):
        """Repeats a given text, staff only."""
        await ctx.send(the_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def speak(self, ctx, channel: discord.TextChannel, *, the_text: str):
        """Repeats a given text in a given channel, staff only."""
        await channel.send(the_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setplaying", "setgame"])
    async def playing(self, ctx, *, game: str = ""):
        """Sets the bot's currently played game name, staff only.

        Just send .playing to wipe the playing state."""
        if game:
            await self.bot.change_presence(activity=discord.Game(name=game))
        else:
            await self.bot.change_presence(activity=None)

        await ctx.send("Successfully set game.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setbotnick", "botnick", "robotnick"])
    async def botnickname(self, ctx, *, nick: str = ""):
        """Sets the bot's nickname, staff only.

        Just send .botnickname to wipe the nickname."""

        if nick:
            await ctx.guild.me.edit(nick=nick, reason=str(ctx.author))
        else:
            await ctx.guild.me.edit(nick=None, reason=str(ctx.author))

        await ctx.send("Successfully set bot nickname.")


def setup(bot):
    bot.add_cog(Mod(bot))
