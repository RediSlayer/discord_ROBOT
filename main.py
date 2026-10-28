"""Bot de Discord: anime, perfiles, osu! y utilidades."""

import os
from pathlib import Path
import random
from typing import Any, Optional

import aiohttp
import discord
from discord.ext import commands

try:
    import key  # Archivo local key.py con DISCORD_TOKEN
except ImportError:
    key = None


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
COMMAND_PREFIX = "/"
BASE_DIR = Path(__file__).resolve().parent
SHIP_IMAGE_PATH = BASE_DIR / "ship.png"
SHIP_IMAGE_NAME = "ship.png"

JIKAN_API_URL = "https://api.jikan.moe/v4"
OSU_API_URL = "https://osu.ppy.sh/api/get_user"
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=15)

SYNOPSIS_MAX_LENGTH = 400
MAX_EMBED_FIELDS = 25

COLOR_RANDOM = 0x00FF00
COLOR_SEARCH = 0x3498DB
COLOR_SUCCESS = 0x2ECC71
COLOR_ERROR = 0xE74C3C
COLOR_PICK = 0xE91E63
COLOR_LIST = 0xF39C12
COLOR_PROFILE = 0x3498DB
COLOR_SHIP = 0xEB459F
COLOR_OSU = 0xFF66AA
COLOR_HELP = 0x2B2D31


# ---------------------------------------------------------------------------
# Excepciones y utilidades
# ---------------------------------------------------------------------------
class APIError(Exception):
    """Error al consultar una API externa."""


def get_token() -> str:
    """Obtiene el token desde la variable de entorno o desde key.py."""
    token = os.getenv("DISCORD_TOKEN") or getattr(key, "DISCORD_TOKEN", None)
    if not token:
        raise RuntimeError(
            "No se encontró el token. Define DISCORD_TOKEN como variable de "
            "entorno o en key.py."
        )
    return token


def fmt(value: Any, default: str = "Desconocido") -> str:
    """Convierte un valor a texto, usando un valor por defecto si es None."""
    return str(value) if value is not None else default


def truncate(text: Optional[str], default: str, limit: int = SYNOPSIS_MAX_LENGTH) -> str:
    """Recorta un texto largo para que quepa en un embed."""
    if not text:
        return default
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def build_embed(
    title: str,
    description: Optional[str] = None,
    color: int = COLOR_SEARCH,
    url: Optional[str] = None,
) -> discord.Embed:
    """Crea un embed con el estilo base del bot."""
    return discord.Embed(
        title=title,
        description=description,
        color=color,
        url=url,
    )


def add_fields(
    embed: discord.Embed,
    fields: list[tuple[str, Any, bool]],
) -> None:
    """Añade varios campos (nombre, valor, inline) a un embed."""
    for field_name, field_value, inline in fields:
        embed.add_field(name=field_name, value=fmt(field_value), inline=inline)


async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: Optional[dict[str, Any]] = None,
) -> Any:
    """Realiza una petición GET y devuelve el JSON, o lanza APIError."""
    try:
        async with session.get(url, params=params) as response:
            if response.status == 429:
                raise APIError("Demasiadas peticiones, inténtalo en unos segundos.")
            if response.status != 200:
                raise APIError(f"La API respondió con el código {response.status}.")
            return await response.json(content_type=None)
    except aiohttp.ClientError as error:
        raise APIError(f"Error de conexión: {error}") from error
    except TimeoutError as error:
        raise APIError("La API tardó demasiado en responder.") from error
    except ValueError as error:
        raise APIError("La API devolvió una respuesta inválida.") from error


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------
class AnimeBot(commands.Bot):
    """Bot con sesión HTTP compartida."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="¿Tienes dudas? Usa /ayuda",
            ),
        )
        self.session: Optional[aiohttp.ClientSession] = None

    async def setup_hook(self) -> None:
        """Se ejecuta antes de conectar: crea la sesión HTTP."""
        self.session = aiohttp.ClientSession(timeout=HTTP_TIMEOUT)

    async def close(self) -> None:
        """Cierra la sesión HTTP antes de apagar el bot."""
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()

    async def on_ready(self) -> None:
        print(f"✅ Bot conectado como {self.user}")

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Gestiona los errores comunes de los comandos."""
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠ Falta un argumento: `{error.param.name}`. Usa `/ayuda`.")
        elif isinstance(error, (commands.BadArgument, commands.MemberNotFound)):
            await ctx.send("⚠ Argumento inválido. Usa `/ayuda` para ver el formato.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 No tienes permisos para usar este comando.")
        else:
            print(f"Error en el comando '{ctx.command}': {error}")
            await ctx.send("🔴 Ocurrió un error inesperado.")


