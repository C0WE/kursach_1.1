# kursach_1.1 – Микросервисная Инфраструктура с Мониторингом

Полнофункциональная контейнеризированная система для разработки и тестирования микросервисов с встроенным мониторингом, логированием и управлением инфраструктурой.

## 📋 Описание

Проект реализует production-ready окружение для веб-приложения на Flask с использованием:

- **Flask Webapp** – основное веб-приложение (порт 3000)
- **Nginx** – реверс-прокси с балансировкой нагрузки (порт 80/443)
- **PostgreSQL** – реляционная база данных
- **Redis** – кеш и хранилище сессий
- **Prometheus** – система сбора метрик (порт 9090)
- **Grafana** – визуализация данных и дашборды (порт 3000)
- **Docker Swarm** – оркестрация контейнеров

## 🗂️ Структура Проекта

```
kursach_1.1/
├── docker-compose.yml              # Основной конфиг для разработки
├── docker-compose.swarm.yml        # Конфиг для Docker Swarm
├── Makefile                        # Удобные команды для управления
├── Dockerfile                      # Образ nginx
├── pytest.ini                      # Конфиг для тестирования
├── health-check.sh                 # Скрипт проверки здоровья сервисов
├── init-swarm.sh                   # Инициализация Docker Swarm
│
├── nginx/
│   ├── conf.d/default.conf         # Конфигурация nginx (балансировка, SSL, rate-limiting)
│   └── ssl/
│       ├── cert.pem                # SSL сертификат
│       └── key.pem                 # Приватный ключ
│
├── monitoring/
│   ├── prometheus.yml              # Конфиг Prometheus (scrape configs)
│   └── grafana-dashboard.json      # Дашборд Grafana (10 панелей с метриками)
│
└── app/                            # Flask приложение
    ├── test_*.py                   # Unit и integration тесты
    └── ... (основные файлы приложения)
```

## 🚀 Быстрый Старт

### Предварительные требования

- Docker >= 20.10
- Docker Compose >= 1.29
- Make (опционально, но рекомендуется)
- Python 3.9+ (для локального запуска тестов)

### Запуск с помощью Make

```bash
# Просмотр всех доступных команд
make help

# Построить образы
make build

# Запустить все сервисы (фон)
make up

# Посмотреть логи в реальном времени
make logs

# Запустить тесты
make test

# Перезагрузить сервисы
make restart

# Проверить здоровье сервисов
make health

# Остановить и удалить контейнеры
make down

# Очистить всё (удалить тома)
make clean
```

### Запуск без Make

```bash
# Построить образы
docker-compose build

# Запустить сервисы
docker-compose up -d

# Остановить
docker-compose down

# Удалить всё (включая данные)
docker-compose down -v
```

## 📊 Веб-Интерфейсы

После `make up` доступны:

| Сервис | URL | Назначение |
|--------|-----|-----------|
| Webapp | http://localhost | Основное приложение |
| Prometheus | http://localhost:9090 | Метрики и PromQL запросы |
| Grafana | http://localhost:3000 | Дашборды и визуализация |
| Health Check | http://localhost/health | Статус приложения |
| Nginx Metrics | http://localhost/metrics | Метрики приложения |

**Grafana credentials** (стандартные):
- Email: `admin`
- Password: `admin`

## 🔧 Конфигурация

### Nginx (default.conf)

Реверс-прокси настроен с:

- **Rate Limiting**:
  - API endpoints: 10 req/s (burst 20)
  - General: 100 req/s (burst 50)
  - HTTP 429 на превышение

- **SSL/TLS**:
  - Protocols: TLSv1.2, TLSv1.3
  - HTTP/2 support
  - Strict-Transport-Security headers

- **Балансировка**:
  - Least connections алгоритм
  - Failover на webapp:3000
  - Connection keepalive

- **Caching**:
  - Статические файлы: 30 дней
  - gzip сжатие для текста/JSON/JavaScript

