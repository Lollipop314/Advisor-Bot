import discord
import ast
import datetime
from discord.ext import commands

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

extensions = ['cogs.notawiki',
              'cogs.owner']

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Hidden means it won't show up on the default help.
    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def extload(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'Error! {type(e).__name__} - {e}')
        else:
            await ctx.send('Loaded the extension')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def extunload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'Error! {type(e).__name__} - {e}')
        else:
            await ctx.send('Unloaded the extension')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def extreload(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""
        if cog == 'all':
            async with ctx.channel.typing():
                for ext in extensions:
                    self.bot.unload_extension(ext)
                    self.bot.load_extension(ext)
            return await ctx.send(':recycle:  Rawr-loaded all the extensions!')
        else:
            try:
                self.bot.unload_extension(cog)
                self.bot.load_extension(cog)
            except Exception as e:
                await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
            else:
                await ctx.send(':recycle:  Rawr-loaded the extension!')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def quit(self, ctx):
        await ctx.bot.change_presence(status=discord.Status.invisible)
        await ctx.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def userid(self, ctx, member: discord.Member):
        await ctx.send(str(member.id))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guildid(self, ctx):
        await ctx.send(str(ctx.guild.id))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def roleid(self, ctx, role):
        if role not in ctx.server.roles:
            return await ctx.send('No role exists')
        else:
            return await ctx.send(discord.Role.id)

    def get_bot_uptime(self, *, brief=False):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def uptime(self, ctx):
        await ctx.send(f':alarm_clock: Uptime: {self.get_bot_uptime()}')

def setup(bot):
    bot.add_cog(Owner(bot))