bot = AnimeBot()

# Lista de animes (persistente mientras el bot esté activo)
anime_list: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Funciones auxiliares de anime
# ---------------------------------------------------------------------------
async def search_anime(name: str) -> Optional[dict[str, Any]]:
    """Busca un anime por nombre en Jikan. Devuelve None si no hay resultados."""
    data = await fetch_json(
        bot.session,
        f"{JIKAN_API_URL}/anime",
        params={"q": name, "limit": 1},
    )
    results = data.get("data") if isinstance(data, dict) else None
    return results[0] if results else None


def anime_image(anime: dict[str, Any], key_name: str = "image_url") -> Optional[str]:
    """Obtiene la URL de la imagen JPG de un anime, si existe."""
    return anime.get("images", {}).get("jpg", {}).get(key_name)


# ---------------------------------------------------------------------------
# Comandos: anime
# ---------------------------------------------------------------------------
@bot.command()
async def randomanime(ctx: commands.Context, genero: Optional[str] = None) -> None:
    """Muestra un anime aleatorio del top, opcionalmente filtrado por género."""
    try:
        data = await fetch_json(
            bot.session,
            f"{JIKAN_API_URL}/top/anime",
            params={"limit": 25},
        )
        animes = data.get("data", [])
        if not animes:
            await ctx.send("⚠ No se pudieron obtener animes en este momento.")
            return

        pool = animes
        if genero:
            genero = genero.lower()
            filtrados = [
                a for a in animes
                if any(g["name"].lower() == genero for g in a.get("genres", []))
            ]
            pool = filtrados or animes

        anime = random.choice(pool)

        embed = build_embed(
            title=anime["title"],
            description=truncate(anime.get("synopsis"), "Sin sinopsis"),
            color=COLOR_RANDOM,
            url=anime.get("url"),
        )
        add_fields(embed, [
            ("⭐ Puntuación", fmt(anime.get("score"), "N/A"), True),
            ("📺 Episodios", fmt(anime.get("episodes"), "?"), True),
        ])
        image = anime_image(anime, "large_image_url")
        if image:
            embed.set_image(url=image)

        await ctx.send(embed=embed)
    except APIError as error:
        await ctx.send(f"🔴 Error al buscar anime aleatorio: {error}")
    except (KeyError, IndexError, TypeError) as error:
        print(f"Error en randomanime: {error}")
        await ctx.send("🔴 Error al procesar los datos del anime.")


@bot.command()
async def buscaranime(ctx: commands.Context, *, name: str) -> None:
    """Busca información detallada de un anime."""
    try:
        anime = await search_anime(name)
        if not anime:
            await ctx.send(f"⚠ No se encontró el anime: {name}")
            return

        embed = build_embed(
            title=anime["title"],
            description=truncate(anime.get("synopsis"), "Descripción no disponible"),
            color=COLOR_SEARCH,
            url=anime.get("url"),
        )
        image = anime_image(anime)
        if image:
            embed.set_thumbnail(url=image)

        add_fields(embed, [
            ("📆 Año", fmt(anime.get("year")), True),
            ("⭐ Puntuación", fmt(anime.get("score"), "Sin puntuación"), True),
            ("📺 Episodios", fmt(anime.get("episodes")), True),
            ("📌 Estado", fmt(anime.get("status")), True),
            ("🌀 Tipo", fmt(anime.get("type")), True),
            ("⏱ Duración", fmt(anime.get("duration")), True),
        ])

        await ctx.send(embed=embed)
    except APIError as error:
        await ctx.send(f"🔴 Error al buscar el anime: {error}")
    except (KeyError, IndexError, TypeError) as error:
        print(f"Error en buscaranime: {error}")
        await ctx.send("🔴 Error al procesar los datos del anime.")


