import discord
from discord.ext import commands
import requests
import random
import key
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configuración inicial
intents = discord.Intents.default()
intents.message_content = True

# Variable para el prefijo (se puede cambiar dinámicamente)
BOT_PREFIX = "/"
bot = commands.Bot(
    command_prefix=BOT_PREFIX,
    intents=intents,
    help_command=None,  # Desactivamos el help integrado
    activity=discord.Activity(type=discord.ActivityType.watching, name="Usa /ayuda")
)

# Lista para almacenar animes
anime_list = []

async def generar_imagen_ship(usuario1, usuario2, porcentaje):
    """Genera imagen para el comando ship"""
    try:
        # Crear imagen base
        img = Image.new('RGB', (400, 200), color=(54, 57, 63))
        draw = ImageDraw.Draw(img)
        
        # Descargar y redimensionar avatares
        avatar1 = Image.open(BytesIO(requests.get(usuario1.avatar.url).content).resize((80, 80))
        avatar2 = Image.open(BytesIO(requests.get(usuario2.avatar.url).content).resize((80, 80))
        
        # Posicionar avatares
        img.paste(avatar1, (60, 50))
        img.paste(avatar2, (260, 50))
        
        # Dibujar corazón entre los avatares
        draw.text((190, 60), "❤️", font=ImageFont.load_default(size=30))
        
        # Barra de porcentaje
        bar_width = int(300 * (porcentaje/100))
        draw.rectangle((50, 150, 50 + bar_width, 160), fill=(255, 105, 180))
        draw.rectangle((50, 150, 350, 160), outline=(200, 200, 200))
        
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

@bot.command()
@commands.has_permissions(administrator=True)
async def prefix(ctx, nuevo_prefijo: str):
    """Cambia el prefijo del bot (Solo admins)"""
    global BOT_PREFIX
    BOT_PREFIX = nuevo_prefijo
    bot.command_prefix = BOT_PREFIX
    await ctx.send(f"✅ Prefijo cambiado a: `{nuevo_prefijo}`")

@bot.command()
async def ayuda(ctx):
    """Muestra todos los comandos disponibles"""
    embed = discord.Embed(
        title=f"📝 Comandos disponibles (Prefijo: `{BOT_PREFIX}`)",
        color=0x5865F2
    )
    
    embed.add_field(
        name="💘 Social",
        value=(
            f"`{BOT_PREFIX}ship @usuario1 @usuario2`\n"
            f"`{BOT_PREFIX}perfil [@usuario]`"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔍 Anime",
        value=(
            f"`{BOT_PREFIX}buscaranime <nombre>`\n"
            f"`{BOT_PREFIX}añadir <nombre>`\n"
            f"`{BOT_PREFIX}lista`\n"
            f"`{BOT_PREFIX}elegir`"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Admin",
        value=f"`{BOT_PREFIX}prefix <nuevo_prefijo>`",
        inline=False
    )
    
    await ctx.send(embed=embed)

# [Tus comandos originales de anime aquí...]
# buscaranime, añadir, elegir, lista, eliminar, limpiar
# ...

bot.run(key.DISCORD_TOKEN)
