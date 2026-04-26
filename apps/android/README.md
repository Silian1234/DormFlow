# Android проект (p4a + buildozer)

## Что это

Платформенный Android-проект для приложения DormFlow на Python/Kivy.

## Структура

- `buildozer.spec` — конфиг сборки Android APK/AAB.
- Общий код приложения берется из корня репозитория (`../../main.py`, пакет `dormflow`).
- Backend не включается в APK. Приложение подключается к внешнему API URL.

## Backend для Android Emulator

Сначала запусти API на Windows:

```powershell
.\.venv310\Scripts\python.exe main.py backend
```

Для ручного тестирования удобнее запускать backend и APK одной командой:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_android_dev.ps1 -CleanData
```

Эта команда поднимает backend на Windows, ставит APK в эмулятор и запускает приложение.
Backend не встраивается в APK: Android-приложение подключается к серверу по сети.

В Android Emulator указывай в поле API URL:

```text
http://10.0.2.2:8765
```

Для реального телефона нужен LAN IP компьютера, например:

```text
http://192.168.1.25:8765
```

В `buildozer.spec` включен `INTERNET` permission. Для production лучше поднять HTTPS; локальный HTTP нужен только для разработки.

## Сборка в WSL (рекомендуется на Windows)

Buildozer корректно работает в Linux-окружении, поэтому для Windows нужен WSL2 + Ubuntu.

### 1) Установка WSL (PowerShell от администратора)

```powershell
wsl --install -d Ubuntu
```

После перезагрузки системы открой Ubuntu и создай пользователя.

### 2) Установка зависимостей в Ubuntu

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv libffi-dev libssl-dev
python3 -m pip install --user --upgrade pip
python3 -m pip install --user buildozer cython
```

Добавь `~/.local/bin` в `PATH`, если нужно:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 3) Сборка debug APK

```bash
cd /mnt/e/Projects/MobileApp/apps/android
buildozer android debug
```

APK появится в каталоге `apps/android/bin/`.

### 4) Сборка release

```bash
cd /mnt/e/Projects/MobileApp/apps/android
buildozer android release
```

## Типовые проблемы

- Ошибки Java/SDK: проверь, что установлен `openjdk-17-jdk`.
- Недоступен `buildozer`: проверь `PATH` и `~/.local/bin`.
- Медленный первый билд: это нормально, p4a скачивает Android toolchain при первом запуске.