- **Security Headers**:
  - X-Frame-Options
  - X-Content-Type-Options
  - X-XSS-Protection
  - CSP (Content-Security-Policy)

### Prometheus (prometheus.yml)

Сбор метрик с:

- `webapp` – Flask приложение (порт 3000, path `/metrics`)
- `postgres-exporter` – метрики PostgreSQL
- `redis-exporter` – метрики Redis
- `nginx` – метрики веб-сервера

**Интервалы**:
- Scrape: 15 сек
- Evaluation: 15 сек

### Grafana Dashboard (grafana-dashboard.json)

10 предустановленных панелей:

1. **Flask Requests/sec** – частота запросов по методам/эндпоинтам
2. **Flask Response Time (p95)** – время ответа на 95-м percentile
3. **PostgreSQL Database Size** – размер БД в MB
4. **PostgreSQL Transactions** – коммиты и откаты в сек
5. **Redis Memory Usage** – использование памяти Redis
6. **Redis Keys** – количество ключей по БД
7. **Redis Cache Hit Rate** – процент попаданий в кеш
8. **Redis Commands/sec** – объём команд в сек
9. **PostgreSQL Cache Hit Rate** – hit rate дискового кеша
10. **Flask Errors (4xx, 5xx)** – количество ошибок

Автообновление каждые 10 сек.

### Тестирование (pytest.ini)

```ini
[pytest]
testpaths = app
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short

markers:
    integration - Integration tests
    unit - Unit tests
    slow - Slow running tests
```

Запуск тестов:
```bash
# Все тесты
make test

# Только unit-тесты
docker-compose run --rm webapp pytest -m unit -v

# Только integration-тесты
docker-compose run --rm webapp pytest -m integration -v

# Исключить slow-тесты
docker-compose run --rm webapp pytest -m "not slow" -v
```

## 🐳 Docker Swarm

Для production-развёртывания:

```bash
# Инициализировать Swarm и создать secrets
./init-swarm.sh

# Или вручную:
docker swarm init
echo "db_pass" | docker secret create db_password -
echo "secret-key" | docker secret create secret_key -
docker stack deploy -c docker-compose.swarm.yml test-env

# Просмотр сервисов
docker service ls

# Логи сервиса
docker service logs test-env_webapp

# Удалить стек
docker stack rm test-env
```

## 📈 Мониторинг Здоровья

### Health Check скрипт

```bash
./health-check.sh
```

Проверяет статус:
- Nginx (localhost)
- Flask webapp (localhost/health)
- Prometheus (localhost:9090)
- Grafana (localhost:3000)

### Встроенный healthcheck в Docker

```bash
# Docker сам проверяет здоровье контейнеров
docker-compose ps

# Статус каждого сервиса (healthy/unhealthy/starting)
```

## 🔐 SSL/TLS

Сертификаты хранятся в `nginx/ssl/`:

- `cert.pem` – публичный сертификат
- `key.pem` – приватный ключ

Nginx слушает:
- `0.0.0.0:80` – перенаправляет на HTTPS (для лок. разработки – прямо к webapp)
- `0.0.0.0:443` – HTTPS с SSL

