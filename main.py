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
    help_command=None
)

# Lista para almacenar animes
anime_list = []

async def generar_imagen_ship(usuario1, usuario2, porcentaje):
    """Genera imagen para el comando ship usando ship.png"""
    try:
        # Cargar imagen base
        with open('ship.png', 'rb') as f:
            img = Image.open(BytesIO(f.read())).convert('RGBA')
        
        draw = ImageDraw.Draw(img)
        
        # Procesar avatares
        def procesar_avatar(url):
            response = requests.get(url, timeout=5)
            avatar = Image.open(BytesIO(response.content)).convert('RGBA')
            avatar = ImageOps.fit(avatar, (120, 120), method=Image.LANCZOS)
            mask = Image.new('L', (120, 120), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 120, 120), fill=255)
            return avatar, mask

        avatar1, mask1 = procesar_avatar(usuario1.display_avatar.url)
        avatar2, mask2 = procesar_avatar(usuario2.display_avatar.url)
        
        # Posicionar avatares
        img.paste(avatar1, (100, 80), mask1)
        img.paste(avatar2, (280, 80), mask2)
        
        # Dibujar porcentaje
        font = ImageFont.truetype("arial.ttf", 36) if hasattr(ImageFont, "truetype") else ImageFont.load_default()
        draw.text((250, 170), f"{porcentaje}%", font=font, fill="white", anchor="mm")
        
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
    if usuario1 == usuario2:
        await ctx.send("¡No puedes shipearte contigo mismo! 😅")
        return
    
    porcentaje = random.randint(0, 100)
    imagen = await generar_imagen_ship(usuario1, usuario2, porcentaje)
    
    if imagen:
        await ctx.send(file=discord.File(imagen, filename="ship_result.png"))
    else:
        await ctx.send(f"💞 Compatibilidad: {porcentaje}%")

@bot.command()
async def perfil(ctx, usuario: discord.Member = None):
    """Muestra el perfil de un usuario"""
    usuario = usuario or ctx.author
    embed = discord.Embed(color=discord.Color.blue())
    embed.set_image(url=usuario.display_avatar.url)
    await ctx.send(embed=embed)

# Comandos de anime
@bot.command()
async def buscaranime(ctx, *, name):
    try:
        response = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1")
        if response.status_code == 200 and response.json()["data"]:
            anime = response.json()["data"][0]
            embed = discord.Embed(
                title=anime["title"],
                url=anime["url"],
                color=0x3498db
            )
            embed.set_thumbnail(url=anime["images"]["jpg"]["image_url"])
            embed.add_field(name="⭐ Puntuación", value=anime.get("score", "N/A"), inline=True)
            embed.add_field(name="📆 Año", value=anime.get("year", "N/A"), inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No se encontró: {name}")
    except Exception as e:
        await ctx.send("Error al buscar anime")
        print(f"Error: {e}")

@bot.command()
async def añadir(ctx, *, name):
    try:
        response = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1")
        if response.status_code == 200 and response.json()["data"]:
            anime = response.json()["data"][0]
            anime_data = {
                "title": anime["title"],
                "score": anime.get("score", "N/A"),
                "image": anime["images"]["jpg"]["image_url"],
                "added_by": ctx.author.name
            }
            anime_list.append(anime_data)
            await ctx.send(f"✅ {anime_data['title']} añadido")
        else:
            await ctx.send(f"No se encontró: {name}")
    except Exception as e:
        await ctx.send("Error al añadir anime")
        print(f"Error: {e}")

@bot.command()
async def lista(ctx):
    if not anime_list:
        await ctx.send("La lista está vacía")
        return
    
    embed = discord.Embed(title="Tu lista de animes")
    for i, anime in enumerate(anime_list, 1):
        embed.add_field(
            name=f"{i}. {anime['title']}",
            value=f"⭐ {anime['score']} | Añadido por: {anime.get('added_by', 'N/A')}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def limpiar(ctx):
    """Limpia toda la lista de animes (Solo admins)"""
    anime_list.clear()
    await ctx.send("🧹 Lista de animes limpiada completamente")

@bot.command()
async def eliminar(ctx, index: int):
    """Elimina un anime de la lista"""
    if not anime_list:
        await ctx.send("La lista está vacía")
        return
    
    if 1 <= index <= len(anime_list):
        removed = anime_list.pop(index-1)
        await ctx.send(f"❌ {removed['title']} eliminado")
    else:
        await ctx.send("Índice inválido")

@bot.command()
async def ayuda(ctx):
    """Muestra los comandos disponibles"""
    embed = discord.Embed(
        title="Comandos disponibles",
        description="Prefijo: `/`",
        color=0x5865F2
    )
    
    embed.add_field(
        name="🔍 Anime",
        value=(
            "`/buscaranime <nombre>` - Busca un anime\n"
            "`/añadir <nombre>` - Añade a tu lista\n"
            "`/lista` - Muestra tu lista\n"
            "`/eliminar <número>` - Elimina un anime"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💘 Social",
        value=(
            "`/ship @usuario1 @usuario2` - Calcula compatibilidad\n"
            "`/perfil [@usuario]` - Muestra perfil"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Admin",
        value="`/limpiar` - Vacía toda la lista",
        inline=False
    )
    
    await ctx.send(embed=embed)

bot.run(key.DISCORD_TOKEN)
