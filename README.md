# Сканер пластика — Roboflow + Railway

Веб-приложение для определения типа пластика через камеру.
Работает на телефоне в браузере.

## Технологии
- **Бэкенд**: Python + Flask
- **AI**: Roboflow (готовая модель распознавания маркировок пластика)
- **Хостинг**: Railway

---

## Шаг 1 — Получить Roboflow API ключ (бесплатно)

1. Зайти на https://roboflow.com → Sign Up (бесплатно)
2. После регистрации: Settings → API Keys → скопировать ключ
3. Также можно получить ключ прямо на странице модели в Universe

## Шаг 2 — Выбрать модель на Roboflow Universe

Лучшие готовые модели для пластика:

| Модель | Ссылка | Что распознаёт |
|--------|--------|----------------|
| Plastic Recycling Code | universe.roboflow.com/swu-deep-learning-project/plastic-recycling-code | Маркировки #1–#7 |
| YOLO Waste Detection | universe.roboflow.com/projectverba/yolo-waste-detection | Бутылки, банки, упаковка |
| Recyclable Items | universe.roboflow.com/recycle/recyclable-items | Пластик, стекло, металл |

Зайдите на страницу модели → вкладка "Model" → скопируйте model_id
(например: `plastic-recycling-code/1`)

Запишите в переменную `ROBOFLOW_MODEL_ID` (см. Шаг 4).

## Шаг 3 — Загрузить код на GitHub

```bash
# В папке проекта:
git init
git add .
git commit -m "first commit"

# Создайте репозиторий на github.com, затем:
git remote add origin https://github.com/ВАШ_ЛОГИН/plastic-scanner.git
git push -u origin main
```

## Шаг 4 — Задеплоить на Railway

1. Зайти на https://railway.com → Login with GitHub
2. New Project → Deploy from GitHub repo → выбрать ваш репозиторий
3. Подождать, пока Railway установит зависимости (~1-2 минуты)
4. Перейти в Settings → Variables → добавить переменные:

```
ROBOFLOW_API_KEY = ваш_ключ_из_шага_1
ROBOFLOW_MODEL_ID = plastic-recycling-code/1
```

5. Railway автоматически перезапустит приложение
6. Перейти в Settings → Networking → Generate Domain
7. Скопировать ссылку вида `plastic-scanner-xxx.railway.app`

## Использование

Откройте ссылку в браузере телефона →
- Разрешите доступ к камере
- Наведите на маркировку ♺ на упаковке
- Нажмите «Сканировать»
- Получите результат: можно переработать или нет

## Структура проекта

```
plastic-scanner/
├── app.py              ← Flask сервер + логика AI
├── templates/
│   └── index.html      ← Фронтенд (HTML + JS)
├── requirements.txt    ← Python зависимости
├── Procfile            ← Команда запуска
├── railway.json        ← Конфиг Railway
└── README.md
```

## Альтернативные бесплатные хостинги

| Платформа | Условия | Сложность |
|-----------|---------|-----------|
| **Render.com** | Бесплатный тир (засыпает после 15 мин простоя) | Легко |
| **Vercel** | Бесплатно, но только для Node.js/фронтенда | Средне |
| **Railway** | $5 кредит 30 дней, потом $5/мес | Легко |
| **Fly.io** | Бесплатный тир 3 маленьких VM | Сложнее |

Для **Render.com** (полностью бесплатно):
1. render.com → New Web Service → подключить GitHub
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Добавить Environment Variables: ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID

---

## Как улучшить точность

Если модель плохо распознаёт:
1. Освещение — снимайте при хорошем свете
2. Расстояние — 10-20 см от упаковки
3. Фокус — подождите, пока камера сфокусируется
4. Другая модель — попробуйте другой model_id из Roboflow Universe
"# plastic-scanner" 