Для production используйте [Let's Encrypt](https://letsencrypt.org/) и [Certbot](https://certbot.eff.org/).

## 🛠️ Разработка

### Структура приложения

Flask приложение находится в `app/`:

```
app/
├── __init__.py          # Инициализация Flask
├── models.py            # ORM модели (SQLAlchemy)
├── routes.py            # API эндпоинты
├── services/            # Бизнес-логика
├── utils/               # Утилиты
├── test_routes.py       # Integration тесты
├── test_services.py     # Unit тесты
└── requirements.txt     # Python зависимости
```

### Добавление зависимостей

```bash
# Обновить requirements.txt и пересобрать
docker-compose build webapp

# Или перезапустить (если не изменились зависимости)
docker-compose restart webapp
```

### Логирование

Логи доступны через:

```bash
# Логи конкретного сервиса
docker-compose logs webapp
docker-compose logs nginx
docker-compose logs postgres

# Живые логи
docker-compose logs -f

# Последние N строк
docker-compose logs --tail=100 webapp
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
make test

# С покрытием кода (если установлен pytest-cov)
docker-compose run --rm webapp pytest --cov=app tests/

# Verbose output
docker-compose run --rm webapp pytest -vv

# Остановка на первой ошибке
docker-compose run --rm webapp pytest -x
```

### Написание тестов

Пример unit-теста:

```python
import pytest
from app.services import MyService

@pytest.mark.unit
def test_my_service():
    service = MyService()
    result = service.process()
    assert result is not None
```

Пример integration-теста:

```python
@pytest.mark.integration
def test_api_endpoint(client):
    response = client.get('/api/data')
    assert response.status_code == 200
    assert 'data' in response.json
```

## 📝 Логирование Prometheus

Flask интегрирован с Prometheus метриками:

```python
from prometheus_client import Counter, Histogram

# Счётчик запросов
request_count = Counter('flask_requests_total', 'Total requests', ['method', 'endpoint', 'status'])

# Гистограмма времени ответа
request_duration = Histogram('flask_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
```

Метрики доступны по `/metrics` эндпоинту.

## 🐛 Troubleshooting

### Port already in use

```bash
# Найти процесс на порту 80
lsof -i :80

# Или изменить в docker-compose.yml
# ports:
#   - "8080:80"  # вместо 80
```

### Контейнер постоянно перезагружается

```bash
# Проверить логи
docker-compose logs webapp

# Проверить здоровье
docker inspect <container_id> | grep -A 5 Healthcheck
```

### База данных не инициализируется

```bash
# Очистить всё и перезапустить
make clean
make up

# Проверить логи postgres
docker-compose logs postgres
```

### Prometheus не собирает метрики

```bash
# Проверить конфиг prometheus.yml
docker-compose logs prometheus

# Проверить доступность webapp с prometheus контейнера
docker-compose exec prometheus curl http://webapp:3000/metrics
```

## 📚 Документация

- [Flask](https://flask.palletsprojects.com/)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Docker Swarm](https://docs.docker.com/engine/swarm/)
- [nginx](https://nginx.org/en/docs/)

## 🤝 Разработка

### Разработка локально с горячей перезагрузкой

```bash
# Запустить только необходимые сервисы
docker-compose up -d postgres redis nginx

# Запустить Flask локально (требует установки зависимостей)
cd app
pip install -r requirements.txt
FLASK_ENV=development FLASK_APP=app.py flask run --host 0.0.0.0 --port 3000
```

### Git Workflow

```bash
# Клонировать
git clone https://github.com/C0WE/kursach_1.1.git
cd kursach_1.1

# Создать ветку
git checkout -b feature/my-feature

# Внести изменения, закоммитить
git commit -am "Add feature description"

# Запустить тесты перед push
make test

# Push в репозиторий
git push origin feature/my-feature
```

## 📋 Чек-лист перед production

- [ ] Изменить пароли в `init-swarm.sh`
- [ ] Обновить SSL сертификаты (Let's Encrypt)
- [ ] Настроить backup PostgreSQL
- [ ] Настроить логирование (ELK, CloudWatch)
- [ ] Настроить alerting в Prometheus/Grafana
- [ ] Провести load-testing
- [ ] Настроить CI/CD pipeline
- [ ] Документировать API (Swagger/OpenAPI)
- [ ] Настроить мониторинг uptime
- [ ] Провести security audit

## 📄 Лицензия

MIT License – свободное использование в образовательных и коммерческих целях.

## 👤 Автор

**C0WE** – GitHub: https://github.com/C0WE

---

**Последнее обновление:** Декабрь 2025  
**Версия:** 1.1
