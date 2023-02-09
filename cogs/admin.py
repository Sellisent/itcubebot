from discord.ext import commands
import pymongo
from discord_slash import SlashCommand, SlashContext, cog_ext
from discord.ext.commands import Bot, Cog
import discord
from datetime import timedelta
import time

text_channels_category_id = ID_КАТЕГОРИИ_ТЕКСТОВЫХ_КАНАЛОВ
voice_channels_category_id = ID_КАТЕГОРИИ_ГОЛОСОВЫХ_КАНАЛОВ


class Admin(Cog):
    def __init__(self, bot: Bot):

        self.bot = bot
        self.db = pymongo.MongoClient(
            "КОНЕКТ_К_MONGODB")
        self.groups = self.db.itcube.groups
        self.users = self.db.itcube.users

    @cog_ext.cog_slash(name='addgroup', description='Добавить группу обучения',
                       options=[
                           {"name": "group", "description": "Название", "type": 3, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def addgroup(self, ctx: SlashContext, group):
        role = await ctx.guild.create_role(name=group)
        cat = discord.utils.get(ctx.guild.categories, id=text_channels_category_id)
        text = await ctx.guild.create_text_channel(name=group, category=cat)
        cat = discord.utils.get(ctx.guild.categories, id=voice_channels_category_id)
        voice = await ctx.guild.create_voice_channel(name=group, category=cat)
        await voice.set_permissions(ctx.guild.default_role, connect=False, view_channel=False)
        await voice.set_permissions(role, view_channel=True)
        await text.set_permissions(ctx.guild.default_role, view_channel=False)
        await text.set_permissions(role, view_channel=True)
        post = {
            "name": group,
            "role": role.id,
            "textid": text.id,
            "voiceid": voice.id
        }
        self.groups.insert_one(post)
        emb = discord.Embed(
            description=f"Группа {group} добавлена! \n RoleID: {role.id} \n TextID: {text.id} \n VoiceID: {voice.id}",
            color=0x87CEFA,
            title="__Добавление группы обучения__"
        )
        emb.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=emb)

    @cog_ext.cog_slash(name='start', description='Начать урок',
                       options=[
                           {"name": "group", "description": "Группа", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def startlesson(self, ctx: SlashContext, group):
        channel = discord.utils.get(ctx.guild.channels, id=self.groups.find_one({"role": group.id})['textid'])
        vchannel = discord.utils.get(ctx.guild.channels, id=self.groups.find_one({"role": group.id})['voiceid'])
        await vchannel.set_permissions(group, connect=True, view_channel=True)
        embed = discord.Embed(
            title=f"__Начало урока__",
            description=f"Для группы **{group.name}** начинается урок! \n Голосовой канал для учеников открыт.",
            color=0x87CEFA)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        await channel.send(f"**{group.mention} начинается урок! Всем просьба подключится к голосовому каналу!**")

    @cog_ext.cog_slash(name='stop', description='Завершить урок',
                       options=[
                           {"name": "group", "description": "Группа", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def endlesson(self, ctx: SlashContext, group):
        vchannel = discord.utils.get(ctx.guild.channels, id=self.groups.find_one({"role": group.id})['voiceid'])
        await vchannel.set_permissions(group, connect=False, view_channel=True)
        members = vchannel.members
        for member in members:
            await member.move_to(None)
        names = ""
        voicetime = ""
        for students in self.users.find({"group": group.id}):
            newtime = int(students['voice_online']) + students['voice_total']
            print(f'Обновление тотал {newtime}')
            names = f"{names}{students['name']} \n"
            if students['voice_online'] == 0:
                voicetime = f"{voicetime}:x: \n"
                self.users.update_one({"group": group.id, "name": students["name"]}, {"$set": {"skipped": students["skipped"]+1}})
            else:
                voicetime = f"{voicetime}{timedelta(seconds=int(students['voice_online']))} \n"
            self.users.update_one({"group": group.id, "name": students["name"]}, {"$set": {"voice_total": newtime}})
            self.users.update_one({"group": group.id, "name": students["name"]}, {"$set": {"voice_online": 0}})
        embed = discord.Embed(
            title=f"__Отчёт об уроке группы {group.name}__",
            description="Урок окончен! Всем спасибо за внимание!",
            color=0x87CEFA)
        embed.add_field(name="Пользователь:", value=names, inline=True)
        embed.add_field(name="Времени в гс:", value=voicetime, inline=True)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name='deluser', description='Удалить человека из группы',
                       options=[
                           {"name": "fullname", "description": "Имя и фамилия ученика", "type": 3, "required": True},
                           {"name": "group", "description": "Группа обучения", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def deluser(self, ctx: SlashContext, fullname, group):
        if self.users.find_one({"name": fullname, "group": group.id}) is None:
            embed = discord.Embed(
                title=f"__Ученик не найден!__",
                description="Проверьте правильность введённых данных.",
                color=0xff2400)
            await ctx.send(embed=embed)
        else:
            if self.users.find_one({"name": fullname, "group": group.id})['id'] is not None:
                await ctx.guild.get_member(
                    int(self.users.find_one({"name": fullname, "group": group.id})['id'])).remove_roles(group)
            self.users.delete_one({"name": fullname, "group": group.id})
            emb = discord.Embed(
                description=f"Ученик **{fullname}** удален из группы **{group.name}**!", color=0x87CEFA,
                title='__Удаление ученика__'
            )
            emb.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=emb)

    @cog_ext.cog_slash(name='list', description='Вывести список группы',
                       options=[
                           {"name": "group", "description": "Группа обучения", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def list(self, ctx: SlashContext, group):
        if self.users.count_documents({"group": group.id}) == 0:
            embed = discord.Embed(
                title=f"__Список группы {group.name}__",
                description="В этой группе нет учеников.",
                color=0x87CEFA)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"__Список группы {group.name}__",
                color=0x87CEFA)
            students = ""
            voice = ""
            skip = ""
            for gays in self.users.find({"group": group.id}):
                students += f"{gays['name']}\n"
                voice += f"{timedelta(seconds=int(gays['voice_total']))}\n"
                skip += f"{int(gays['skipped'])}\n"
            embed.add_field(name="Имя, фамилия:", value=students, inline=True)
            embed.add_field(name="Времени в гс:", value=voice, inline=True)
            embed.add_field(name="Пропущено:", value=skip, inline=True)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @cog_ext.cog_slash(name='delgroup', description='Удалить группу обучения',
                       options=[
                           {"name": "group", "description": "Группа обучения", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def delgroup(self, ctx: SlashContext, group):
        if self.groups.find_one({"name": group.name}) is None:
            embed = discord.Embed(
                title=f"__Группа не найдена!__",
                description="Проверьте правильность введённых данных.",
                color=0xff2400)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        else:
            channel = discord.utils.get(ctx.guild.channels, id=self.groups.find_one({"name": group.name})['textid'])
            await channel.delete()
            channel = discord.utils.get(ctx.guild.channels, id=self.groups.find_one({"name": group.name})['voiceid'])
            await channel.delete()
            role = discord.utils.get(ctx.guild.roles, id=self.groups.find_one({"role": group.id})['role'])
            self.users.delete_many({"group": role.id})
            await role.delete()
            self.groups.delete_one({"role": group.id})
            # for user in self.groups.find({"group": group}):
            #     if user[id] != None:
            #         await ctx.guild.get_member(user[id]).remove_roles(role)
            emb = discord.Embed(
                description=f"Группа **{group.name}** удалена!", color=0x87CEFA,
                title="__Удаление группы обучения__"
            )
            emb.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=emb)

    @cog_ext.cog_slash(name='adduser', description='Добавить ученика в группу',
                       options=[
                           {"name": "fullname", "description": "Фамилия и имя ученика", "type": 3, "required": True},
                           {"name": "group", "description": "Группа обучения", "type": 8, "required": True}
                       ],
                       guild_ids=[1015311530054647849])
    @commands.has_permissions(administrator=True)
    async def adduser(self, ctx: SlashContext, fullname, group):
        post = {
            "name": fullname,
            "group": group.id,
            "id": None,
            "skipped": 0,
            "voice_online": 0,
            "voice_total": 0
        }
        self.users.insert_one(post)
        embed = discord.Embed(
            description=f"**{fullname}** добавлен в группу **{group.name}**",
            title="__Добавление ученика в группу обучения__",
            color=0x87CEFA)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
