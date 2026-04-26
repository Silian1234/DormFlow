# DormFlow: Android + iOS (Python/Kivy)

Полноценный клиент-серверный проект DormFlow:

- **Backend**: `FastAPI + SQLite`
- **Android**: `python-for-android + buildozer`
- **iOS**: `kivy-ios + Xcode`

Мобильный клиент один (`main.py` + пакет `dormflow`) и работает с API-сервером. Платформенные проекты лежат отдельно в `apps/android` и `apps/ios`.

## Архитектура

### Общий код

- [`main.py`](./main.py) — вход в приложение.
- [`docs/architecture.md`](./docs/architecture.md) — описание архитектуры по слоям.
- [`dormflow/models.py`](./dormflow/models.py) — доменные сущности.
- [`dormflow/seed.py`](./dormflow/seed.py) — стартовые данные.
- [`dormflow/repository.py`](./dormflow/repository.py) — JSON repository.
- [`dormflow/services.py`](./dormflow/services.py) — бизнес-логика.
- [`dormflow/api_client.py`](./dormflow/api_client.py) — HTTP-клиент мобильного приложения.
- [`dormflow/api_service.py`](./dormflow/api_service.py) — service-layer поверх backend API.
- [`dormflow/app.py`](./dormflow/app.py) — Kivy-контроллер приложения.
- [`dormflow/ui.kv`](./dormflow/ui.kv) — экранная разметка.
- [`backend`](./backend) — FastAPI-сервер, регистрация, авторизация, SQLite.

### Платформенные проекты

- [`apps/android`](./apps/android) — Android-сборка через `buildozer`.
- [`apps/ios`](./apps/ios) — iOS-сборка через `kivy-ios`.

## Быстрый запуск (desktop, для проверки логики)

Рекомендуемый Python для Kivy: **3.10–3.12**.

Сначала запусти backend:

```powershell
py -3.10 -m venv .venv310
.\.venv310\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv310\Scripts\python.exe main.py backend
```

Потом в другом терминале запусти клиент:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Или одной командой:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_desktop.ps1 -InstallDeps
```

## Тесты

```powershell
.\.venv310\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv310\Scripts\python.exe -m unittest discover -s tests
```

## Сборка Android

Смотри подробные шаги: [`apps/android/README.md`](./apps/android/README.md).

Кратко (в WSL Ubuntu):

```bash
cd /mnt/e/Projects/MobileApp/apps/android
buildozer android debug
```

Из Windows PowerShell можно дернуть WSL сборку так:

```powershell
powershell -ExecutionPolicy Bypass -File .\apps\android\build_android.ps1
```

Для ручной проверки в Android Emulator с автоматическим запуском backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_android_dev.ps1 -CleanData
```

## Сборка iOS

Смотри подробные шаги: [`apps/ios/README.md`](./apps/ios/README.md).

Кратко (на macOS с Xcode):

```bash
cd /path/to/MobileApp
bash apps/ios/build_ios.sh
```

Скрипт создает Xcode-проект в `apps/ios/xcode/dormflow-ios`, применяет iOS-иконку/launch image из `assets/ios` и использует Bundle ID `org.dormflow.dormflow` по умолчанию.

## Функционал MVP

- Регистрация и логин через backend API.
- Bearer-сессия хранится на устройстве, выход удаляет локальный токен.
- Роли проверяются сервером: `resident` / `headman`.
- Староста создается только по коду `DORMFLOW_HEADMAN_CODE`.
- Дежурства: список, карточка, отметка выполнения, создание старостой.
- Заявки: список, создание жильцом, перевод статуса только старостой.
- Объявления: просмотр для всех, публикация только старостой.
- Голосования: просмотр, голосование один раз на пользователя, создание только старостой.
- Персистентность: SQLite на backend, локально хранится только URL сервера и токен.

## Материалы по заданию

- Backend: [`backend/README.md`](./backend/README.md)
- API: [`docs/api.md`](./docs/api.md)
- Паспорт проекта: [`docs/project-passport.md`](./docs/project-passport.md)
- Интеллект-карта: [`docs/mindmap.md`](./docs/mindmap.md)
- Ранний wireframe-прототип: [`prototype/index.html`](./prototype/index.html)
