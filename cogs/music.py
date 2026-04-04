import disnake
from disnake.ext import commands
import wavelink


class MusicControls(disnake.ui.View):
    def __init__(self, player: wavelink.Player, author_id: int):
        super().__init__(timeout=None)
        self.player = player
        self.author_id = author_id

    def check_access(self, interaction: disnake.MessageInteraction):
        # только автор ИЛИ человек в том же голосовом канале
        if interaction.user.id == self.author_id:
            return True

        vc = interaction.guild.voice_client
        if vc and interaction.user in vc.channel.members:
            return True

        return False

    async def deny(self, interaction):
        await interaction.response.send_message(
            "❌ Ты не можешь управлять этим плеером",
            ephemeral=True
        )

    @disnake.ui.button(label="⏯", style=disnake.ButtonStyle.gray)
    async def pause_resume(self, button, interaction: disnake.MessageInteraction):
        if not self.check_access(interaction):
            return await self.deny(interaction)

        if self.player.paused:
            await self.player.pause(False)
            await interaction.response.send_message("▶️ Продолжено", ephemeral=True)
        else:
            await self.player.pause(True)
            await interaction.response.send_message("⏸ Пауза", ephemeral=True)

    @disnake.ui.button(label="⏭", style=disnake.ButtonStyle.blurple)
    async def skip(self, button, interaction: disnake.MessageInteraction):
        if not self.check_access(interaction):
            return await self.deny(interaction)

        await self.player.skip()
        await interaction.response.send_message("⏭ Пропущено", ephemeral=True)

    @disnake.ui.button(label="⏹", style=disnake.ButtonStyle.red)
    async def stop(self, button, interaction: disnake.MessageInteraction):
        if not self.check_access(interaction):
            return await self.deny(interaction)

        self.player.queue.clear()
        await self.player.stop()
        await self.player.disconnect()
        await interaction.response.send_message("⏹ Остановлено", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def connect_node(self):
        await self.bot.wait_until_ready()

        node = wavelink.Node(
            uri="https://maj-music-1.onrender.com",
            password="majmusic"
        )

        await wavelink.Pool.connect(nodes=[node], client=self.bot)
        print("[LAVALINK] Connected")

    @commands.Cog.listener()
    async def on_ready(self):
        if not wavelink.Pool.nodes:
            self.bot.loop.create_task(self.connect_node())

    async def get_player(self, ctx):
        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        return vc

    def embed(self, title, desc, color=0x2b2d31):
        return disnake.Embed(title=title, description=desc, color=color)

    @commands.command()
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send(embed=self.embed("❌", "Зайди в голосовой канал", 0xed4245))

        player: wavelink.Player = await self.get_player(ctx)

        tracks = await wavelink.Playable.search(query)

        if not tracks:
            return await ctx.send(embed=self.embed("❌", "Ничего не найдено", 0xed4245))

        track = tracks[0]

        if not player.playing:
            await player.play(track)
            await ctx.send(
                embed=self.embed("🎵 Играет", f"{track.title}", 0x57f287),
                view=MusicControls(player, ctx.author.id)
            )
        else:
            await player.queue.put_wait(track)
            await ctx.send(embed=self.embed("📋 В очередь", f"{track.title}", 0x5865f2))

    @commands.command()
    async def skip(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if not player or not player.playing:
            return await ctx.send(embed=self.embed("❌", "Ничего не играет", 0xed4245))

        await player.skip()
        await ctx.send(embed=self.embed("⏭", "Пропущено", 0xfee75c))

    @commands.command()
    async def stop(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if not player:
            return

        player.queue.clear()
        await player.stop()
        await player.disconnect()

        await ctx.send(embed=self.embed("⏹", "Остановлено", 0xed4245))

    @commands.command()
    async def pause(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if player and player.playing:
            await player.pause(True)
            await ctx.send(embed=self.embed("⏸", "Пауза", 0xfee75c))

    @commands.command()
    async def resume(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if player and player.paused:
            await player.pause(False)
            await ctx.send(embed=self.embed("▶️", "Продолжено", 0x57f287))

    @commands.command()
    async def volume(self, ctx, vol: int):
        player: wavelink.Player = ctx.voice_client

        if not player:
            return

        vol = max(0, min(150, vol))
        await player.set_volume(vol)

        await ctx.send(embed=self.embed("🔊", f"{vol}%", 0x57f287))

    @commands.command()
    async def queue(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if not player:
            return await ctx.send(embed=self.embed("📋", "Пусто", 0xfee75c))

        desc = ""

        if player.current:
            desc += f"▶️ {player.current.title}\n\n"

        for i, track in enumerate(player.queue[:10], 1):
            desc += f"{i}. {track.title}\n"

        await ctx.send(embed=self.embed("📋 Очередь", desc, 0x5865f2))

    @commands.command()
    async def loop(self, ctx):
        player: wavelink.Player = ctx.voice_client

        if not player:
            return

        player.autoplay = not player.autoplay

        await ctx.send(embed=self.embed("🔁", f"Loop: {player.autoplay}", 0x5865f2))


    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player

        if player.queue:
            next_track = await player.queue.get_wait()
            await player.play(next_track)


def setup(bot):
    bot.add_cog(Music(bot))
