import json
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode, ContentType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from config import API_TOKEN, ADMIN_ID, REGISTER_LINK, CHANNEL_USERNAME
import asyncio

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Load verified users
try:
    with open("users.json", "r") as f:
        verified_users = json.load(f)
except:
    verified_users = []

# Load pending verifications
try:
    with open("pending_verifications.json", "r") as f:
        pending_verifications = json.load(f)
except:
    pending_verifications = {}

# Load prediction history to enforce daily limit
try:
    with open("prediction_log.json", "r") as f:
        prediction_log = json.load(f)
except:
    prediction_log = {}

user_verification_state = {}
user_prediction_step = {}
PREDICTION_LIMIT = 5

def is_subscribed(member):
    return member.status in ("member", "administrator", "creator")

@dp.message(Command("start"))
async def start_cmd(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Register on TashanWin", url=REGISTER_LINK)],
        [InlineKeyboardButton(text="📢 Join Prediction Channel", url=CHANNEL_USERNAME)],
        [InlineKeyboardButton(text="✅ Done", callback_data="done_register")]
    ])
    await message.answer(
        "🎉 <b>Welcome to TashanWin VIP HACK Bot📈❤️!</b>\n\n"
        "🚨 To access Vip Hack Bot💸🤑:\n"
        "1️⃣ Register From This link\n"
        "2️⃣ Deposit Minimum 500\n"
        "3️⃣ Join All The channel\n"
        "4️⃣ Click ✅ Done and send your UID and screenshot\n\n"
        "📩 After admin verification, you will get access.",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "done_register")
async def ask_uid(callback: types.CallbackQuery):
    await callback.message.answer("✅ Please send your UID (at least 5 digits):")
    await callback.answer()

@dp.message(Command("verify"))
async def manual_verify(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ You are not the admin.")
    parts = message.text.split()
    if len(parts) != 2:
        return await message.reply("Usage: /verify <user_id>")
    user_id = int(parts[1])
    if user_id not in verified_users:
        verified_users.append(user_id)
        with open("users.json", "w") as f:
            json.dump(verified_users, f)
        await message.reply(f"✅ Verified user {user_id}")
        await bot.send_message(user_id, "🎉 You have been verified by admin! Use /predict to get predictions.")
    else:
        await message.reply("✅ User already verified")

@dp.message(Command("predict"))
async def initiate_prediction(message: Message):
    user_id = str(message.from_user.id)

    if message.from_user.id not in verified_users:
        return await message.reply("❌ You are not verified. Wait for admin approval after submitting your UID and deposit proof.")

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
        if not is_subscribed(member):
            return await message.reply("🚫 You must stay subscribed to the channel to use predictions.")
    except:
        return await message.reply("⚠️ Couldn't verify your channel membership.")

    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in prediction_log:
        prediction_log[user_id] = {}
    if prediction_log[user_id].get(today, 0) >= PREDICTION_LIMIT:
        return await message.reply("⛔ You've reached your daily prediction limit.")

    user_prediction_step[message.from_user.id] = "awaiting_period"
    await message.reply("📥 Please send the last 3 digits of the current period number to receive the prediction.")

@dp.message()
async def handle_text_or_photo(message: Message):
    user_id = message.from_user.id
    uid_str = str(user_id)

    if user_id in user_prediction_step and user_prediction_step[user_id] == "awaiting_period":
        if message.text and message.text.isdigit() and len(message.text) == 3:
            digits = message.text
            user_prediction_step.pop(user_id)

            today = datetime.now().strftime("%Y-%m-%d")
            if uid_str not in prediction_log:
                prediction_log[uid_str] = {}
            prediction_log[uid_str][today] = prediction_log[uid_str].get(today, 0) + 1

            with open("prediction_log.json", "w") as f:
                json.dump(prediction_log, f)

            prediction_color, prediction_number = generate_prediction(digits)
            await message.reply(f"🎯 Prediction:\nColor: <b>{prediction_color}</b>\nNumber: <b>{prediction_number}</b>")
            return
        else:
            return await message.reply("❗ Please send exactly 3 digits.")

    if message.text and message.text.isdigit() and len(message.text) >= 5:
        user_verification_state[user_id] = message.text
        await message.reply("✅ UID received! Now send your deposit screenshot for verification.")
        return

    if message.content_type == ContentType.PHOTO and user_id in user_verification_state:
        uid = user_verification_state.pop(user_id)
        pending_verifications[str(user_id)] = uid

        with open("pending_verifications.json", "w") as f:
            json.dump(pending_verifications, f)

        await message.reply("📩 Your request is sent to admin for verification. Please wait.")
        await bot.send_message(ADMIN_ID, f"🆕 New verification pending:\nUser ID: {user_id}\nUID: {uid}")
        await message.forward(ADMIN_ID)
        return

    await message.reply("❗ Please send your UID first (at least 5 digits).")

def generate_prediction(last_digits):
    num = int(last_digits)

    # Improved logic example (basic AI pattern logic - customizable)
    if num % 10 in [0, 2, 4, 6, 8]:
        color = "🔴 RED"
        number = str((num * 3 + 7) % 100)
    else:
        color = "🟢 GREEN"
        number = str((num * 2 + 5) % 100)

    return color, number

if __name__ == "__main__":
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
