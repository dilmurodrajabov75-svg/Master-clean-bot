import logging
import asyncio
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

# Sizning Admin ID raqamingiz
ADMIN_IDS = [8554402317]
CHANNEL_ID = "@ish_keremidi"  # E'lonlar boradigan kanal username yoki ID si

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

users_db = {}

# --- HOLATLAR (FSM) ---
class Registration(StatesGroup):
    full_name = State()
    phone = State()
    age = State()
    gender = State()
    region = State()
    profession = State()
    photo = State()

class JobPost(StatesGroup):
    waiting_text = State()
    waiting_salary = State()
    waiting_screenshot = State()


# --- 1. START VA RO'YXATDAN O'TISH ---
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in users_db:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📝 E'lon berish")
        builder.button(text="👤 Mening ma'lumotlarim")
        builder.button(text="💰 Balans")
        builder.adjust(1, 2)
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz! Quyidagi tugmalar orqali xizmatlardan foydalanishingiz mumkin:",
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
    builder.button(text="📝 E'lon berish")
    builder.button(text="👤 Mening ma'lumotlarim")
    builder.button(text="💰 Balans")
    builder.adjust(1, 2)

    await message.answer(
        "✅ Tabriklaymiz, ro'yxatdan muvaffaqiyatli o'tdingiz!",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
    await state.clear()


# --- 2. E'LON BERISH JARAYONI ---
@dp.message(F.text == "📝 E'lon berish")
async def start_job_post(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 Kerakli ish bo'yicha ma'lumotlarni kiriting (masalan: Ish turi, qancha odam kerakligi, vaqt va manzil):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(JobPost.waiting_text)


@dp.message(JobPost.waiting_text)
async def process_job_text(message: types.Message, state: FSMContext):
    await state.update_data(job_text=message.text)
    await message.answer(
        "💵 **Xizmat haqqi** (ishchiga beriladigan kunlik ish haqi miqdorini) kiriting:\n"
        "Masalan: 150 000 so'm"
    )
    await state.set_state(JobPost.waiting_salary)


@dp.message(JobPost.waiting_salary)
async def process_job_salary(message: types.Message, state: FSMContext):
    await state.update_data(salary=message.text)
    
    payment_text = (
        f"💳 **To'lov qilish uchun karta:**\n"
        f"`{CARD_NUMBER}`\n"
        f"Egasi: {CARD_OWNER}\n\n"
        f"Iltimos, e'lon joylash to'lovini amalga oshiring va chek (skrinshot) rasmini yuboring:"
    )
    await message.answer(payment_text, parse_mode="Markdown")
    await state.set_state(JobPost.waiting_screenshot)


@dp.message(JobPost.waiting_screenshot, F.photo)
async def process_job_screenshot(message: types.Message, state: FSMContext):
    screenshot_id = message.photo[-1].file_id
    data = await state.get_data()
    
    user = users_db.get(message.from_user.id, {})
    phone = user.get("phone", "Ko'rsatilmagan")

    # Adminlarga tasdiqlash uchun yuborish
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}")
    builder.button(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
    builder.adjust(2)

    admin_text = (
        f"🔔 **Yangi e'lon keldi!**\n\n"
        f"👤 Yuboruvchi: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"📞 Tel: {phone}\n\n"
        f"📝 Matn: {data['job_text']}\n"
        f"💰 Xizmat haqqi: {data['salary']}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=screenshot_id, caption=admin_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Admin uchun xatolik: {e}")

    builder_menu = ReplyKeyboardBuilder()
    builder_menu.button(text="📝 E'lon berish")
    builder_menu.button(text="👤 Mening ma'lumotlarim")
    builder_menu.button(text="💰 Balans")
    builder_menu.adjust(1, 2)

    await message.answer(
        "✅ E'loningiz muvaffaqiyatli yuborildi! Tekshiruvdan so'ng kanalga chiqariladi.",
        reply_markup=builder_menu.as_markup(resize_keyboard=True)
    )
    await state.clear()


# --- 3. PROFIL VA BALANS ---
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


# --- ASOSIY MAIN ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
