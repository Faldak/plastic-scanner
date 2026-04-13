import os
import requests
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "GPKmLKlpIhdozMQ7STZs")
ROBOFLOW_MODEL_ID = os.environ.get("ROBOFLOW_MODEL_ID", "garbage-classification-3/2")

# Все возможные классы модели -> можно/нельзя переработать
CLASSES = {
    # Перерабатываемые
    "plastic":          (True,  "Пластик"),
    "plastic bottle":   (True,  "Пластиковая бутылка"),
    "bottle":           (True,  "Бутылка"),
    "cardboard":        (True,  "Картон"),
    "paper":            (True,  "Бумага"),
    "metal":            (True,  "Металл"),
    "can":              (True,  "Металлическая банка"),
    "glass":            (True,  "Стекло"),
    "glass bottle":     (True,  "Стеклянная бутылка"),
    "white-glass":      (True,  "Стекло"),
    "brown-glass":      (True,  "Стекло"),
    "green-glass":      (True,  "Стекло"),
    # Не перерабатываемые
    "trash":            (False, "Мусор"),
    "garbage":          (False, "Мусор"),
    "styrofoam":        (False, "Пенопласт"),
    "foam":             (False, "Пенопласт"),
    "plastic bag":      (False, "Пластиковый пакет"),
    "food waste":       (False, "Пищевые отходы"),
    "biodegradable":    (False, "Органика/биоотходы"),
    "biological":       (False, "Органика"),
    "diaper":           (False, "Подгузник"),
    "cigarette":        (False, "Сигарета"),
    "textile":          (False, "Текстиль"),
    # Специальная утилизация
    "battery":          (None,  "Батарейка"),
    "electronics":      (None,  "Электроника"),
    "e-waste":          (None,  "Электроника"),
    "medicine":         (None,  "Лекарства"),
}

INSTRUCTIONS = {
    True: {
        "plastic":        "Сдать в пункт приёма пластика. Ополоснуть от остатков еды.",
        "plastic bottle": "Убрать крышку, ополоснуть бутылку, сдать в пункт приёма.",
        "bottle":         "Ополоснуть и сдать в пункт приёма пластика или стекла.",
        "cardboard":      "Сложить плоско и сдать в пункт приёма картона/бумаги.",
        "paper":          "Сдать в пункт приёма макулатуры. Не мокрую и не жирную.",
        "metal":          "Сдать в пункт приёма металла или металлолом.",
        "can":            "Ополоснуть банку и сдать в пункт приёма металла.",
        "glass":          "Сдать в пункт приёма стекла. Не смешивать с битым.",
        "glass bottle":   "Убрать крышку и сдать в пункт приёма стекла.",
        "white-glass":    "Сдать в пункт приёма стекла.",
        "brown-glass":    "Сдать в пункт приёма стекла.",
        "green-glass":    "Сдать в пункт приёма стекла.",
        "default":        "Сдать в пункт приёма вторсырья.",
    },
    False: {
        "styrofoam":      "Выбросить в общий мусор. Пенопласт почти нигде не принимают.",
        "plastic bag":    "В большинстве городов не принимают. Уточните локально.",
        "biodegradable":  "В контейнер для органики или в общий мусор.",
        "biological":     "В контейнер для органики или в общий мусор.",
        "food waste":     "В контейнер для органики или компост.",
        "default":        "Выбросить в контейнер для смешанных отходов.",
    },
    None: {
        "battery":        "Сдать в пункт приёма батареек — они есть в супермаркетах!",
        "electronics":    "Сдать в пункт приёма электроники или сервисный центр.",
        "e-waste":        "Сдать в пункт приёма электроники или сервисный центр.",
        "medicine":       "Сдать в аптеку или специальный пункт утилизации лекарств.",
        "default":        "Требует специальной утилизации. Уточните в вашем городе.",
    }
}

TIPS = {
    "plastic":        "Твёрдый пластик с маркировкой #1 и #2 принимают везде",
    "plastic bottle": "Пластиковые бутылки — самый часто перерабатываемый материал",
    "cardboard":      "Картон перерабатывается до 7 раз",
    "paper":          "Из 1 тонны макулатуры получают 900 кг новой бумаги",
    "metal":          "Алюминий переплавляется бесконечно без потери качества",
    "can":            "Из переработанной банки новую делают всего за 60 дней",
    "glass":          "Стекло перерабатывается бесконечно без потери качества",
    "styrofoam":      "Пенопласт (PS #6) — один из самых сложных для переработки",
    "biodegradable":  "Органику можно компостировать дома или на даче",
    "battery":        "Одна батарейка загрязняет 20 м² земли — не выбрасывайте в мусор!",
    "electronics":    "В электронике есть золото, серебро и опасные вещества",
    "default":        "Сортировка мусора снижает нагрузку на полигоны на 30%",
}


def classify(label):
    key = label.lower().strip()
    # Точное совпадение
    if key in CLASSES:
        return key, CLASSES[key]
    # Поиск подстроки
    for k, v in CLASSES.items():
        if k in key or key in k:
            return k, v
    return key, (None, label)


def get_instruction(recyclable, key):
    group = INSTRUCTIONS.get(recyclable, {})
    return group.get(key, group.get("default", "Уточните в вашем городе."))


def get_tip(key):
    return TIPS.get(key, TIPS["default"])


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
        return jsonify({"error": "ROBOFLOW_API_KEY не задан"}), 500

    try:
        rf_url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL_ID}"
        print(f"→ {rf_url}")
        response = requests.post(
            rf_url,
            params={"api_key": ROBOFLOW_API_KEY},
            data=image_b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        print(f"Статус: {response.status_code} | {response.text[:200]}")
        response.raise_for_status()
        predictions = response.json()

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"Ошибка Roboflow: {str(e)}"}), 502

    preds = predictions.get("predictions", [])

    if not preds:
        return jsonify({
            "found": False,
            "message": "Объект не распознан. Поднесите предмет ближе и убедитесь в хорошем освещении."
        })

    best = max(preds, key=lambda p: p.get("confidence", 0))
    raw_label = best.get("class", "").strip()
    confidence = round(best.get("confidence", 0) * 100)
    print(f"Результат: {raw_label} ({confidence}%)")
    

    key, (recyclable, name_ru) = classify(raw_label)
    instruction = get_instruction(recyclable, key)
    tip = get_tip(key)

    if recyclable is True:
        verdict = "Можно переработать"
        color = "green"
    elif recyclable is False:
        verdict = "Нельзя переработать"
        color = "red"
    else:
        verdict = "Специальная утилизация"
        color = "orange"

    return jsonify({
        "found": True,
        "raw_label": raw_label,
        "name_ru": name_ru,
        "confidence": confidence,
        "recyclable": recyclable,
        "color": color,
        "verdict": verdict,
        "instruction": instruction,
        "tip": tip,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
