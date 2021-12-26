from discord import Option

from views.buttons import PaginatorView

import discord
import json


class ConfigCog(discord.Cog, name='Configuration'):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.utils = self.bot.get_cog('Utilities')

    config = discord.SlashCommandGroup('config', 'Configuration commands')

    @config.command(name='help', description='View all configuration commands.')
    async def _help(self, ctx: discord.ApplicationContext) -> None:
        cmd_embeds = [await self.utils.cmd_help_embed(ctx, _) for _ in self.config.subcommands]

        paginator = PaginatorView(cmd_embeds, ctx, timeout=180)
        await ctx.respond(embed=cmd_embeds[paginator.embed_num], view=paginator, ephemeral=True)

    @config.command(name='setchannel', description='Set a channel for *OS releases to be announced in.') #TODO: Implement setting announcement channels on a per-role basis
    async def set_channel(self, ctx: discord.ApplicationContext, channel: Option(discord.TextChannel, 'Channel to send *OS releases in')):
        async with self.bot.db.execute('SELECT data FROM roles WHERE guild = ?', (ctx.guild.id,)) as cursor:
            roles = json.loads((await cursor.fetchone())[0])

        for os in roles.keys():
            roles[os].update({'channel': channel.id})

        await self.bot.db.execute('UPDATE roles SET data = ? WHERE guild = ?', (json.dumps(roles), ctx.guild.id))
        await self.bot.db.commit()

        embed = discord.Embed(title='Configuration', description=f'Announcements for *OS releases have been set to: {channel.mention}')
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.with_static_format('png').url)

        await ctx.respond(embed=embed, ephemeral=True)
        

def setup(bot):
    bot.add_cog(ConfigCog(bot))
