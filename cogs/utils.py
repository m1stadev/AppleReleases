from discord.enums import SlashCommandOptionType

import discord


class UtilsCog(discord.Cog, name='Utilities'):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    READABLE_INPUT_TYPES = {
        SlashCommandOptionType.string: 'string',
        SlashCommandOptionType.channel: 'channel',
        SlashCommandOptionType.user: 'user'
    }

    @property
    def invite(self) -> str:
        """ Returns an invite URL for the bot.

        This is a much better implementation that utilizes
        available tools in the discord library rather than
        being lazy and using a long string. """
        return discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(268463104), scopes=('bot', 'applications.commands'))

    async def cmd_help_embed(self, ctx: discord.ApplicationContext, cmd: discord.SlashCommand):
        embed = {
            'title': f"/{' '.join((cmd.full_parent_name, cmd.name)) or cmd.name} ",
            'description': cmd.description,
            'fields': list(),
            'color': int(discord.Color.blurple()),
            'footer': {
                'text': ctx.author.display_name,
                'icon_url': str(ctx.author.display_avatar.with_static_format('png').url)
            }
        }

        for arg in cmd.options:
            embed['title'] += f'<{arg.name}> ' if arg.required else f'[{arg.name}] '
            embed['fields'].append({
                'name': f'<{arg.name}>' if arg.required else f'[{arg.name}]',
                'value': f"```yaml\nDescription: {arg.description or 'No description'}\nInput Type: {self.READABLE_INPUT_TYPES[arg.input_type]}\nRequired: {arg.required}```",
                'inline': True
            })

        return discord.Embed.from_dict(embed)


def setup(bot):
    bot.add_cog(UtilsCog(bot))
