#!/bin/bash

# Сборка образа
docker build -t turel_app .

# Запуск контейнера с доступом к камере и GPIO
docker run --privileged \
    --device=/dev/video0:/dev/video0 \
    --device=/dev/gpio:/dev/gpio \
    -v /dev/gpio:/dev/gpio \
    -v /sys/class/gpio:/sys/class/gpio \
    -v /dev/mem:/dev/mem \
    --network host \
    turel_app 