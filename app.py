import os
import requests
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HF_API_KEY = os.environ.get("HF_API_KEY", "")

# Модель на Hugging Face — бесплатно, точно распознаёт мусор
HF_MODEL = "yangy50/garbage-classification"

RECYCLABLE = {
    "cardboard": (True,  "Картон",  "Сдать в пункт приёма бумаги/картона. Сложить плоско.", "Картон перерабатывается до 7 раз"),
    "glass":     (True,  "Стекло",  "Сдать в пункт приёма стекла. Не смешивать с битым.", "Стекло можно переплавлять бесконечно"),
    "metal":     (True,  "Металл",  "Сдать в пункт приёма металла. Ополоснуть банку.", "Алюминий переплавляется без потери качества"),
    "paper":     (True,  "Бумага",  "Сдать в пункт приёма макулатуры. Не мокрую.", "Из 1 тонны макулатуры — 900 кг новой бумаги"),
    "plastic":   (True,  "Пластик", "Сдать в пункт приёма пластика. Ополоснуть.", "Твёрдый пластик #1 и #2 принимают везде"),
    "trash":     (False, "Мусор",   "Выбросить в контейнер для смешанных отходов.", "Если сомневаетесь — в общий мусор"),
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

    try:
        import base64
        image_bytes = base64.b64decode(image_b64)

        headers = {}
        if HF_API_KEY:
            headers["Authorization"] = f"Bearer {HF_API_KEY}"

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            data=image_bytes,
            timeout=20
        )

        print(f"HF статус: {response.status_code}")
        print(f"HF ответ: {response.text[:300]}")
        response.raise_for_status()
        results = response.json()

        # HF возвращает список [{label, score}, ...]
        if isinstance(results, list) and len(results) > 0:
            best = results[0]
            label = best.get("label", "").lower().strip()
            confidence = round(best.get("score", 0) * 100)
        else:
            return jsonify({"found": False, "message": "Объект не распознан. Поднесите ближе."})

        print(f"Результат: {label} ({confidence}%)")

        if confidence < 40:
            return jsonify({
                "found": False,
                "message": f"Не уверен ({confidence}%). Поднесите предмет ближе и улучшите освещение."
            })

        info = RECYCLABLE.get(label)
        if not info:
            return jsonify({
                "found": True,
                "raw_label": label,
                "name_ru": label,
                "confidence": confidence,
                "recyclable": False,
                "color": "orange",
                "verdict": f"Обнаружен: {label}",
                "instruction": "Уточните возможность переработки в вашем городе.",
                "tip": "Если сомневаетесь — выбрасывайте в общий мусор"
            })

        recyclable, name_ru, instruction, tip = info
        return jsonify({
            "found": True,
            "raw_label": label,
            "name_ru": name_ru,
            "confidence": confidence,
            "recyclable": recyclable,
            "color": "green" if recyclable else "red",
            "verdict": "Можно переработать" if recyclable else "Нельзя переработать",
            "instruction": instruction,
            "tip": tip
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Ошибка: {str(e)}"}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
