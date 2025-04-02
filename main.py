import discord
from discord.ext import commands
import requests
import random
import key
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    activity=discord.Activity(type=discord.ActivityType.watching, name="Si tienes dudas /ayuda")
)

# Lista para almacenar animes
anime_list = []

async def generar_imagen_ship(usuario1, usuario2, porcentaje):
    """Genera una imagen simple para el ship con corazones"""
    try:
        # Tamaño de la imagen final
        img_width = 400
        img_height = 200
        
        # Crear imagen base
        img = Image.new('RGB', (img_width, img_height), color=(47, 49, 54))
        draw = ImageDraw.Draw(img)
        
        # Descargar avatares (CORRECCIÓN AQUÍ)
        avatar1_bytes = BytesIO(requests.get(usuario1.avatar.url).content)
        avatar1 = Image.open(avatar1_bytes).resize((80, 80))
        
        avatar2_bytes = BytesIO(requests.get(usuario2.avatar.url).content)
        avatar2 = Image.open(avatar2_bytes).resize((80, 80))
        
        # Pegar avatares
        img.paste(avatar1, (80, 50))
        img.paste(avatar2, (240, 50))
        
        # Dibujar corazón
        draw.text((200, 60), "❤️", font=ImageFont.load_default(size=30))
        
        # Barra de porcentaje
        bar_width = int(300 * (porcentaje/100))
        draw.rectangle((50, 150, 50 + bar_width, 160), fill=(255, 105, 180))
        draw.rectangle((50, 150, 350, 160), outline=(255, 255, 255))
        
        # Texto de porcentaje
        draw.text((200, 165), f"{porcentaje}%", fill=(255, 255, 255))
        
        # Guardar imagen
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
        
    except Exception as e:
        print(f"Error generando imagen: {e}")
        return None

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')

@bot.command()
async def ship(ctx, usuario1: discord.Member, usuario2: discord.Member):
    """Calcula la compatibilidad entre dos usuarios"""
    porcentaje = random.randint(0, 100)
    imagen = await generar_imagen_ship(usuario1, usuario2, porcentaje)
    
    if imagen:
        file = discord.File(imagen, filename="ship.png")
        await ctx.send(file=file)
    else:
        await ctx.send(f"💞 Compatibilidad: {porcentaje}%")

@bot.command()
async def perfil(ctx, usuario: discord.Member = None):
    """Muestra el perfil de un usuario"""
    usuario = usuario or ctx.author
    
    embed = discord.Embed(color=discord.Color.blue())
    embed.set_author(name=usuario.name)
    embed.set_image(url=usuario.avatar.url)
    
    await ctx.send(embed=embed)

# [Tus comandos originales de anime aquí...]
# buscaranime, añadir, elegir, lista, eliminar, limpiar
# ...

@bot.command()
async def ayuda(ctx):
    """Muestra los comandos disponibles"""
    embed = discord.Embed(
        title="Comandos disponibles",
        description="Prefijo: `/`",
        color=0x5865F2
    )
    
    embed.add_field(
        name="💘 Social",
        value="`/ship @usuario1 @usuario2`\n`/perfil [@usuario]`",
        inline=False
    )
    
    embed.add_field(
        name="🔍 Anime",
        value="`/buscaranime <nombre>`\n`/añadir <nombre>`\n`/lista`\n`/elegir`",
        inline=False
    )
    
    await ctx.send(embed=embed)

bot.run(key.DISCORD_TOKEN)
