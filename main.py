import discord
from discord.ext import commands
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import yt_dlp
import os

# Configuración del bot con prefijo /
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)

# Variables globales
FONDO_URL = "https://media.tenor.com/BXDrQy1pBp8AAAAd/heart-love.gif"

# ------------------------------------------
# Funciones auxiliares
# ------------------------------------------

async def generar_imagen(usuario1, usuario2, porcentaje):
    """Genera imagen para el comando ship"""
    response = requests.get(FONDO_URL)
    fondo = Image.open(BytesIO(response.content)).convert("RGBA").resize((500, 250))
    
    avatar1 = Image.open(BytesIO(requests.get(usuario1.avatar.url).content)).convert("RGBA").resize((100, 100))
    avatar2 = Image.open(BytesIO(requests.get(usuario2.avatar.url).content)).convert("RGBA").resize((100, 100))
    
    fondo.paste(avatar1, (50, 75), avatar1)
    fondo.paste(avatar2, (350, 75), avatar2)
    
    draw = ImageDraw.Draw(fondo)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    textos = [
        (f"Compatibilidad: {porcentaje}%", (200, 20)),
        (usuario1.name, (50, 180)),
        (usuario2.name, (350, 180))
    ]
    
    for texto, pos in textos:
        draw.text(pos, texto, fill="white", font=font)
    
    img_bytes = BytesIO()
    fondo.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

# ------------------------------------------
# Comandos
# ------------------------------------------

@bot.command()
async def ship(ctx, usuario1: discord.Member, usuario2: discord.Member):
    """Calcula la compatibilidad entre dos usuarios con imagen"""
    porcentaje = random.randint(0, 100)
    imagen = await generar_imagen(usuario1, usuario2, porcentaje)
    
    embed = discord.Embed(title="💘 Shipómetro", color=discord.Color.pink())
    embed.add_field(name="Personas", value=f"{usuario1.mention} ❤️ {usuario2.mention}", inline=False)
    embed.add_field(name="Compatibilidad", value=f"**{porcentaje}%**", inline=False)
    embed.set_footer(text="¡Que viva el amor!")
    
    await ctx.send(embed=embed, file=discord.File(imagen, "ship.png"))

@bot.command()
async def perfil(ctx, usuario: discord.Member = None):
    """Muestra información de un usuario"""
    usuario = usuario or ctx.author
    embed = discord.Embed(title=f"👤 Perfil de {usuario.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=usuario.avatar.url)
    embed.add_field(name="🆔 ID", value=usuario.id, inline=True)
    embed.add_field(name="📅 Creación", value=usuario.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="📌 Ingreso", value=usuario.joined_at.strftime("%d/%m/%Y"), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def play(ctx, *, titulo: str):
    """Reproduce audio de YouTube"""
    if not ctx.author.voice:
        return await ctx.send("🔇 Debes estar en un canal de voz")
    
    channel = ctx.author.voice.channel
    vc = await channel.connect() if not ctx.voice_client else ctx.voice_client
    
    ydl_opts = {"format": "bestaudio", "quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{titulo}", download=False)["entries"][0]
    
    vc.play(discord.FFmpegPCMAudio(info["url"], options="-vn"))
    
    embed = discord.Embed(title="🎵 Reproduciendo", description=f"**{info['title']}**", color=0x1DB954)
    embed.set_thumbnail(url=info["thumbnail"])
    await ctx.send(embed=embed)

@bot.command()
async def leave(ctx):
    """Desconecta al bot de voz"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🔇 Desconectado del canal de voz")
    else:
        await ctx.send("🤖 No estoy en ningún canal de voz")

# ------------------------------------------
# Comando Help mejorado
# ------------------------------------------

@bot.command(name="help", aliases=["ayuda"])
async def help(ctx):
    """Muestra todos los comandos disponibles"""
    embed = discord.Embed(
        title="🌟 Menú de Ayuda",
        description="Todos los comandos disponibles:",
        color=0x5865F2
    )
    
    embed.add_field(
        name="💘 Comandos Sociales",
        value=(
            "`/ship @usuario1 @usuario2` - Calcula compatibilidad\n"
            "`/perfil [@usuario]` - Muestra información de usuario"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎵 Comandos de Música",
        value=(
            "`/play <título>` - Reproduce música\n"
            "`/leave` - Desconecta al bot"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Pedido por {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

# ------------------------------------------
# Eventos
# ------------------------------------------

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/help"))

# Iniciar bot
bot.run(os.getenv("DISCORD_TOKEN"))
