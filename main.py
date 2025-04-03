import discord
from discord.ext import commands
import key
import yt_dlp as youtube_dl
from discord import FFmpegPCMAudio

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

# Configuración mejorada para música
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def check_queue(self, ctx, id):
        if id in self.queues and len(self.queues[id]) > 0:
            voice = ctx.voice_client
            source = self.queues[id].pop(0)
            voice.play(source, after=lambda x=None: self.check_queue(ctx, id))
            
    @commands.command(name='unir')
    async def unir(self, ctx):
        """Une el bot al canal de voz"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = ctx.voice_client
            
            if voice_client and voice_client.is_connected():
                await voice_client.move_to(channel)
            else:
                voice_client = await channel.connect()
            
            await ctx.send(f"🎤 Conectado a {channel.name}")
        else:
            await ctx.send("🔇 Debes estar en un canal de voz para usar este comando!")

    @commands.command(name='play')
    async def play(self, ctx, *, query):
        """Reproduce música desde YouTube"""
        voice_client = ctx.voice_client
        
        if not voice_client:
            if ctx.author.voice:
                await ctx.invoke(self.unir)
                voice_client = ctx.voice_client
            else:
                return await ctx.send("🔇 Debes estar en un canal de voz para reproducir música!")
        
        try:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                if not info['entries']:
                    return await ctx.send("⚠️ No se encontraron resultados para tu búsqueda.")
                info = info['entries'][0]
                url = info['formats'][0]['url']
                title = info['title']
                
                source = FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
                
                if not voice_client.is_playing():
                    voice_client.play(source, after=lambda x=None: self.check_queue(ctx, ctx.guild.id))
                    await ctx.send(f"🎶 Reproduciendo: **{title}**")
                else:
                    if ctx.guild.id not in self.queues:
                        self.queues[ctx.guild.id] = []
                    self.queues[ctx.guild.id].append((source, title))
                    await ctx.send(f"🎵 Añadido a la cola: **{title}**")
                    
        except Exception as e:
            await ctx.send("🔴 Error al reproducir la canción. Intenta nuevamente.")
            print(f"Error en play: {e}")

    @commands.command(name='pausa')
    async def pausa(self, ctx):
        """Pausa la reproducción actual"""
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ Reproducción pausada")
        else:
            await ctx.send("🔇 No hay nada reproduciéndose")

    @commands.command(name='reanudar')
    async def reanudar(self, ctx):
        """Reanuda la reproducción"""
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Reproducción reanudada")
        else:
            await ctx.send("🔇 No hay nada pausado")

    @commands.command(name='saltar')
    async def saltar(self, ctx):
        """Salta la canción actual"""
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("⏭️ Canción saltada")
            self.check_queue(ctx, ctx.guild.id)
        else:
            await ctx.send("🔇 No hay nada reproduciéndose")

    @commands.command(name='cola')
    async def cola(self, ctx):
        """Muestra la cola de reproducción"""
        if ctx.guild.id in self.queues and len(self.queues[ctx.guild.id]) > 0:
            embed = discord.Embed(title="🎵 Cola de reproducción", color=0x3498db)
            for i, item in enumerate(self.queues[ctx.guild.id], 1):
                embed.add_field(name=f"{i}. {item[1]}", value="\u200b", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("📭 La cola está vacía")

    @commands.command(name='desconectar')
    async def desconectar(self, ctx):
        """Desconecta el bot del canal de voz"""
        voice_client = ctx.voice_client
        if voice_client:
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id].clear()
            await voice_client.disconnect()
            await ctx.send("✅ Desconectado del canal de voz")
        else:
            await ctx.send("🤖 No estoy conectado a ningún canal de voz")

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    await bot.add_cog(Music(bot))  # Añade el cog de música

# Iniciar el bot
bot.run(key.DISCORD_TOKEN)
