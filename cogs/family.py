import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

FAMILY_CHANNEL_ID = int(os.getenv("FAMILY_CHANNEL_ID"))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID"))
FAMILY_ROLE_ID = int(os.getenv("FAMILY_ROLE_ID"))


# ──────────────────────────────────────────
# Модал: заявка на вступление
# ──────────────────────────────────────────
class FamilyModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Ник в игре",
                placeholder="Например: Alex_Johnson",
                custom_id="nick",
                style=disnake.TextInputStyle.short,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Static (статистика)",
                placeholder="Например: #123123",
                custom_id="static",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(title="🎭 Заявка в Leverage Family", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        nick = inter.text_values["nick"]
        static = inter.text_values["static"]
        applicant = inter.author

        await inter.response.send_message("✅ Заявка отправлена! Ожидай решения администрации.", ephemeral=True)

        admin_channel = inter.guild.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            return

        embed = disnake.Embed(
            title="📋 НОВАЯ ЗАЯВКА | Leverage Family",
            color=0x2b2d31
        )
        embed.add_field(name="👤 Игрок", value=f"{applicant.mention}\n`{applicant.id}`", inline=True)
        embed.add_field(name="🎮 Ник", value=f"`{nick}`", inline=True)
        embed.add_field(name="📊 Static", value=f"`{static}`", inline=True)
        embed.set_thumbnail(url=applicant.display_avatar.url)
        embed.set_footer(text="Система ANBU • Автоматизация и разработка")
        embed.timestamp = disnake.utils.utcnow()

        view = AdminDecisionView(
            applicant_id=applicant.id,
            applicant_nick=nick,
            applicant_static=static,
            origin_channel_id=FAMILY_CHANNEL_ID
        )
        await admin_channel.send(embed=embed, view=view)


# ──────────────────────────────────────────
# Кнопка: Получить роль
# ──────────────────────────────────────────
class FamilyJoinView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Получить роль",
        style=disnake.ButtonStyle.danger,
        emoji="🎭",
        custom_id="family_join"
    )
    async def join_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(FamilyModal())


