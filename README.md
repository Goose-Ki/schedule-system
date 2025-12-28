Cистема управления расписанием с Go backend и Python-утилитами (aiogram)

Project Overview
- Назначение: Сервис управления расписаниями с бэкендом на Go и вспомогательными Python-скриптами/ботом для интеграций и тестирования.
- Кратко: Go-сервер предоставляет HTTP API для работы с расписаниями и пользователями; pyschedule клиент, тесты и Telegram-бот

Repository Structure
- Root files: основной README.md и CI-конфигурация.
- Go backend: go-backend/
- Python tools: pyschedule/

Architecture
- Backend (Go):
  - Server entry: go-backend/cmd/server/main.go
  - Models: go-backend/internal/models/models.go
  - Handlers: go-backend/internal/handlers/schedule_handler.go, go-backend/internal/handlers/get_schedule_by_id.go, go-backend/internal/handlers/user_handler.go
  - Database: go-backend/internal/database/db.go
- Python tools:
  - API client: pyschedule/api_client.py
  - Конфиг: pyschedule/config.py
  - Хендлеры / bot: pyschedule/handlers.py, pyschedule/keyboards.py
  - Запуск: pyschedule/run.py
  - Тесты: pyschedule/test_api.py

Prerequisites
- Go: версия, совместимая с go-backend/go.mod (рекомендуется Go 1.18+).
- Python: 3.8+.
- DB: реляционная БД (подключение и настройки в go-backend/internal/database/db.go).
- Python deps: установить из pyschedule/requirements.txt.

Quick Start  Backend (Go)
- Сборка и запуск:
cd go-backend
go mod download
go run ./cmd/server

- Сборка бинарника:
cd go-backend
go build ./cmd/server
./server   # server.exe на Windows

- Конфигурация: проверьте параметры подключения к БД и порт в go-backend/cmd/server/main.go и go-backend/internal/database/db.go.

Quick Start  Python tools
- Установка зависимостей:
cd pyschedule
python -m pip install -r requirements.txt

- Настройка: отредактируйте pyschedule/config.py  укажите URL API, токены и пр.
- Запуск:
cd pyschedule
python run.py

Configuration
- Go: параметры сервера и БД в go-backend/cmd/server/main.go и go-backend/internal/database/db.go. Рекомендуется использовать переменные окружения для секретов.
- Python: настройки в pyschedule/config.py. Можно расширить под .env и python-dotenv.

API  где смотреть
- Основные маршруты и логика  в папке go-backend/internal/handlers:
  - go-backend/internal/handlers/schedule_handler.go
  - go-backend/internal/handlers/get_schedule_by_id.go
  - go-backend/internal/handlers/user_handler.go
- Модели данных  go-backend/internal/models/models.go

Database
- Подключение и базовая логика  go-backend/internal/database/db.go.
- Рекомендации: хранить строку подключения и миграции в безопасном месте; использовать инструмент миграций (например, golang-migrate) при расширении схемы.

Testing
- Python:
cd pyschedule
pytest -q

- Go:
cd go-backend
go test ./...

Development
- Форматирование и проверка (Go): gofmt, go vet.
- Локальная отладка: запустите сервер и используйте pyschedule/api_client.py или curl для проверки эндпоинтов.
- Добавление фич: добавляйте обработчики в go-backend/internal/handlers и модели в go-backend/internal/models/models.go. Обновляйте pyschedule при изменениях API.

Deployment
- Go: билдите бинарник и деплойте в контейнер/VM.
- Python: запуск в виртуальном окружении или контейнере; безопасно передавайте секреты через переменные окружения.
- CI: в репозитории есть пример workflow для Python: .github/workflows/python-ci.yml

Troubleshooting
- Сервер не стартует: проверьте логи сервера и параметры подключения к БД.
- Python не соединяется: убедитесь, что pyschedule/config.py содержит правильный URL API и токены.
- Кодировка/Windows: при записи файлов убедитесь, что используется UTF-8.


Files To Look At
- Server entry: go-backend/cmd/server/main.go
- DB: go-backend/internal/database/db.go
- Models: go-backend/internal/models/models.go
- Handlers: go-backend/internal/handlers
- Python runner: pyschedule/run.py
- Python client: pyschedule/api_client.py
- Config (Python): pyschedule/config.py
- Tests (Python): pyschedule/test_api.py
