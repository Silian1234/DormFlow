# DormFlow Backend

Python API-сервер для мобильного приложения DormFlow.

## Возможности

- Регистрация пользователя.
- Логин по email/паролю.
- Bearer-сессии.
- Роль `resident` для обычного жильца.
- Роль `headman` только по коду старосты.
- Серверная проверка доступа к `headman` операциям.
- SQLite-хранилище пользователей, сессий, заявок, дежурств, объявлений и голосований.

## Запуск

```powershell
py -3.10 -m venv .venv310
.\.venv310\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python main.py backend
```

По умолчанию сервер слушает `0.0.0.0:8765`.

## Переменные окружения

```powershell
$env:DORMFLOW_HOST = "0.0.0.0"
$env:DORMFLOW_PORT = "8765"
$env:DORMFLOW_DATABASE = "E:\Projects\MobileApp\backend\data\dormflow.sqlite3"
$env:DORMFLOW_HEADMAN_CODE = "HEADMAN-2026"
python main.py backend
```

Для Android Emulator в приложении указывай API URL:

```text
http://10.0.2.2:8765
```

Для iOS Simulator / desktop:

```text
http://127.0.0.1:8765
```

Для реального телефона нужен LAN IP компьютера, например:

```text
http://192.168.1.25:8765
```

## Проверка

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```
