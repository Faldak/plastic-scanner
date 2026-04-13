import os
import base64
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "GPKmLKlpIhdozMQ7STZs")

# Модель на Roboflow Universe для маркировок пластика
# https://universe.roboflow.com/swu-deep-learning-project/plastic-recycling-code
ROBOFLOW_MODEL_ID = os.environ.get(
    "ROBOFLOW_MODEL_ID",
    "plastic-recycling-code/1"   # замените на ID вашей модели из Universe
)

# База знаний по всем типам пластика
PLASTIC_INFO = {
    "1": {
        "name": "PET / PETE",
        "full": "Полиэтилентерефталат",
        "recyclable": True,
        "color": "green",
        "instruction": "Сдать в пункт приёма. Убрать крышку и этикетку. Ополоснуть.",
        "examples": "Бутылки для воды и напитков, лотки для еды",
        "tip": "Самый часто перерабатываемый пластик в мире"
    },
    "2": {
        "name": "HDPE",
        "full": "Полиэтилен высокой плотности",
        "recyclable": True,
        "color": "green",
        "instruction": "Сдать в пункт приёма. Ополоснуть перед сдачей.",
        "examples": "Канистры, флаконы шампуня, молочные бутылки",
        "tip": "Очень хорошо перерабатывается — из него делают трубы и мебель"
    },
    "3": {
        "name": "PVC / V",
        "full": "Поливинилхлорид",
        "recyclable": False,
        "color": "red",
        "instruction": "Выбросить в общий мусор. Не сжигать — выделяет токсины!",
        "examples": "Трубы, оконные рамы, упаковочная плёнка",
        "tip": "Содержит хлор — при сжигании образует диоксины"
    },
    "4": {
        "name": "LDPE",
        "full": "Полиэтилен низкой плотности",
        "recyclable": False,
        "color": "orange",
        "instruction": "Обычно не принимают. Уточните в вашем пункте приёма.",
        "examples": "Пакеты, упаковочная плёнка, крышки",
        "tip": "В некоторых городах принимают отдельно — уточните локально"
    },
    "5": {
        "name": "PP",
        "full": "Полипропилен",
        "recyclable": True,
        "color": "green",
        "instruction": "Сдать в пункт приёма. Хорошо промыть от остатков еды.",
        "examples": "Контейнеры для еды, крышки, стаканчики йогурта",
        "tip": "Термостойкий — используется в медицинских изделиях"
    },
    "6": {
        "name": "PS",
        "full": "Полистирол",
        "recyclable": False,
        "color": "red",
        "instruction": "Выбросить в общий мусор. Почти нигде не принимается.",
        "examples": "Пенопласт, одноразовые стаканчики, лотки",
        "tip": "Очень лёгкий и хрупкий — плохо поддаётся сортировке"
    },
    "7": {
        "name": "OTHER",
        "full": "Другие / смешанные пластики",
        "recyclable": False,
        "color": "red",
        "instruction": "Выбросить в общий мусор. Смешанный состав не перерабатывается.",
        "examples": "Многослойная упаковка, поликарбонат, нейлон",
        "tip": "Включает биопластики — проверяйте маркировку PLA/compostable"
    }
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    image_b64 = data.get("image")

    if not image_b64:
        return jsonify({"error": "Нет изображения"}), 400

    if not ROBOFLOW_API_KEY:
        return jsonify({"error": "ROBOFLOW_API_KEY не задан на сервере"}), 500

    try:
        # Отправляем в Roboflow Serverless API
        rf_url = f"https://serverless.roboflow.com/{ROBOFLOW_MODEL_ID}"
        response = requests.post(
            rf_url,
            params={"api_key": ROBOFLOW_API_KEY},
            data=image_b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        response.raise_for_status()
        predictions = response.json()

    except requests.exceptions.Timeout:
        return jsonify({"error": "Roboflow не ответил за 15 секунд. Попробуйте ещё раз."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Ошибка запроса к Roboflow: {str(e)}"}), 502

    # Парсим результат
    preds = predictions.get("predictions", [])

    if not preds:
        return jsonify({
            "found": False,
            "message": "Маркировка пластика не обнаружена. Наведите камеру ближе на треугольник со стрелками."
        })

    # Берём предсказание с наибольшей уверенностью
    best = max(preds, key=lambda p: p.get("confidence", 0))
    label = best.get("class", "").strip()
    confidence = round(best.get("confidence", 0) * 100)

    # Ищем по номеру (метка может быть "1", "PET", "resin-1" и т.д.)
    plastic_key = None
    for key in PLASTIC_INFO:
        if key in label or label.upper() in ["PET", "PETE", "HDPE", "PVC", "LDPE", "PP", "PS"]:
            if label == key:
                plastic_key = key
                break
            name = PLASTIC_INFO[key]["name"].upper()
            if label.upper() in name or name.split("/")[0].strip() == label.upper():
                plastic_key = key
                break

    # Запасной поиск по цифре в метке
    if not plastic_key:
        for char in label:
            if char in PLASTIC_INFO:
                plastic_key = char
                break

    if not plastic_key:
        return jsonify({
            "found": True,
            "raw_label": label,
            "confidence": confidence,
            "message": f"Обнаружен объект '{label}', но тип пластика не распознан. Уточните маркировку вручную."
        })

    info = PLASTIC_INFO[plastic_key]
    return jsonify({
        "found": True,
        "code": plastic_key,
        "name": info["name"],
        "full_name": info["full"],
        "recyclable": info["recyclable"],
        "color": info["color"],
        "instruction": info["instruction"],
        "examples": info["examples"],
        "tip": info["tip"],
        "confidence": confidence,
        "raw_label": label
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
