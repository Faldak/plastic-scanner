import os
import requests
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "GPKmLKlpIhdozMQ7STZs")
ROBOFLOW_MODEL_ID = os.environ.get("ROBOFLOW_MODEL_ID", "garbage-classification-3/2")

ITEM_INFO = {
    "plastic": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма пластика. Ополоснуть от остатков.",
        "tip": "Большинство твёрдых пластиковых предметов перерабатываются"
    },
    "plastic bottle": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма. Убрать крышку, ополоснуть.",
        "tip": "Пластиковые бутылки — один из самых часто перерабатываемых материалов"
    },
    "bottle": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма. Ополоснуть перед сдачей.",
        "tip": "Бутылки с маркировкой #1 и #2 принимают везде"
    },
    "cardboard": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма бумаги/картона. Сложить плоско.",
        "tip": "Картон перерабатывается до 7 раз"
    },
    "paper": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма макулатуры.",
        "tip": "Не сдавайте мокрую или жирную бумагу"
    },
    "metal": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма металла.",
        "tip": "Алюминий переплавляется бесконечно без потери качества"
    },
    "can": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма. Ополоснуть банку.",
        "tip": "Из переработанной банки новую делают за 60 дней"
    },
    "glass": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма стекла.",
        "tip": "Стекло перерабатывается бесконечно без потери качества"
    },
    "glass bottle": {
        "recyclable": True, "color": "green",
        "verdict": "Можно переработать",
        "instruction": "Сдать в пункт приёма стекла. Убрать крышку.",
        "tip": "Стеклянные бутылки принимают во многих супермаркетах"
    },
    "trash": {
        "recyclable": False, "color": "red",
        "verdict": "В обычный мусор",
        "instruction": "Выбросить в контейнер для смешанных отходов.",
        "tip": "Если не уверены — лучше в общий мусор, чем загрязнять переработку"
    },
    "garbage": {
        "recyclable": False, "color": "red",
        "verdict": "В обычный мусор",
        "instruction": "Выбросить в контейнер для смешанных отходов.",
        "tip": "Смешанные материалы обычно не перерабатываются"
    },
    "styrofoam": {
        "recyclable": False, "color": "red",
        "verdict": "В обычный мусор",
        "instruction": "Выбросить в общий мусор. Пенопласт почти нигде не принимают.",
        "tip": "Пенопласт (PS #6) — один из самых сложных для переработки материалов"
    },
    "plastic bag": {
        "recyclable": False, "color": "orange",
        "verdict": "Уточните в вашем городе",
        "instruction": "В большинстве городов не принимают. Уточните в местном пункте.",
        "tip": "Некоторые супермаркеты собирают пластиковые пакеты отдельно"
    },
    "food waste": {
        "recyclable": False, "color": "red",
        "verdict": "В органику или общий мусор",
        "instruction": "В компост или контейнер для органических отходов.",
        "tip": "Пищевые отходы можно компостировать дома"
    },
    "battery": {
        "recyclable": True, "color": "orange",
        "verdict": "Специальная утилизация",
        "instruction": "Сдать в пункт приёма батареек (есть в супермаркетах).",
        "tip": "Одна батарейка загрязняет 20 м² земли — не выбрасывайте в мусор"
    },
    "electronics": {
        "recyclable": True, "color": "orange",
        "verdict": "Специальная утилизация",
        "instruction": "Сдать в пункт приёма электроники или сервисный центр.",
        "tip": "В электронике содержатся ценные металлы и опасные вещества"
    },
}

KEYWORD_MAP = {
    "plastic": "plastic",
    "bottle": "bottle",
    "cardboard": "cardboard",
    "paper": "paper",
    "metal": "metal",
    "can": "can",
    "glass": "glass",
    "trash": "trash",
    "garbage": "garbage",
    "styrofoam": "styrofoam",
    "foam": "styrofoam",
    "bag": "plastic bag",
    "food": "food waste",
    "battery": "battery",
    "electron": "electronics",
}


def find_item_info(label):
    label_lower = label.lower().strip()
    if label_lower in ITEM_INFO:
        return ITEM_INFO[label_lower]
    for keyword, mapped in KEYWORD_MAP.items():
        if keyword in label_lower:
            return ITEM_INFO.get(mapped)
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    image_b64 = data.get("image")

    if not image_b64:
        return jsonify({"error": "Нет изображения"}), 400

    print(f"API KEY: {ROBOFLOW_API_KEY[:8]}..." if ROBOFLOW_API_KEY else "API KEY ПУСТОЙ!")
    print(f"MODEL ID: {ROBOFLOW_MODEL_ID}")

    if not ROBOFLOW_API_KEY:
        return jsonify({"error": "ROBOFLOW_API_KEY не задан на сервере"}), 500

    try:
        rf_url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL_ID}"
        print(f"Запрос к: {rf_url}")

        response = requests.post(
            rf_url,
            params={"api_key": ROBOFLOW_API_KEY},
            data=image_b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )

        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text[:300]}")

        response.raise_for_status()
        predictions = response.json()

    except Exception as e:
        print(f"ОШИБКА: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Ошибка запроса к Roboflow: {str(e)}"}), 502

    preds = predictions.get("predictions", [])
    print(f"Предсказаний: {len(preds)}")

    if not preds:
        return jsonify({
            "found": False,
            "message": "Объект не распознан. Поднесите предмет ближе и убедитесь в хорошем освещении."
        })

    best = max(preds, key=lambda p: p.get("confidence", 0))
    label = best.get("class", "").strip()
    confidence = round(best.get("confidence", 0) * 100)
    print(f"Результат: {label} ({confidence}%)")

    info = find_item_info(label)

    if not info:
        return jsonify({
            "found": True,
            "raw_label": label,
            "confidence": confidence,
            "recyclable": None,
            "color": "orange",
            "verdict": f"Обнаружен: {label}",
            "instruction": "Уточните возможность переработки в вашем городе.",
            "tip": "Если сомневаетесь — выбрасывайте в общий мусор"
        })

    return jsonify({
        "found": True,
        "raw_label": label,
        "confidence": confidence,
        "recyclable": info["recyclable"],
        "color": info["color"],
        "verdict": info["verdict"],
        "instruction": info["instruction"],
        "tip": info["tip"]
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
