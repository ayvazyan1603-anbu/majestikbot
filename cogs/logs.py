import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

LOG_JOIN_ID     = int(os.getenv("LOG_JOIN_ID"))
LOG_LEAVE_ID    = int(os.getenv("LOG_LEAVE_ID"))
LOG_NAME_ID     = int(os.getenv("LOG_NAME_ID"))
LOG_WARN_ID     = int(os.getenv("LOG_WARN_ID"))
LOG_ROLES_ID    = int(os.getenv("LOG_ROLES_ID"))
LOG_MESSAGES_ID = int(os.getenv("LOG_MESSAGES_ID"))
LOG_VOICE_ID    = int(os.getenv("LOG_VOICE_ID"))

def make_embed(title: str, description: str, color: int) -> disnake.Embed:
    embed = disnake.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Система ANBU • Автоматизация и разработка")
    embed.timestamp = disnake.utils.utcnow()
    return embed

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def ch(self, guild: disnake.Guild, channel_id: int):
        return guild.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        ch = self.ch(member.guild, LOG_JOIN_ID)
        if ch:
            embed = make_embed(
                "📥 Участник зашёл",
                f"{member.mention} (`{member.id}`)\n"
                f"Аккаунт создан: <t:{int(member.created_at.timestamp())}:R>",
                0x57f287
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        ch = self.ch(member.guild, LOG_LEAVE_ID)
        if ch:
            embed = make_embed(
                "📤 Участник вышел",
                f"{member.mention} (`{member.id}`)\n"
                f"Был на сервере с: <t:{int(member.joined_at.timestamp())}:R>",
                0xed4245
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        # Ник
        if before.nick != after.nick:
            ch = self.ch(after.guild, LOG_NAME_ID)
            if ch:
                await ch.send(embed=make_embed(
                    "✏️ Смена ника",
                    f"{after.mention}\n**До:** `{before.nick or before.name}`\n**После:** `{after.nick or after.name}`",
                    0xfee75c
                ))

        # Роли
        if before.roles != after.roles:
            ch = self.ch(after.guild, LOG_ROLES_ID)
            if ch:
                added   = [r for r in after.roles if r not in before.roles]
                removed = [r for r in before.roles if r not in after.roles]
                desc = f"{after.mention}\n"
                if added:
                    desc += f"**➕ Добавлены:** {', '.join(r.mention for r in added)}\n"
                if removed:
                    desc += f"**➖ Убраны:** {', '.join(r.mention for r in removed)}"
                await ch.send(embed=make_embed("🎭 Роли изменены", desc, 0x5865f2))

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot or not message.guild:
            return
        ch = self.ch(message.guild, LOG_MESSAGES_ID)
        if ch:
            await ch.send(embed=make_embed(
                "🗑 Сообщение удалено",
                f"**Автор:** {message.author.mention}\n"
                f"**Канал:** {message.channel.mention}\n"
                f"**Текст:** {message.content[:1000] or '*без текста*'}",
                0xfee75c
            ))

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        ch = self.ch(before.guild, LOG_MESSAGES_ID)
        if ch:
            await ch.send(embed=make_embed(
                "📝 Сообщение изменено",
                f"**Автор:** {before.author.mention}\n"
                f"**Канал:** {before.channel.mention}\n"
                f"**До:** {before.content[:500]}\n"
                f"**После:** {after.content[:500]}",
                0xfee75c
            ))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        ch = self.ch(member.guild, LOG_VOICE_ID)
        if not ch:
            return
        if not before.channel and after.channel:
            await ch.send(embed=make_embed("🔊 Вошёл в войс", f"{member.mention} → {after.channel.mention}", 0x57f287))
        elif before.channel and not after.channel:
            await ch.send(embed=make_embed("🔇 Вышел из войса", f"{member.mention} ← {before.channel.mention}", 0xed4245))
        elif before.channel != after.channel:
            await ch.send(embed=make_embed("🔀 Сменил канал", f"{member.mention}\n{before.channel.mention} → {after.channel.mention}", 0xfee75c))

def setup(bot):
    bot.add_cog(Logs(bot))