FROM --platform=linux/arm/v7 debian:bullseye-slim

# Установка базовых зависимостей
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    libopencv-dev \
    python3-opencv \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY requirements.txt .
COPY upravl_mart.py .
COPY turel_control.py .
COPY config.py .
COPY mock_gpio.py .
COPY YOLOv8m.pt .  # Копируем вашу обученную модель

# Создание и активация виртуального окружения
RUN python3.10 -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# Установка зависимостей
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Установка PyTorch для ARM
RUN pip install torch==1.7.0 torchvision==0.8.1 torchaudio==0.7.0 -f https://download.pytorch.org/whl/torch_stable.html

# Настройка доступа к камере
RUN usermod -a -G video root

# Запуск приложения
CMD ["python", "upravl_mart.py"] 