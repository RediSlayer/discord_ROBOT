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
    help_command=None,
    activity=discord.Activity(name="Usa /ayuda")
)

# Lista para almacenar animes (persistente mientras el bot esté activo)
anime_list = []

async def generar_imagen_ship(usuario1, usuario2, porcentaje):
    """Genera imagen para el comando ship"""
    try:
        # Tamaño de la imagen
        img = Image.new('RGB', (400, 200), color=(54, 57, 63))
        draw = ImageDraw.Draw(img)
        
        # Descargar avatares
        avatar1 = Image.open(BytesIO(requests.get(usuario1.avatar.url).content).resize((80, 80))
        avatar2 = Image.open(BytesIO(requests.get(usuario2.avatar.url).content).resize((80, 80))
        
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
@bot.command()
async def buscaranime(ctx, *, name):
    """Busca información detallada de un anime"""
    try:
        response = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1")
        
        if response.status_code == 200 and response.json()["data"]:
            anime = response.json()["data"][0]
            
            embed = discord.Embed(
                title=anime["title"],
                url=anime["url"],
                description=anime.get("synopsis", "Descripción no disponible")[:400] + "...",
                color=0x3498db
            )
            embed.set_thumbnail(url=anime["images"]["jpg"]["image_url"])
            
            info_fields = [
                ("📆 Año", anime.get("year", "Desconocido"), True),
                ("⭐ Puntuación", anime.get("score", "Sin puntuación"), True),
                ("📺 Episodios", anime.get("episodes", "Desconocido"), True),
                ("📌 Estado", anime.get("status", "Desconocido"), True),
                ("🌀 Tipo", anime.get("type", "Desconocido"), True),
                ("⏱ Duración", anime.get("duration", "Desconocido"), True)
            ]
            
            for name, value, inline in info_fields:
                embed.add_field(name=name, value=value, inline=inline)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"⚠ No se encontró el anime: {name}")
    except Exception as e:
        await ctx.send("🔴 Error al buscar el anime. Intenta nuevamente.")
        print(f"Error en buscaranime: {e}")

@bot.command()
async def añadir(ctx, *, name):
    """Añade un anime a tu lista personal"""
    try:
        response = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1")
        
        if response.status_code == 200 and response.json()["data"]:
            anime = response.json()["data"][0]
            
            if any(a["title"] == anime["title"] for a in anime_list):
                await ctx.send(f"❌ {anime['title']} ya está en tu lista!")
                return
            
            anime_data = {
                "title": anime["title"],
                "year": anime.get("year", "Desconocido"),
                "score": anime.get("score", "Sin puntuación"),
                "url": anime["url"],
                "image": anime["images"]["jpg"]["image_url"],
                "added_by": ctx.author.name
            }
            
            anime_list.append(anime_data)
            
            embed = discord.Embed(
                title=f"✅ {anime_data['title']} añadido!",
                description=f"Añadido por: {ctx.author.mention}",
                color=0x2ecc71
            )
            embed.set_thumbnail(url=anime_data["image"])
            embed.add_field(name="⭐ Puntuación", value=anime_data["score"], inline=True)
            embed.add_field(name="📆 Año", value=anime_data["year"], inline=True)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"⚠ No se pudo encontrar: {name}")
    except Exception as e:
        await ctx.send("🔴 Error al añadir el anime. Intenta nuevamente.")
        print(f"Error en añadir: {e}")

@bot.command()
async def elegir(ctx):
    """Elige un anime aleatorio de tu lista"""
    if not anime_list:
        await ctx.send("📭 Tu lista está vacía. Usa `/añadir` para agregar animes!")
        return
    
    anime = random.choice(anime_list)
    
    embed = discord.Embed(
        title=f"🎲 Anime seleccionado: {anime['title']}",
        url=anime["url"],
        color=0xe91e63
    )
    embed.set_thumbnail(url=anime["image"])
    embed.add_field(name="⭐ Puntuación", value=anime["score"], inline=True)
    embed.add_field(name="📆 Año", value=anime["year"], inline=True)
    embed.set_footer(text=f"Añadido por: {anime.get('added_by', 'Desconocido')}")
    
    await ctx.send(embed=embed)

@bot.command()
async def lista(ctx):
    """Muestra todos los animes en tu lista"""
    if not anime_list:
        await ctx.send("📭 Tu lista de animes está vacía.")
        return
    
    embed = discord.Embed(
        title=f"📚 Tu lista de animes ({len(anime_list)})",
        color=0xf39c12
    )
    
    for i, anime in enumerate(anime_list, 1):
        embed.add_field(
            name=f"{i}. {anime['title']}",
            value=f"⭐ {anime['score']} | 📆 {anime['year']} | 👤 {anime.get('added_by', 'Desconocido')}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def eliminar(ctx, index: int):
    """Elimina un anime de tu lista por su número"""
    if not anime_list:
        await ctx.send("📭 Tu lista está vacía!")
        return
    
    if 1 <= index <= len(anime_list):
        removed = anime_list.pop(index-1)
        
        embed = discord.Embed(
            title=f"❌ {removed['title']} eliminado",
            color=0xe74c3c
        )
        embed.add_field(name="Puntuación", value=removed["score"], inline=True)
        embed.add_field(name="Año", value=removed["year"], inline=True)
        embed.set_thumbnail(url=removed["image"])
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠ Ingresa un número entre 1 y {len(anime_list)}")

@bot.command()
@commands.has_permissions(administrator=True)
async def limpiar(ctx):
    """Elimina todos los animes de tu lista"""
    if not anime_list:
        await ctx.send("📭 La lista ya está vacía!")
        return
    
    anime_list.clear()
    await ctx.send("🧹 ¡Lista limpiada correctamente!")

@bot.command()
async def ayuda(ctx):
    """Muestra todos los comandos disponibles"""
    embed = discord.Embed(
        title="🎌 **Ayuda del Bot de Anime**",
        description="Lista de comandos disponibles:\n(Prefijo: `/`)",
        color=0x2b2d31
    )
    
    embed.add_field(
        name="🔍 **Búsqueda**",
        value=(
            "`/buscaranime <nombre>` - Busca información de un anime\n"
            "`/añadir <nombre>` - Añade un anime a tu lista\n"
            "`/lista` - Muestra tu lista de animes\n"
            "`/elegir` - Elige un anime aleatorio"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💘 **Social**",
        value=(
            "`/ship @usuario1 @usuario2` - Calcula compatibilidad\n"
            "`/perfil [@usuario]` - Muestra perfil de usuario"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚙️ **Moderación** (Solo staff)",
        value=(
            "`/eliminar <número>` - Elimina un anime de la lista\n"
            "`/limpiar` - Vacía toda la lista"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Pedido por {ctx.author.name}", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

bot.run(key.DISCORD_TOKEN)
