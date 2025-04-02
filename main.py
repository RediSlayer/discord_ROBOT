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
bot = commands.Bot(command_prefix="/", intents=intents)

# Lista para almacenar animes
anime_list = []

# URL de fondo para el shipómetro
SHIP_BACKGROUND = "https://i.imgur.com/W9qVd7R.png"  # Imagen mejorada para el fondo

async def generar_imagen_ship(usuario1, usuario2, porcentaje):
    """Genera una imagen atractiva para el shipómetro"""
    try:
        # Descargar recursos
        fondo = Image.open(BytesIO(requests.get(SHIP_BACKGROUND).content)).convert("RGBA")
        avatar1 = Image.open(BytesIO(requests.get(usuario1.avatar.url).content)).convert("RGBA")
        avatar2 = Image.open(BytesIO(requests.get(usuario2.avatar.url).content)).convert("RGBA")
        
        # Redimensionar
        fondo = fondo.resize((600, 300))
        avatar1 = avatar1.resize((120, 120))
        avatar2 = avatar2.resize((120, 120))
        
        # Crear máscara circular para avatares
        mask = Image.new("L", (120, 120), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 120, 120), fill=255)
        
        # Pegar elementos
        fondo.paste(avatar1, (90, 90), mask)
        fondo.paste(avatar2, (390, 90), mask)
        
        # Dibujar texto
        draw = ImageDraw.Draw(fondo)
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
        
        # Texto central con porcentaje
        draw.text((300, 30), f"{porcentaje}%", fill=(255, 105, 180), font=font, anchor="mm")
        
        # Nombres de usuarios
        draw.text((150, 220), usuario1.name[:12], fill="white", font=font, anchor="mm")
        draw.text((450, 220), usuario2.name[:12], fill="white", font=font, anchor="mm")
        
        # Barra de compatibilidad
        bar_width = int(400 * (porcentaje/100))
        draw.rectangle((100, 250, 100 + bar_width, 270), fill=(255, 105, 180))
        
        # Guardar imagen
        img_bytes = BytesIO()
        fondo.save(img_bytes, format="PNG")
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
        embed = discord.Embed(title="💘 Shipómetro", color=discord.Color.pink())
        embed.add_field(name="Compatibilidad", value=f"**{porcentaje}%**", inline=False)
        embed.set_image(url="attachment://ship.png")
        await ctx.send(embed=embed, file=discord.File(imagen, "ship.png"))
    else:
        await ctx.send(f"💞 {usuario1.mention} + {usuario2.mention} = {porcentaje}% de compatibilidad")

@bot.command()
async def perfil(ctx, usuario: discord.Member = None):
    """Muestra información de un usuario"""
    usuario = usuario or ctx.author
    
    embed = discord.Embed(
        title=f"👤 Perfil de {usuario.display_name}",
        color=usuario.color if usuario.color else discord.Color.blue()
    )
    
    embed.set_thumbnail(url=usuario.avatar.url)
    
    embed.add_field(name="🆔 ID", value=usuario.id, inline=True)
    embed.add_field(name="📅 Creación", value=usuario.created_at.strftime("%d/%m/%Y"), inline=True)
    
    if isinstance(usuario, discord.Member):
        embed.add_field(name="📌 Ingreso", value=usuario.joined_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🎭 Roles", value=len(usuario.roles)-1, inline=True)  # Resta 1 para omitir @everyone
        embed.add_field(name="🚀 Máximo rol", value=usuario.top_role.name, inline=True)
    
    embed.set_footer(text=f"Solicitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

# [Aquí van todos tus comandos originales de anime (buscaranime, añadir, elegir, etc.)]
# ... (mantén exactamente los mismos comandos que ya tenías)

@bot.command()
async def ayuda(ctx):
    """Muestra todos los comandos disponibles"""
    embed = discord.Embed(
        title="🎌 **Ayuda del Bot**",
        description="Todos los comandos disponibles:",
        color=0x5865F2
    )
    
    embed.add_field(
        name="💘 Social",
        value=(
            "`/ship @usuario1 @usuario2` - Calcula compatibilidad\n"
            "`/perfil [@usuario]` - Muestra información"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔍 Anime",
        value=(
            "`/buscaranime <nombre>` - Busca información\n"
            "`/añadir <nombre>` - Añade a tu lista\n"
            "`/lista` - Muestra tu lista\n"
            "`/elegir` - Anime aleatorio"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Moderación",
        value=(
            "`/eliminar <número>` - Elimina anime\n"
            "`/limpiar` - Vacía la lista (admin)"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Pedido por {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

bot.run(key.DISCORD_TOKEN)
