from discord.ext import commands
import discord
import os
from discord_slash import SlashCommand, SlashContext

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)
bot.remove_command("help")


@bot.event
async def on_ready():
    print("ITCube bot started")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("Developed by Sellisent"))

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1015311530826412196)
    embed = discord.Embed(title = "Добро пожаловать!", color = 0x87CEFA,
    description = f"{member.mention}, чтобы начать обучение, используйте команду \n /login <ваше имя и фамилия> <группа_обучения>")
    embed.set_thumbnail(url = member.avatar_url)
    embed.set_footer(text = "Отправлено автоматически ботом ITCube", icon_url=bot.user.avatar_url)
    await channel.send(embed = embed)

@slash.slash(name='reload', description='Перезагрузить ког',
             options=[{"name": "cog", "description": "название файла-кога", "type": 3, "required": True}],
             guild_ids=[1015311530054647849])
@commands.has_permissions(administrator=True)
async def reload(ctx: SlashContext, cog):
    if not os.path.exists(f"cogs/{cog}.py"):
        await ctx.send(
            embed=discord.Embed(title=f"__Доступ разрешён!__", description=f"{cog} не найден!", color=0x87CEFA))
    else:
        await ctx.send(
            embed=discord.Embed(title="__Доступ разрешён!__", description=f"{cog} перезагружен", color=0x87CEFA))
        bot.unload_extension(f"cogs.{cog}")
        bot.load_extension(f"cogs.{cog}")
        print(f'Перезагрузил ког {cog}')


@slash.slash(name='unload', description='Выгрузить ког',
             options=[{"name": "cog", "description": "название файла-кога", "type": 3, "required": True}],
             guild_ids=[1015311530054647849])
@commands.has_permissions(administrator=True)
async def unload(ctx: SlashContext, cog):
    if not os.path.exists(f"cogs/{cog}.py"):
        await ctx.send(
            embed=discord.Embed(title=f"__Доступ разрешён!__", description=f"{cog} не найден!", color=0x87CEFA))
    else:
        await ctx.send(
            embed=discord.Embed(title="__Доступ разрешён!__", description=f"{cog} отключен", color=0x87CEFA))
        bot.unload_extension(f"cogs.{cog}")
        print(f'Выгрузил ког {cog}')


@slash.slash(name="load", description="Загрузить ког",
             options=[{"name": "cog", "description": "название файла-кога", "type": 3, "required": True}],
             guild_ids=[1015311530054647849])
@commands.has_permissions(administrator=True)
async def load(ctx: SlashContext, cog: str):
    if not os.path.exists(f"cogs/{cog}.py"):
        await ctx.send(
            embed=discord.Embed(title=f"__Доступ разрешён!__", description=f"{cog} не найден!", color=0x87CEFA))
    else:
        await ctx.send(
            embed=discord.Embed(title="__Доступ разрешён!__", description=f"{cog} загружен", color=0x87CEFA))
        bot.load_extension(f"cogs.{cog}")
        print(f'Загрузил ког {cog}')


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        print(f'{filename[:-3]} loding...')

bot.run("ТОКЕН_БОТА")