# ──────────────────────────────────────────
# Модал: причина отказа
# ──────────────────────────────────────────
class DenyReasonModal(disnake.ui.Modal):
    def __init__(self, applicant_id: int, applicant_nick: str, origin_channel_id: int, admin_message: disnake.Message):
        self.applicant_id = applicant_id
        self.applicant_nick = applicant_nick
        self.origin_channel_id = origin_channel_id
        self.admin_message = admin_message

        components = [
            disnake.ui.TextInput(
                label="Причина отказа",
                placeholder="Укажи причину отказа...",
                custom_id="reason",
                style=disnake.TextInputStyle.paragraph,
                max_length=500,
            )
        ]
        super().__init__(title="❌ Причина отказа", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        reason = inter.text_values["reason"]
        admin = inter.author

        await inter.response.defer()

        origin_channel = inter.guild.get_channel(self.origin_channel_id)
        if origin_channel:
            embed = disnake.Embed(
                title="❌ ЗАЯВКА ОТКЛОНЕНА",
                color=0xed4245
            )
            embed.add_field(name="🎮 Ник", value=f"`{self.applicant_nick}`", inline=True)
            embed.add_field(name="📋 Причина", value=reason, inline=False)
            embed.set_footer(text="Система ANBU • Автоматизация и разработка")
            embed.timestamp = disnake.utils.utcnow()

            result_view = ResultView(approved=False, admin=admin)
            await origin_channel.send(embed=embed, view=result_view)

        disabled_view = AdminDecisionView(
            applicant_id=self.applicant_id,
            applicant_nick=self.applicant_nick,
            applicant_static="",
            origin_channel_id=self.origin_channel_id,
            disabled=True
        )
        try:
            await self.admin_message.edit(view=disabled_view)
        except Exception:
            pass


# ──────────────────────────────────────────
# Кнопки: Одобрить / Отказать (для админов)
# ──────────────────────────────────────────
class AdminDecisionView(disnake.ui.View):
    def __init__(self, applicant_id: int, applicant_nick: str, applicant_static: str, origin_channel_id: int, disabled: bool = False):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.applicant_nick = applicant_nick
        self.applicant_static = applicant_static
        self.origin_channel_id = origin_channel_id

        approve_btn = disnake.ui.Button(
            label="Одобрить",
            style=disnake.ButtonStyle.success,
            emoji="✅",
            custom_id=f"approve_{applicant_id}",
            disabled=disabled
        )
        deny_btn = disnake.ui.Button(
            label="Отказать",
            style=disnake.ButtonStyle.danger,
            emoji="❌",
            custom_id=f"deny_{applicant_id}",
            disabled=disabled
        )
        approve_btn.callback = self.approve_callback
        deny_btn.callback = self.deny_callback
        self.add_item(approve_btn)
        self.add_item(deny_btn)

    async def approve_callback(self, inter: disnake.MessageInteraction):
        guild = inter.guild
        admin = inter.author
        member = guild.get_member(self.applicant_id)

        await inter.response.defer()

        if member:
            role = guild.get_role(FAMILY_ROLE_ID)
            if role:
                try:
                    await member.add_roles(role, reason="Принят в Leverage Family")
                except Exception:
                    pass

        origin_channel = guild.get_channel(self.origin_channel_id)
        if origin_channel:
            embed = disnake.Embed(
                title="✅ ЗАЯВКА ОДОБРЕНА",
                color=0x57f287
            )
            embed.add_field(name="🎮 Ник", value=f"`{self.applicant_nick}`", inline=True)
            embed.add_field(name="👤 Игрок", value=f"<@{self.applicant_id}>", inline=True)
            embed.set_footer(text="Система ANBU • Автоматизация и разработка")
            embed.timestamp = disnake.utils.utcnow()

            result_view = ResultView(approved=True, admin=admin)
            await origin_channel.send(embed=embed, view=result_view)

        disabled_view = AdminDecisionView(
            applicant_id=self.applicant_id,
            applicant_nick=self.applicant_nick,
            applicant_static=self.applicant_static,
            origin_channel_id=self.origin_channel_id,
            disabled=True
        )
        await inter.message.edit(view=disabled_view)

    async def deny_callback(self, inter: disnake.MessageInteraction):
        modal = DenyReasonModal(
            applicant_id=self.applicant_id,
            applicant_nick=self.applicant_nick,
            origin_channel_id=self.origin_channel_id,
            admin_message=inter.message
        )
        await inter.response.send_modal(modal)


# ──────────────────────────────────────────
# Итоговые кнопки (только для отображения)
# ──────────────────────────────────────────
class ResultView(disnake.ui.View):
    def __init__(self, approved: bool, admin: disnake.Member):
        super().__init__(timeout=None)

        status_btn = disnake.ui.Button(
            label="Одобрено" if approved else "Отказано",
            style=disnake.ButtonStyle.success if approved else disnake.ButtonStyle.danger,
            disabled=True
        )
        who_btn = disnake.ui.Button(
            label=f"{'Одобрил' if approved else 'Отказал'}: {admin.display_name}",
            style=disnake.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(status_btn)
        self.add_item(who_btn)


# ──────────────────────────────────────────
# Ког
# ──────────────────────────────────────────
class Family(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(FamilyJoinView())
        print("✅ Family views зарегистрированы")

    @commands.command(name="setup_family")
    @commands.has_permissions(administrator=True)
    async def setup_family(self, ctx: commands.Context):
        await ctx.message.delete()

        embed = disnake.Embed(
            title="🎭 ПОЛУЧЕНИЕ РОЛЕЙ | Leverage Family",
            description=(
                "Ты уже с нами? Тогда подтверди своё участие в семье и получи роль в Discord.\n\n"
                "Заполни анкету ниже и ожидай решения администрации."
            ),
            color=0x2b2d31
        )
        embed.set_footer(text="Система ANBU • Автоматизация и разработка")
        embed.timestamp = disnake.utils.utcnow()

        await ctx.send(embed=embed, view=FamilyJoinView())

    @commands.command(name="uninvite")
    @commands.has_permissions(administrator=True)
    async def uninvite(self, ctx: commands.Context, member: disnake.Member):
        role = ctx.guild.get_role(FAMILY_ROLE_ID)

        if not role:
            return await ctx.send(embed=disnake.Embed(
                title="❌ Ошибка",
                description="Роль не найдена.",
                color=0xed4245
            ).set_footer(text="Система ANBU • Автоматизация и разработка"))

        if role not in member.roles:
            return await ctx.send(embed=disnake.Embed(
                title="❌ Ошибка",
                description=f"У {member.mention} нет роли Family Member.",
                color=0xed4245
            ).set_footer(text="Система ANBU • Автоматизация и разработка"))

        await member.remove_roles(role, reason=f"Uninvite от {ctx.author}")
        await ctx.send(embed=disnake.Embed(
            title="✅ Роль снята",
            description=f"{member.mention} исключён из Leverage Family.\n**Модератор:** {ctx.author.mention}",
            color=0xed4245
        ).set_footer(text="Система ANBU • Автоматизация и разработка"))


def setup(bot):
    bot.add_cog(Family(bot))
