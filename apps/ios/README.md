# iOS проект DormFlow

Папка содержит iOS-пайплайн для общего Kivy/Python-кода проекта. Сборка iOS не выполняется через Buildozer: нужен macOS, Xcode и `kivy-ios`.

## Что уже подготовлено

- `build_ios.sh` создает `.venv-ios`, ставит зависимости `kivy-ios`, собирает `python3 + kivy`, создает staging-копию приложения и генерирует Xcode-проект.
- Staging-копия лежит в `apps/ios/.build/app` и содержит `main.py`, `requirements.txt`, пакет `dormflow`.
- Xcode-проект создается в `apps/ios/xcode/dormflow-ios`.
- Bundle ID по умолчанию: `org.dormflow.dormflow`.
- Иконка и launch image берутся из `assets/ios/icon.png` и `assets/ios/launch.png`.

## Требования на Mac

```bash
xcode-select --install
brew install autoconf automake libtool pkg-config
brew link libtool
```

Нужен установленный Xcode 13+ с iOS SDK. Первый билд `kivy-ios` долгий: toolchain компилирует Python, SDL2, Kivy и связанные библиотеки под iPhone/iOS Simulator.

## Сборка

```bash
cd /path/to/MobileApp
bash apps/ios/build_ios.sh
```

После успешного выполнения:

```bash
open apps/ios/xcode/dormflow-ios/*.xcodeproj
```

В Xcode нужно выбрать Team/Signing, затем запустить проект на iOS Simulator или реальном устройстве.

## Backend URL

Перед запуском клиента подними API:

```bash
python main.py backend
```

Для iOS Simulator в приложении указывай:

```text
http://127.0.0.1:8765
```

Для реального iPhone нужен LAN IP компьютера:

```text
http://192.168.1.25:8765
```

`build_ios.sh` добавляет `NSAppTransportSecurity/NSAllowsArbitraryLoads=true`, чтобы dev-сервер на HTTP работал в симуляторе и на устройстве. Для production нужно использовать HTTPS и убрать arbitrary loads.

## Настройки через переменные окружения

```bash
DORMFLOW_IOS_BUNDLE_ID=org.example.dormflow bash apps/ios/build_ios.sh
DORMFLOW_IOS_TITLE=DormFlow bash apps/ios/build_ios.sh
DORMFLOW_IOS_PLATFORM=iphonesimulator-arm64 bash apps/ios/build_ios.sh
```

Поддерживаемые значения `DORMFLOW_IOS_PLATFORM`:

- `auto` - стандартный набор платформ для текущего Mac.
- `iphoneos-arm64` - только реальное устройство.
- `iphonesimulator-arm64` - Apple Silicon simulator.
- `iphonesimulator-x86_64` - Intel simulator.
- `all` - все поддерживаемые платформы.

## Важные правила

- Не редактируй исходники внутри `apps/ios/.build/app` и `apps/ios/xcode/dormflow-ios/.../YourApp`: они пересоздаются/синхронизируются toolchain. Правки нужно делать в корневом `main.py` и `dormflow`.
- Если добавятся Python-библиотеки с C/C++ расширениями, для iOS потребуется отдельный recipe в `kivy-ios`; обычный `pip install` сработает только для pure-Python пакетов.
- После изменения зависимостей запускай `bash apps/ios/build_ios.sh` повторно, чтобы Xcode-проект получил обновленные фреймворки.

## Официальные ориентиры

- Kivy packaging iOS: https://kivy.org/doc/stable/guide/packaging-ios.html
- Kivy-iOS toolchain: https://github.com/kivy/kivy-ios
