import discord
from discord.ext import commands
import requests
import random
import key  # Importamos el archivo key.py con el token
import os  # Importar os para acceder a las variables de entorno
import yt_dlp as youtube_dl
from discord import FFmpegPCMAudio

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    help_command=None,
    activity=discord.Activity(type=discord.ActivityType.listening, name="¿Tienes dudas? Usa /ayuda")
)

# Lista para almacenar animes (persistente mientras el bot esté activo)
anime_list = []

# Configuración de youtube-dl y FFmpeg
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def unir(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await channel.connect()
            else:
                await ctx.voice_client.move_to(channel)
        else:
            await ctx.send("¡Debes estar en un canal de voz!")

    @commands.command()
    async def play(self, ctx, *, query):
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.invoke(self.unir)
            voice_client = ctx.voice_client

        try:
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            voice_client.play(FFmpegPCMAudio(info['url'], **ffmpeg_options))
            await ctx.send(f"🎵 Reproduciendo: **{info['title']}**")
        except Exception as e:
            await ctx.send(f"🔴 Error al reproducir: {str(e)}")

    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("✅ Desconectado del canal de voz.")

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    # Elimina o define la función setup si es necesaria
    # await setup(bot)

# Registrar el Cog
async def setup(bot):
    await bot.add_cog(Music(bot))

# Comandos adicionales...

# Iniciar el bot
bot.run(key.DISCORD_TOKEN)
