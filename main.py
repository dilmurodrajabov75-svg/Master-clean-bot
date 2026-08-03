import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = "8350987756:AAFOms_5ccVJJ873nK7FUwS8xpEyjq5DLkk"
CARD_NUMBER = "4413597600169336"
CARD_OWNER = "Dilmurod Rajabov"
PHONE_NUMBER = "+998-88-800-99-56"
ADMIN_USERNAME = "@exodus_admn"

# Admin ID raqamlari
ADMIN_IDS = [8554402317]
# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Ma'lumotlar bazasi
users_db = {}


# --- FSM (Holatlar) ---
class Registration(StatesGroup):
    full_name = State()
    phone = State()
    age = State()
    gender = State()
    region = State()
    profession = State()
    photo = State()


class JobProcess(StatesGroup):
    waiting_location_screenshot = State()
    waiting_check = State()


# --- 1. RO'YXATDAN O'TISH QISMI ---
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Agar bazada bo'lmasa, qaytadan ro'yxatdan o'tishni boshlaymiz
    if user_id in users_db:
        builder = ReplyKeyboardBuilder()
        builder.button(text="👤 Mening ma'lumotlarim")
        builder.button(text="💰 Balans")
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz!",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
        return

    await message.answer(
        "Assalomu alaykum! Ishchilar kanali rasmiy botiga xush kelibsiz.\n"
        "Ro'yxatdan o'tish uchun Ism va familiyangizni kiriting:\n"
        "Misol: Abdullayev Sardor"
    )
    await state.set_state(Registration.full_name)


@dp.message(Registration.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Telefon raqamni yuborish", request_contact=True)
    await message.answer(
        "Pastdagi tugma orqali telefon raqamingizni yuboring:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
    await state.set_state(Registration.phone)


@dp.message(Registration.phone, F.contact | F.text)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)

    await message.answer(
        "Yoshingizni kiriting (15–65):",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await state.set_state(Registration.age)


@dp.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (15 <= int(message.text) <= 65):
        await message.answer("Iltimos, yoshni to'g'ri kiriting (15-65 oralig'ida):")
        return
    await state.update_data(age=message.text)

    builder = InlineKeyboardBuilder()
    builder.button(text="👨 Erkak", callback_data="gender_male")
    builder.button(text="👩 Ayol", callback_data="gender_female")
    builder.adjust(2)

    await message.answer("Jinsingizni tanlang:", reply_markup=builder.as_markup())
    await state.set_state(Registration.gender)


@dp.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = "Erkak" if callback.data == "gender_male" else "Ayol"
    await state.update_data(gender=gender)
    await callback.message.edit_text("Qayerdansiz? (Viloyat, tuman yoki shahar):")
    await state.set_state(Registration.region)
    await callback.answer()


@dp.message(Registration.region)
async def process_region(message: types.Message, state: FSMContext):
    await state.update_data(region=message.text)
    await message.answer(
        "🛠 Qanday turdagi ishlarni bajarasiz? (Masalan: Malyar, Gipsokarton, Universal uborik va h.k.):"
    )
    await state.set_state(Registration.profession)


@dp.message(Registration.profession)
async def process_profession(message: types.Message, state: FSMContext):
    await state.update_data(profession=message.text)
    await message.answer("📷 O'zingizning 1 ta shaxsiy rasmingizni yuboring (majburiy):")
    await state.set_state(Registration.photo)


@dp.message(Registration.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()

    users_db[message.from_user.id] = {
        "full_name": data["full_name"],
        "phone": data["phone"],
        "age": data["age"],
        "gender": data["gender"],
        "region": data["region"],
        "profession": data["profession"],
        "photo": photo_id,
        "status": "Faol",
    }

    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Mening ma'lumotlarim")
    builder.button(text="💰 Balans")

    await message.answer(
        "✅ Tabriklaymiz, ro'yxatdan muvaffaqiyatli o'tdingiz!",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
    await state.clear()


# --- TUGMALAR UCHUN HANDLERLAR ---
@dp.message(F.text == "👤 Mening ma'lumotlarim")
async def show_profile(message: types.Message):
    user = users_db.get(message.from_user.id)
    if not user:
        await message.answer("Siz ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    
    text = (
        f"👤 **Sizning ma'lumotlaringiz:**\n\n"
        f"F.I.O: {user['full_name']}\n"
        f"Telefon: {user['phone']}\n"
        f"Yosh: {user['age']}\n"
        f"Jins: {user['gender']}\n"
        f"Hudud: {user['region']}\n"
        f"Mutaxassislik: {user['profession']}\n"
        f"Holat: {user['status']}"
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message(F.text == "💰 Balans")
async def show_balance(message: types.Message):
    user = users_db.get(message.from_user.id)
    if not user:
        await message.answer("Siz ro'yxatdan o'tmagansiz. /start ni bosing.")
        return
    await message.answer("💰 Sizning balansingiz: 0 so'm")


# --- ADMIN PANEL ---
@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Siz admin emassiz!")
        return
    await message.answer("Xush kelibsiz, Admin! Panel ishga tushdi.")


# --- ASOSIY MAIN FUNKSIYA ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
