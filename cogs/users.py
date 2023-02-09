from discord.ext import commands
import pymongo
from discord_slash import SlashCommand, SlashContext, cog_ext
from discord.ext.commands import Bot, Cog
import discord
import time

text_channels_category_id = ID_КАТЕГОРИИ_ТЕКСТОВЫХ_КАНАЛОВ
voice_channels_category_id = ID_КАТЕГОРИИ_ГОЛОСОВЫХ_КАНАЛОВ

class Users(Cog):
    def __init__(self, bot: Bot):

        self.bot = bot
        self.db = pymongo.MongoClient(
            "КОНЕКТ_К_MONGODB")
        self.groups = self.db.itcube.groups
        self.users = self.db.itcube.users


    global tdict
    tdict = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if after.channel is not None and after.channel.id != 1015311530826412197:
                tdict[member.id] = time.time()
            if (before.channel.id != 1015311530826412197 and after.channel is None) or (before.channel.id != 1015311530826412197 and after.channel.id == 1015311530826412197):
                t2 = time.time() - tdict[member.id]
                print(f'Обновление онлайн {t2}')
                self.users.update_one({"id": member.id}, {"$set": {"voice_online": t2}})

        except Exception:
            pass

    @cog_ext.cog_slash(name='login', description='Войти',
                       options=[
                           {"name": "fullname", "description": "Фамилия и имя", "type": 3, "required": True},
                           {"name": "group", "description": "Группа обучения", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    async def login(self, ctx: SlashContext, fullname, group):
        if self.users.find_one({"name": fullname, "group": group.id}) is None:
            embed = discord.Embed(
                title=f"__Ученик не найден!__",
                description="Проверьте правильность введённых данных.",
                color=0xff2400)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        else:
            if self.users.find_one({"name": fullname, "group": group.id})['id'] is None:
                self.users.update_one({"fullname": fullname, "group": group.id}, {"$set": {"id": ctx.author.id}})
                await ctx.author.edit(nick=fullname)
                await ctx.author.add_roles(group)
                self.users.update_one({"name": fullname, "group": group.id},
                                      {"$set": {"id": ctx.author.id}})
                embed = discord.Embed(
                    title=f"__Вы успешно авторизовались!__",
                    description=f"Вы вошли как **{fullname}** \n Ваша группа — **{group.name}** \n *Удачного обучения!*",
                    color=0x87CEFA)
                embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"__Ученик уже авторизован!__",
                    description="Данный ученик уже авторизован в системе. Если вы этого не делали, тогда обратитесь к преподавателю.",
                    color=0xff2400)
                embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Users(bot))