@bot.command(name="añadir")
async def anadir(ctx: commands.Context, *, name: str) -> None:
    """Añade un anime a la lista personal."""
    try:
        anime = await search_anime(name)
        if not anime:
            await ctx.send(f"⚠ No se pudo encontrar: {name}")
            return

        if any(item["title"] == anime["title"] for item in anime_list):
            await ctx.send(f"❌ {anime['title']} ya está en tu lista!")
            return

        anime_data = {
            "title": anime["title"],
            "year": fmt(anime.get("year")),
            "score": fmt(anime.get("score"), "Sin puntuación"),
            "url": anime.get("url"),
            "image": anime_image(anime),
            "added_by": ctx.author.name,
        }
        anime_list.append(anime_data)

        embed = build_embed(
            title=f"✅ {anime_data['title']} añadido!",
            description=f"Añadido por: {ctx.author.mention}",
            color=COLOR_SUCCESS,
        )
        if anime_data["image"]:
            embed.set_thumbnail(url=anime_data["image"])
        add_fields(embed, [
            ("⭐ Puntuación", anime_data["score"], True),
            ("📆 Año", anime_data["year"], True),
        ])

        await ctx.send(embed=embed)
    except APIError as error:
        await ctx.send(f"🔴 Error al añadir el anime: {error}")
    except (KeyError, IndexError, TypeError) as error:
        print(f"Error en añadir: {error}")
        await ctx.send("🔴 Error al procesar los datos del anime.")


@bot.command()
async def elegir(ctx: commands.Context) -> None:
    """Elige un anime aleatorio de la lista."""
    if not anime_list:
        await ctx.send("📭 Tu lista está vacía. Usa `/añadir` para agregar animes!")
        return

    anime = random.choice(anime_list)

    embed = build_embed(
        title=f"🎲 Anime seleccionado: {anime['title']}",
        color=COLOR_PICK,
        url=anime.get("url"),
    )
    if anime.get("image"):
        embed.set_thumbnail(url=anime["image"])
    add_fields(embed, [
        ("⭐ Puntuación", anime["score"], True),
        ("📆 Año", anime["year"], True),
    ])
    embed.set_footer(text=f"Añadido por: {anime.get('added_by', 'Desconocido')}")

    await ctx.send(embed=embed)


@bot.command()
async def lista(ctx: commands.Context) -> None:
    """Muestra todos los animes de la lista."""
    if not anime_list:
        await ctx.send("📭 Tu lista de animes está vacía.")
        return

    embed = build_embed(
        title=f"📚 Tu lista de animes ({len(anime_list)})",
        color=COLOR_LIST,
    )

    for index, anime in enumerate(anime_list[:MAX_EMBED_FIELDS], start=1):
        embed.add_field(
            name=f"{index}. {anime['title']}",
            value=(
                f"⭐ {anime['score']} | 📆 {anime['year']} | "
                f"👤 {anime.get('added_by', 'Desconocido')}"
            ),
            inline=False,
        )

    if len(anime_list) > MAX_EMBED_FIELDS:
        embed.set_footer(
            text=f"Mostrando {MAX_EMBED_FIELDS} de {len(anime_list)} animes"
        )

    await ctx.send(embed=embed)


@bot.command()
async def eliminar(ctx: commands.Context, index: int) -> None:
    """Elimina un anime de la lista por su número."""
    if not anime_list:
        await ctx.send("📭 Tu lista está vacía!")
        return

    if not 1 <= index <= len(anime_list):
        await ctx.send(f"⚠ Ingresa un número entre 1 y {len(anime_list)}")
        return

    removed = anime_list.pop(index - 1)

    embed = build_embed(title=f"❌ {removed['title']} eliminado", color=COLOR_ERROR)
    if removed.get("image"):
        embed.set_thumbnail(url=removed["image"])
    add_fields(embed, [
        ("Puntuación", removed["score"], True),
        ("Año", removed["year"], True),
    ])

    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def limpiar(ctx: commands.Context) -> None:
    """Elimina todos los animes de la lista (solo administradores)."""
    if not anime_list:
        await ctx.send("📭 La lista ya está vacía!")
        return

    anime_list.clear()
    await ctx.send("🧹 ¡Lista limpiada correctamente!")


# ---------------------------------------------------------------------------
# Comandos: social y utilidades
# ---------------------------------------------------------------------------
@bot.command()
async def perfil(ctx: commands.Context, usuario: Optional[discord.Member] = None) -> None:
    """Muestra el avatar y datos de un usuario."""
    usuario = usuario or ctx.author

    embed = build_embed(
        title=f"🖼️ Avatar de {usuario.display_name}",
        color=COLOR_PROFILE,
    )
    embed.set_image(url=usuario.display_avatar.url)

    joined = (
        usuario.joined_at.strftime("%d/%m/%Y") if usuario.joined_at else "Desconocido"
    )
    embed.set_footer(text=f"🆔 ID: {usuario.id} | 📅 Se unió el {joined}")

    await ctx.send(embed=embed)


