import discord
from discord.ext import commands
import requests
import random
import key
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    help_command=None,
    activity=discord.Activity(type=discord.ActivityType.watching, name="Escribe /ayuda")
)

# Lista para almacenar animes
anime_list = []

async def generar_imagen_ship(usuario1, usuario2, porcentaje):
    """Genera imagen para el comando ship con diseño mejorado"""
    try:
        # Crear imagen base
        img = Image.new('RGB', (500, 250), (54, 57, 63))
        draw = ImageDraw.Draw(img)
        
        # Procesar avatares con forma circular
        def procesar_avatar(url):
            response = requests.get(url, timeout=10)
            avatar = Image.open(BytesIO(response.content)).convert('RGBA')
            avatar = ImageOps.fit(avatar, (120, 120), method=Image.LANCZOS)
            
            # Crear máscara circular
            mask = Image.new('L', (120, 120), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, 120, 120), fill=255)
            
            return avatar, mask

        avatar1, mask1 = procesar_avatar(usuario1.display_avatar.url)
        avatar2, mask2 = procesar_avatar(usuario2.display_avatar.url)
        
        # Posiciones de los avatares
        img.paste(avatar1, (100, 80), mask1)
        img.paste(avatar2, (280, 80), mask2)
        
        # Dibujar corazón entre los avatares
        draw.text((250, 100), "❤️", font=ImageFont.load_default(size=40))
        
        # Barra de porcentaje
        bar_width = int(300 * (porcentaje/100))
        draw.rectangle((100, 200, 100 + bar_width, 210), fill=(255, 105, 180))
        draw.rectangle((100, 200, 400, 210), outline=(255, 255, 255), width=2)
        
        # Texto de porcentaje
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
        draw.text((250, 170), f"{porcentaje}%", font=font, fill=(255, 255, 255), anchor="mm")
        
        # Guardar imagen
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
        
    except Exception as e:
        print(f"Error generando imagen ship: {e}")
        return None

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="Escribe /ayuda"
    ))

@bot.command()
async def ship(ctx, usuario1: discord.Member, usuario2: discord.Member):
    """Calcula la compatibilidad entre dos usuarios 💘"""
    if usuario1 == usuario2:
        return await ctx.send("¡No puedes shipearte contigo mismo! 😅")
    
    porcentaje = random.randint(0, 100)
    imagen = await generar_imagen_ship(usuario1, usuario2, porcentaje)
    
    if imagen:
        embed = discord.Embed(
            title=f"💕 Compatibilidad: {porcentaje}%",
            description=f"{usuario1.mention} ❤️ {usuario2.mention}",
            color=0xff66b2
        )
        embed.set_image(url="attachment://ship.png")
        await ctx.send(embed=embed, file=discord.File(imagen, filename="ship.png"))
    else:
        await ctx.send(f"💞 {usuario1.display_name} + {usuario2.display_name} = {porcentaje}%")

@bot.command()
async def perfil(ctx, usuario: discord.Member = None):
    """Muestra el perfil de un usuario 👤"""
    usuario = usuario or ctx.author
    
    embed = discord.Embed(
        title=f"Perfil de {usuario.display_name}",
        color=usuario.color if usuario.color else discord.Color.blue()
    )
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

# [Tus comandos originales de anime aquí...]
# @bot.command()
# async def buscaranime...
# @bot.command()
# async def añadir...
# etc...

bot.run(key.DISCORD_TOKEN)
