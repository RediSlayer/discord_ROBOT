import discord
from discord.ext import commands
import requests
import random
import key  # Importamos el archivo key.py con el token
import os  # Importar os para acceder a las variables de entorno
import yt_dlp

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

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')

@bot.command()
async def play(ctx, *, titulo: str):
    """Reproduce audio de YouTube"""
    if not ctx.author.voice:
        return await ctx.send("🔇 Debes estar en un canal de voz")

    channel = ctx.author.voice.channel
    vc = await channel.connect() if not ctx.voice_client else ctx.voice_client

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "default_search": "ytsearch",
        "extract_flat": "in_playlist"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(titulo, download=False)
        if "entries" in info:
            info = info["entries"][0]

    url = info["url"]
    title = info.get('title', 'Unknown Title')
    thumbnail = info.get('thumbnail', '')

    # Utiliza FFmpegPCMAudio para reproducir el audio
    source = discord.FFmpegPCMAudio(url)
    vc.play(discord.PCMVolumeTransformer(source))

    embed = discord.Embed(title="🎵 Reproduciendo", description=f"{title}", color=0x1DB954)
    embed.set_thumbnail(url=thumbnail)
    await ctx.send(embed=embed)

@bot.command()
async def leave(ctx):
    """Desconecta al bot de voz"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🔇 Desconectado del canal de voz")
    else:
        await ctx.send("🤖 No estoy en ningún canal de voz")

@bot.command()
async def randomanime(ctx, genero: str = None):
    try:
        response = requests.get("https://api.jikan.moe/v4/top/anime?limit=25")
        data = response.json()
        animes = data['data']

        if genero:
            genero = genero.lower()
            filtrados = [a for a in animes if any(g['name'].lower() == genero for g in a['genres'])]
            anime = random.choice(filtrados) if filtrados else random.choice(animes)
        else:
            anime = random.choice(animes)

        embed = discord.Embed(
            title=anime['title'],
            url=anime['url'],
            description=anime.get('synopsis', 'Sin sinopsis')[:400] + "...",
            color=0x00ff00
        )
        embed.add_field(name="⭐ Puntuación", value=anime.get('score', 'N/A'))
        embed.add_field(name="📺 Episodios", value=anime.get('episodes', '?'))
        embed.set_image(url=anime['images']['jpg']['large_image_url'])
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send("🔴 Error al buscar anime aleatorio.")
        print(f"Error: {e}")

@bot.command()
async def msj(ctx, *, msj: str):
    await ctx.message.delete()
    await ctx.send(msj)

@bot.command()
async def buscaranime(ctx, *, name):
    """Busca información detallada de un anime"""
    try:
        response = requests.get(f"https://api.jikan.moe/v4/anime?q={name}&limit=1")

        if response.status_code == 200 and response.json()["data"]:
            anime = response.json()["data"][0]

            # Crear un embed visualmente atractivo
            embed = discord.Embed(
                title=anime["title"],
                url=anime["url"],
                description=anime.get("synopsis", "Descripción no disponible")[:400] + "...",
                color=0x3498db
            )
            embed.set_thumbnail(url=anime["images"]["jpg"]["image_url"])

            # Añadir campos importantes
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

            # Verificar si el anime ya está en la lista
            if any(a["title"] == anime["title"] for a in anime_list):
                await ctx.send(f"❌ {anime['title']} ya está en tu lista!")
                return

            # Guardar datos relevantes
            anime_data = {
                "title": anime["title"],
                "year": anime.get("year", "Desconocido"),
                "score": anime.get("score", "Sin puntuación"),
                "url": anime["url"],
                "image": anime["images"]["jpg"]["image_url"],
                "added_by": ctx.author.name
            }

            anime_list.append(anime_data)

            # Mensaje de confirmación con embed
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
async def perfil(ctx, usuario: discord.Member = None):
    """Muestra el perfil de un usuario"""
    usuario = usuario or ctx.author
    embed = discord.Embed(
        title=f"🖼️ Avatar de {usuario.display_name}",
        color=discord.Color.blue()
    )
    embed.set_image(url=usuario.display_avatar.url)
    embed.set_footer(text=f"🆔 ID: {usuario.id} | 📅 Se unió el {usuario.joined_at.strftime('%d/%m/%Y')}")
    await ctx.send(embed=embed)

@bot.command()
async def ship(ctx, usuario1: discord.Member, usuario2: discord.Member):
    """Calcula la compatibilidad entre dos usuarios"""
    porcentaje = random.randint(0, 100)
    embed = discord.Embed(
        title="💖 Compatibilidad 💖",
        description=f"La compatibilidad entre {usuario1.mention} y {usuario2.mention} es de {porcentaje}%",
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)

@bot.command()
async def osu(ctx, *, username):
    """Busca información del perfil de osu! de un usuario"""
    osu_api_key = os.getenv("OSU_API_KEY")
    if not osu_api_key:
        await ctx.send("🔴 La API key de osu! no está configurada.")
        return

    try:
        response = requests.get(f"https://osu.ppy.sh/api/get_user?k={osu_api_key}&u={username}")

        if response.status_code == 200 and response.json():
            user = response.json()[0]

            # Crear un embed visualmente atractivo
            embed = discord.Embed(
                title=f"Perfil de osu! de {user['username']}",
                url=f"https://osu.ppy.sh/users/{user['user_id']}",
                color=0xff66aa
            )
            embed.set_thumbnail(url=f"https://a.ppy.sh/{user['user_id']}")

            # Añadir campos importantes
            info_fields = [
                ("🎮 Username", user['username'], True),
                ("🏆 PP Rank", user['pp_rank'], True),
                ("✨ Level", user['level'], True),
                ("🔹 Accuracy", f"{float(user['accuracy']):.2f}%", True),
                ("🕹️ Playcount", user['playcount'], True),
                ("💯 Total Score", user['total_score'], True)
            ]

            for name, value, inline in info_fields:
                embed.add_field(name=name, value=value, inline=inline)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"⚠ No se encontró el perfil de osu! para el usuario: {username}")
    except Exception as e:
        await ctx.send("🔴 Error al buscar el perfil de osu!. Intenta nuevamente.")
        print(f"Error en osu: {e}")

@bot.command()
async def ayuda(ctx):
    """Muestra todos los comandos disponibles"""
    embed = discord.Embed(
        title="🎌 **Ayuda del Bot**",
        description="Lista de comandos disponibles:",
        color=0x2b2d31
    )
    embed.add_field(
        name="🔍 **Búsqueda**",
        value=(
            "`/buscaranime <nombre>` - Busca información de un anime\n"
            "`/añadir <nombre>` - Añade un anime a tu lista\n"
            "`/lista` - Muestra tu lista de animes\n"
            "`/randomanime <genero>` - Elige un anime aleatorio"
        ),
        inline=False
    )

    embed.add_field(
        name="👥 **Social**",
        value=(
            "`/ship <usuario1> <usuario2>` - Calcula la compatibilidad entre dos usuarios\n"
            "`/perfil <usuario>` - Muestra el perfil de un usuario\n"
            "`/msj <mensage>` - Te copio tu mensaje\n"
            "`/osu <username>` - Busca información del perfil de osu!"
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