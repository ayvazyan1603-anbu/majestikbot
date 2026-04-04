import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import json
import os
from datetime import timedelta
from pathlib import Path

load_dotenv()

MOD_ROLE_ID  = int(os.getenv("MOD_ROLE_ID"))
MUTE_ROLE_ID = int(os.getenv("MUTE_ROLE_ID"))
LOG_WARN_ID  = int(os.getenv("LOG_WARN_ID"))

WARNS_FILE = Path("data/warns.json")
WARNS_FILE.parent.mkdir(exist_ok=True)

def load_warns() -> dict:
    if WARNS_FILE.exists():
        with open(WARNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_warns(data: dict):
    with open(WARNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_mod(member: disnake.Member) -> bool:
    return member.guild_permissions.administrator or any(r.id == MOD_ROLE_ID for r in member.roles)

def anbu_embed(title: str, desc: str, color: int = 0x2b2d31) -> disnake.Embed:
    e = disnake.Embed(title=title, description=desc, color=color)
    e.set_footer(text="Система ANBU • Автоматизация и разработка")
    e.timestamp = disnake.utils.utcnow()
    return e

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_mod(self, ctx: commands.Context):
        if not is_mod(ctx.author):
            raise commands.CheckFailure("no_perm")

    # ── Kick ──────────────────────────────────────────
    @commands.command(name="kick")
    async def kick(self, ctx: commands.Context, member: disnake.Member, *, reason: str = "Не указана"):
        self.check_mod(ctx)
        if is_mod(member):
            return await ctx.send(embed=anbu_embed("❌ Ошибка", "Нельзя кикнуть модератора.", 0xed4245))
        await member.kick(reason=reason)
        await ctx.send(embed=anbu_embed(
            "👢 Кик",
            f"**Игрок:** {member.mention}\n**Причина:** {reason}\n**Модератор:** {ctx.author.mention}",
            0xfee75c
        ))

    # ── Ban ───────────────────────────────────────────
    @commands.command(name="ban")
    async def ban(self, ctx: commands.Context, member: disnake.Member, *, reason: str = "Не указана"):
        self.check_mod(ctx)
        if is_mod(member):
            return await ctx.send(embed=anbu_embed("❌ Ошибка", "Нельзя забанить модератора.", 0xed4245))
        await member.ban(reason=reason, delete_message_days=0)
        await ctx.send(embed=anbu_embed(
            "🔨 Бан",
            f"**Игрок:** {member.mention}\n**Причина:** {reason}\n**Модератор:** {ctx.author.mention}",
            0xed4245
        ))

    # ── Unban ─────────────────────────────────────────
    @commands.command(name="unban")
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: str = "Не указана"):
        self.check_mod(ctx)
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(embed=anbu_embed(
                "✅ Разбан",
                f"**Игрок:** {user.mention}\n**Причина:** {reason}\n**Модератор:** {ctx.author.mention}",
                0x57f287
            ))
        except disnake.NotFound:
            await ctx.send(embed=anbu_embed("❌ Ошибка", "Пользователь не найден или не забанен.", 0xed4245))

    # ── Mute ──────────────────────────────────────────
    @commands.command(name="mute")
    async def mute(self, ctx: commands.Context, member: disnake.Member, duration: int = 10, *, reason: str = "Не указана"):
        """!mute @user [минуты] [причина]"""
        self.check_mod(ctx)
        if is_mod(member):
            return await ctx.send(embed=anbu_embed("❌ Ошибка", "Нельзя замутить модератора.", 0xed4245))
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            return await ctx.send(embed=anbu_embed("❌ Ошибка", "Роль мута не найдена.", 0xed4245))
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(embed=anbu_embed(
            "🔇 Мут",
            f"**Игрок:** {member.mention}\n**Длительность:** {duration} мин.\n**Причина:** {reason}\n**Модератор:** {ctx.author.mention}",
            0xfee75c
        ))
        await disnake.utils.sleep_until(disnake.utils.utcnow() + timedelta(minutes=duration))
        if mute_role in member.roles:
            await member.remove_roles(mute_role, reason="Мут истёк")

    # ── Unmute ────────────────────────────────────────
    @commands.command(name="unmute")
    async def unmute(self, ctx: commands.Context, member: disnake.Member):
        self.check_mod(ctx)
        mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
        if not mute_role or mute_role not in member.roles:
            return await ctx.send(embed=anbu_embed("❌ Ошибка", "Пользователь не в муте.", 0xed4245))
        await member.remove_roles(mute_role)
        await ctx.send(embed=anbu_embed(
            "🔊 Размут",
            f"**Игрок:** {member.mention}\n**Модератор:** {ctx.author.mention}",
            0x57f287
        ))

    # ── Warn ──────────────────────────────────────────
    @commands.command(name="warn")
    async def warn(self, ctx: commands.Context, member: disnake.Member, *, reason: str = "Не указана"):
        self.check_mod(ctx)
        if is_mod(member):
            return await ctx.send(embed=anbu_embed("❌ Ошибка", "Нельзя варнить модератора.", 0xed4245))

        warns = load_warns()
        uid = str(member.id)
        if uid not in warns:
            warns[uid] = []
        warns[uid].append({"reason": reason, "mod": str(ctx.author.id)})
        save_warns(warns)

        count = len(warns[uid])
        embed = anbu_embed(
            "⚠️ Варн",
            f"**Игрок:** {member.mention}\n**Причина:** {reason}\n**Варнов всего:** {count}\n**Модератор:** {ctx.author.mention}",
            0xfee75c
        )
        await ctx.send(embed=embed)

        # Лог варна
        log_ch = ctx.guild.get_channel(LOG_WARN_ID)
        if log_ch:
            await log_ch.send(embed=embed)

        # Автомут на 3 варне
        if count >= 3:
            mute_role = ctx.guild.get_role(MUTE_ROLE_ID)
            if mute_role:
                await member.add_roles(mute_role, reason="3 варна — автомут")
                await ctx.send(embed=anbu_embed(
                    "🔇 Автомут",
                    f"{member.mention} получил **3 варна** и замучен на 30 минут.",
                    0xed4245
                ))

    # ── Warns list ────────────────────────────────────
    @commands.command(name="warns")
    async def warns_list(self, ctx: commands.Context, member: disnake.Member):
        self.check_mod(ctx)
        warns = load_warns()
        uid = str(member.id)
        user_warns = warns.get(uid, [])

        if not user_warns:
            return await ctx.send(embed=anbu_embed("📋 Варны", f"У {member.mention} нет варнов.", 0x57f287))

        desc = f"**Игрок:** {member.mention}\n**Всего варнов:** {len(user_warns)}\n\n"
        for i, w in enumerate(user_warns, 1):
            desc += f"`{i}.` {w['reason']} — <@{w['mod']}>\n"

        await ctx.send(embed=anbu_embed("📋 Список варнов", desc, 0xfee75c))

    # ── Clearwarn ─────────────────────────────────────
    @commands.command(name="clearwarn")
    async def clearwarn(self, ctx: commands.Context, member: disnake.Member):
        self.check_mod(ctx)
        warns = load_warns()
        warns[str(member.id)] = []
        save_warns(warns)
        await ctx.send(embed=anbu_embed("✅ Варны сброшены", f"Варны {member.mention} очищены.", 0x57f287))

    # ── Clear ─────────────────────────────────────────
    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context, amount: int = 10):
        self.check_mod(ctx)
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(embed=anbu_embed("🧹 Очищено", f"Удалено **{amount}** сообщений.", 0x57f287))
        await msg.delete(delay=3)

    # ── Error handler ─────────────────────────────────
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=anbu_embed("❌ Нет прав", "Эта команда доступна только модераторам.", 0xed4245), delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=anbu_embed("❌ Ошибка", f"Не хватает аргумента: `{error.param.name}`", 0xed4245), delete_after=5)
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(embed=anbu_embed("❌ Ошибка", "Участник не найден.", 0xed4245), delete_after=5)

def setup(bot):
    bot.add_cog(Moderation(bot))