#!/bin/bash

# Instala FFmpeg
apt-get update && apt-get install -y ffmpeg

# Ejecuta tu bot de Discord
python bot.py