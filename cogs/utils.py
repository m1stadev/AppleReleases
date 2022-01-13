# imports
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
        return discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(268651520), scopes=('bot', 'applications.commands'))

    async def cmd_help_embed(self, ctx: discord.ApplicationContext, cmd: discord.SlashCommand):
        embed = {
            'description': cmd.description,
            'fields': list(),
            'footer': {
                'text': ctx.author.display_name,
                'icon_url': str(ctx.author.display_avatar.with_static_format('png').url)
            }
        }

        if cmd.full_parent_name:
            embed['title'] = f"/{' '.join((cmd.full_parent_name, cmd.name))}",
        else:
            embed['title'] = f"/{cmd.name}",

        for arg in cmd.options:
            embed['title'] += f'<{arg.name}> ' if arg.required else f'[{arg.name}] '
            embed['fields'].append({
                'name': f'<{arg.name}>' if arg.required else f'[{arg.name}]',
                'value': f"```Description: {arg.description or 'No description'}\nInput Type: {self.READABLE_INPUT_TYPES[arg.input_type]}\nRequired: {arg.required}```",
                'inline': True
            })

        return discord.Embed.from_dict(embed)

    async def cog_help_embed(self, ctx: discord.ApplicationContext, cog: str) -> list[discord.Embed]:
        embed = {
            'title': f"{cog.capitalize() if cog != 'tss' else cog.upper()} Commands",
            'fields': list(),
            'footer': {
                'text': ctx.author.display_name,
                'icon_url': str(ctx.author.display_avatar.with_static_format('png').url)
            }
        }

        for cmd in self.bot.cogs[cog].get_commands():
            if isinstance(cmd, discord.SlashCommandGroup):
                continue

            cmd_field = {
                'name': f"/{cmd.name} ",
                'value': cmd.description,
                'inline': False
            }

            for arg in cmd.options:
                cmd_field['name'] += f'<{arg.name}> ' if arg.required else f'[{arg.name}] '

            embed['fields'].append(cmd_field)

        embed['fields'] = sorted(embed['fields'], key=lambda field: field['name'])
        return discord.Embed.from_dict(embed)

    async def group_help_embed(self, ctx: discord.ApplicationContext, group: discord.SlashCommandGroup) -> list[discord.Embed]:
        embed = {
            'title': f"{group.name.capitalize() if group.name != 'tss' else group.name.upper()} Commands",
            'fields': list(),
            'footer': {
                'text': ctx.author.display_name,
                'icon_url': str(ctx.author.display_avatar.with_static_format('png').url)
            }
        }

        for cmd in group.subcommands:
            cmd_field = {
                'name': f"/{' '.join((group.name, cmd.name))} ",
                'value': cmd.description,
                'inline': False
            }
            for arg in cmd.options:
                cmd_field['name'] += f'<{arg.name}> ' if arg.required else f'[{arg.name}] '

            embed['fields'].append(cmd_field)

        embed['fields'] = sorted(embed['fields'], key=lambda field: field['name'])
        return discord.Embed.from_dict(embed)


def setup(bot):
    bot.add_cog(UtilsCog(bot))