@bot.command()
async def ship(
    ctx: commands.Context,
    usuario1: discord.Member,
    usuario2: discord.Member,
) -> None:
    """Calcula la compatibilidad entre dos usuarios."""
    porcentaje = random.randint(0, 100)

    embed = build_embed(
        title="💖 Compatibilidad 💖",
        description=(
            f"La compatibilidad entre {usuario1.mention} y {usuario2.mention} "
            f"es de **{porcentaje}%**"
        ),
        color=COLOR_SHIP,
    )

    # Si la imagen no existe, se envía igualmente el porcentaje
    image_file: Optional[discord.File] = None
    if SHIP_IMAGE_PATH.is_file():
        image_file = discord.File(SHIP_IMAGE_PATH, filename=SHIP_IMAGE_NAME)
        embed.set_image(url=f"attachment://{SHIP_IMAGE_NAME}")

    try:
        if image_file:
            await ctx.send(embed=embed, file=image_file)
        else:
            await ctx.send(embed=embed)
    except OSError as error:
        print(f"Error al enviar la imagen de ship: {error}")
        embed.set_image(url=None)
        await ctx.send(embed=embed)


@bot.command()
async def osu(ctx: commands.Context, *, username: str) -> None:
    """Busca información del perfil de osu! de un usuario."""
    osu_api_key = os.getenv("OSU_API_KEY")
    if not osu_api_key:
        await ctx.send("🔴 La API key de osu! no está configurada.")
        return

    try:
        data = await fetch_json(
            bot.session,
            OSU_API_URL,
            params={"k": osu_api_key, "u": username},
        )
        if not data:
            await ctx.send(f"⚠ No se encontró el perfil de osu! para el usuario: {username}")
            return

        user = data[0]

        embed = build_embed(
            title=f"Perfil de osu! de {user['username']}",
            color=COLOR_OSU,
            url=f"https://osu.ppy.sh/users/{user['user_id']}",
        )
        embed.set_thumbnail(url=f"https://a.ppy.sh/{user['user_id']}")

        accuracy = user.get("accuracy")
        accuracy_text = f"{float(accuracy):.2f}%" if accuracy is not None else "N/A"

        add_fields(embed, [
            ("🎮 Username", user["username"], True),
            ("🏆 PP Rank", fmt(user.get("pp_rank"), "N/A"), True),
            ("✨ Level", fmt(user.get("level"), "N/A"), True),
            ("🔹 Accuracy", accuracy_text, True),
            ("🕹️ Playcount", fmt(user.get("playcount"), "N/A"), True),
            ("💯 Total Score", fmt(user.get("total_score"), "N/A"), True),
        ])

        await ctx.send(embed=embed)
    except APIError as error:
        await ctx.send(f"🔴 Error al buscar el perfil de osu!: {error}")
    except (KeyError, IndexError, TypeError, ValueError) as error:
        print(f"Error en osu: {error}")
        await ctx.send("🔴 Error al procesar los datos del perfil de osu!.")


@bot.command()
async def msj(ctx: commands.Context, *, mensaje: str) -> None:
    """Repite el mensaje del usuario y borra el original."""
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass  # Sin permiso para borrar o el mensaje ya no existe

    await ctx.send(mensaje, allowed_mentions=discord.AllowedMentions.none())


@bot.command()
async def ayuda(ctx: commands.Context) -> None:
    """Muestra todos los comandos disponibles."""
    embed = build_embed(
        title="🎌 Ayuda del Bot",
        description="Lista de comandos disponibles:",
        color=COLOR_HELP,
    )

    embed.add_field(
        name="🔍 Anime",
        value=(
            "`/buscaranime <nombre>` - Busca información de un anime\n"
            "`/randomanime <género>` - Elige un anime aleatorio\n"
            "`/añadir <nombre>` - Añade un anime a tu lista\n"
            "`/lista` - Muestra tu lista de animes\n"
            "`/elegir` - Elige un anime aleatorio de tu lista\n"
            "`/eliminar <número>` - Elimina un anime de la lista"
        ),
        inline=False,
    )
    embed.add_field(
        name="👥 Social",
        value=(
            "`/ship <usuario1> <usuario2>` - Calcula la compatibilidad entre dos usuarios\n"
            "`/perfil <usuario>` - Muestra el perfil de un usuario\n"
            "`/msj <mensaje>` - Repite tu mensaje\n"
            "`/osu <username>` - Busca información del perfil de osu!"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚙️ Moderación (solo administradores)",
        value="`/limpiar` - Vacía toda la lista de animes",
        inline=False,
    )

    embed.set_footer(
        text=f"Pedido por {ctx.author.name}",
        icon_url=ctx.author.display_avatar.url,
    )

    await ctx.send(embed=embed)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    bot.run(get_token())
