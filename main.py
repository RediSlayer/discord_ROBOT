import discord
from discord.ext import commands
import requests
import random
import key
import os
import yt_dlp as youtube_dl
from discord import FFmpegPCMAudio
import asyncio

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

# Lista para almacenar animes
anime_list = []
# Sistema de colas de música
music_queues = {}

# Configuración optimizada para música
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto'
}

def check_queue(ctx):
    if music_queues.get(ctx.guild.id) and len(music_queues[ctx.guild.id]) > 0:
        source = music_queues[ctx.guild.id].pop(0)
        ctx.voice_client.play(source, after=lambda e: check_queue(ctx))

@bot.command()
async def unir(ctx):
    """Une el bot al canal de voz"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)
        await ctx.send(f"🎤 Conectado a {channel.name}")
    else:
        await ctx.send("🔇 Debes estar en un canal de voz")

@bot.command()
async def play(ctx, *, query):
    """Reproduce música desde YouTube"""
    voice_client = ctx.voice_client or await ctx.invoke(unir)
    
    try:
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            url = info['entries'][0]['url']
            title = info['entries'][0]['title']
            
            source = FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            
            if not voice_client.is_playing():
                voice_client.play(source, after=lambda e: check_queue(ctx))
                await ctx.send(f"🎶 Reproduciendo: **{title}**")
            else:
                if ctx.guild.id not in music_queues:
                    music_queues[ctx.guild.id] = []
                music_queues[ctx.guild.id].append(source)
                await ctx.send(f"🎵 Añadido a la cola: **{title}**")
                
    except Exception as e:
        await ctx.send(f"🔴 Error: {str(e)}")

@bot.command()
async def pausa(ctx):
    """Pausa la reproducción actual"""
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Pausado")

@bot.command()
async def reanudar(ctx):
    """Reanuda la reproducción"""
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Reanudado")

@bot.command()
async def saltar(ctx):
    """Salta la canción actual"""
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        check_queue(ctx)
        await ctx.send("⏭️ Saltado")

@bot.command()
async def cola(ctx):
    """Muestra la cola de reproducción"""
    if ctx.guild.id in music_queues and music_queues[ctx.guild.id]:
        embed = discord.Embed(title="🎵 Cola de reproducción", color=0x3498db)
        for i, item in enumerate(music_queues[ctx.guild.id], 1):
            embed.add_field(name=f"{i}. Canción en cola", value="\u200b", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("📭 La cola está vacía")

@bot.command()
async def leave(ctx):
    """Desconecta el bot del canal de voz"""
    if ctx.voice_client:
        if ctx.guild.id in music_queues:
            music_queues[ctx.guild.id].clear()
        await ctx.voice_client.disconnect()
        await ctx.send("✅ Desconectado")
    else:
        await ctx.send("🤖 No estoy conectado")

# [TODOS TUS OTROS COMANDOS EXISTENTES PERMANECEN IGUAL]
# randomanime, buscaranime, añadir, elegir, lista, eliminar, limpiar, perfil, ship, osu, msj
# ...

@bot.command()
async def ayuda(ctx):
    """Muestra todos los comandos disponibles"""
    embed = discord.Embed(
        title="🎌 **Ayuda del Bot de Anime**",
        description="Lista de comandos disponibles:\n(Prefijo: `/`)",
        color=0x2b2d31
    )
    
    embed.add_field(
        name="🔍 **Búsqueda de Anime**",
        value=(
            "`/buscaranime <nombre>` - Busca información de un anime\n"
            "`/añadir <nombre>` - Añade un anime a tu lista\n"
            "`/lista` - Muestra tu lista de animes\n"
            "`/elegir` - Elige un anime aleatorio\n"
            "`/randomanime <genero>` - Recomienda un anime por género"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎵 **Música**",
        value=(
            "`/unir` - Une el bot a tu canal de voz\n"
            "`/play <canción>` - Reproduce música\n"
            "`/pausa` - Pausa la reproducción\n"
            "`/reanudar` - Reanuda la reproducción\n"
            "`/saltar` - Salta la canción actual\n"
            "`/cola` - Muestra la cola de reproducción\n"
            "`/leave` - Desconecta el bot"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👥 **Social**",
        value=(
            "`/perfil [usuario]` - Muestra un perfil\n"
            "`/ship <usuario1> <usuario2>` - Calcula compatibilidad\n"
            "`/osu <usuario>` - Info de perfil de osu!\n"
            "`/msj <mensaje>` - Repite un mensaje"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚙️ **Moderación**",
        value=(
            "`/eliminar <número>` - Elimina anime de la lista\n"
            "`/limpiar` - Vacía toda la lista"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Pedido por {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')

bot.run(key.DISCORD_TOKEN)

