#!/bin/bash

echo "🛑 Stopping Content Creator..."

# Остановка процессов
pkill -f "python main.py"
pkill -f "vite"

# Остановка Docker
docker-compose down

echo "✅ Content Creator остановлен"

