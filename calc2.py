import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Вставляем токен прямо в код
TOKEN = "8487032692:AAEo8Fs7n6h_2KS2O-aaFaxH6CBm5943OiY"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Сессии пользователей
user_data = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    user_data[message.from_user.id] = {
        "total_carbs": 0.0,
        "total_XE": 0.0,
        "total_insulin": 0.0,
        "current_product": {},
        "stage": "weight"  # ← ЭТАПЫ: weight → carbs100 → count → eat
    }

    await message.answer(
        "Привет! Я калькулятор хлебных единиц 🍞\n"
        "Введите общий вес упаковки (в граммах):"
    )

@dp.message()
async def process(message: types.Message):
    uid = message.from_user.id

    if uid not in user_data:
        await message.answer("Сначала нажмите /start")
        return

    session = user_data[uid]
    product = session["current_product"]
    text = message.text.strip().replace(",", ".")

    # Попытка привести к float
    def num():
        try:
            return float(text)
        except:
            return None

    # Логика "Ещё продукт?"
    if session.get("ask_more"):
        if text.lower() in ["да", "д", "yes", "y"]:
            session["ask_more"] = False
            session["current_product"] = {}
            session["stage"] = "weight"
            await message.answer("Введите общий вес упаковки:")
            return
        elif text.lower() in ["нет", "н", "no", "n"]:
            await message.answer(
                f"📊 ИТОГ ЗА СЕССИЮ:\n"
                f"Углеводов: {session['total_carbs']:.2f} г\n"
                f"ХЕ: {session['total_XE']:.2f}\n"
                f"Инсулин: {session['total_insulin']:.2f} ед."
            )
            user_data.pop(uid)
            return
        else:
            await message.answer("Введите 'да' или 'нет'.")
            return

    # ЭТАП 1: ВЕС
    if session["stage"] == "weight":
        val = num()
        if val is None or val <= 0:
            await message.answer("Введите корректный вес.")
            return

        product["total_weight"] = val
        session["stage"] = "carbs100"

        await message.answer("Введите количество углеводов на 100 г:")
        return

    # ЭТАП 2: УГЛЕВОДЫ
    if session["stage"] == "carbs100":
        val = num()
        if val is None or val < 0:
            await message.answer("Введите корректное число.")
            return

        product["carbs_per_100"] = val
        session["stage"] = "count"

        await message.answer("Введите количество штук в упаковке:")
        return

    # ЭТАП 3: ШТУК В УПАКОВКЕ
    if session["stage"] == "count":
        val = num()
        if val is None or val <= 0:
            await message.answer("Введите корректное число.")
            return

        product["count_in_pack"] = val
        session["stage"] = "eat"

        product["carbs_per_one"] = (
            product["total_weight"] / product["count_in_pack"]
        ) * (product["carbs_per_100"] / 100)

        await message.answer(
            f"В 1 штуке ≈ {product['carbs_per_one']:.2f} г углеводов.\n"
            f"Сколько штук вы хотите съесть?"
        )
        return

    # ЭТАП 4: СКОЛЬКО СЪЕСТЬ
    if session["stage"] == "eat":
        qty = num()
        if qty is None or qty <= 0:
            await message.answer("Введите корректное число.")
            return

        carbs = product["carbs_per_one"] * qty
        XE = carbs / 12
        insulin = XE

        # Добавляем к итогам
        session["total_carbs"] += carbs
        session["total_XE"] += XE
        session["total_insulin"] += insulin

        await message.answer(
            f"📌 Результат:\n"
            f"Углеводы: {carbs:.2f} г\n"
            f"ХЕ: {XE:.2f}\n"
            f"Инсулин: {insulin:.2f} ед.\n\n"
            f"Добавить ещё продукт? (да/нет)"
        )

        session["ask_more"] = True
        session["stage"] = "wait"
        return

async def main():
    print("Бот запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
