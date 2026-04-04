import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        embed = disnake.Embed(
            title="⛩ ДОБРО ПОЖАЛОВАТЬ",
            description=(
                f"### {member.mention} вступил в **{member.guild.name}**\n\n"
                f"Ты стал **{member.guild.member_count}-м** участником.\n"
                f"Ознакомься с правилами и получи роли."
            ),
            color=0x2b2d31
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url="https://i.pinimg.com/originals/b3/4b/d0/b34bd0ef85660338e6082332e0d31a7f.gif")
        # ^ замени на свой GIF
        embed.set_footer(text="Система ANBU • Автоматизация и разработка")
        embed.timestamp = disnake.utils.utcnow()

        await channel.send(content=member.mention, embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))