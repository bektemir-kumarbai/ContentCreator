#!/bin/bash

echo "🚀 Starting Content Creator..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверка .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создайте его на основе ENV_TEMPLATE.txt"
    echo "   Пример: cp ENV_TEMPLATE.txt .env"
    echo "   Затем отредактируйте .env и добавьте свои API ключи"
    exit 1
fi

# Запуск PostgreSQL
echo "📦 Starting PostgreSQL..."
docker compose up -d

# Ожидание запуска PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Запуск Backend
echo "🔧 Starting Backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

python main.py &
BACKEND_PID=$!
cd ..

# Запуск Frontend
echo "🎨 Starting Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm packages..."
    npm install > /dev/null 2>&1
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Content Creator запущен!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "🗄️  PostgreSQL: localhost:5111"
echo ""
echo "Для остановки нажмите Ctrl+C"

# Ожидание завершения
wait $BACKEND_PID $FRONTEND_PID

