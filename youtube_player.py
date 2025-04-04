from discord.ext import commands
import discord
import yt_dlp

class YouTubePlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx, *, titulo: str):
        """Reproduce audio de YouTube sin usar FFmpeg"""
        if not ctx.author.voice:
            return await ctx.send("🔇 Debes estar en un canal de voz")

        channel = ctx.author.voice.channel
        vc = await channel.connect() if not ctx.voice_client else ctx.voice_client

        ydl_opts = {"format": "bestaudio", "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{titulo}", download=False)["entries"][0]

        # Attempt to play using direct stream URL
        url = info["url"]
        source = await discord.FFmpegOpusAudio.from_probe(url, method="fallback")
        vc.play(source)

        embed = discord.Embed(title="🎵 Reproduciendo", description=f"{info['title']}", color=0x1DB954)
        embed.set_thumbnail(url=info["thumbnail"])
        await ctx.send(embed=embed)

    @commands.command()
    async def leave(self, ctx):
        """Desconecta al bot de voz"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("🔇 Desconectado del canal de voz")
        else:
            await ctx.send("🤖 No estoy en ningún canal de voz")

def setup(bot):
    bot.add_cog(YouTubePlayer(bot))