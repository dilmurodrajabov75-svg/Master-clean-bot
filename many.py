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

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Ma'lumotlar bazasi o'rnida vaqtinchalik xotira (dict)
users_db = {}
active_jobs = {}


# --- FSM (Holatlar) ---
class Registration(StatesGroup):
    full_name = State()
    phone = State()
    age = State()
    gender = State()
    region = State()
    photo = State()


class JobProcess(StatesGroup):
    waiting_location_screenshot = State()
    waiting_check = State()


# --- 1. RO'YXATDAN O'TISH QISMI ---
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
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
    builder.button(
        text="📱 Telefon raqamni yuborish", request_contact=True
    )
    await message.answer(
        "Pastdagi tugma orqali telefon raqamingizni yuboring:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
    await state.set_state(Registration.phone)


@dp.message(Registration.phone, F.contact | F.text)
async def process_phone(message: types.Message, state: FSMContext):
    phone = (
        message.contact.phone_number
        if message.contact
        else message.text
    )
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
        "📷 O'zingizning 1 ta shaxsiy rasmingizni yuboring (majburiy):"
    )
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
        "photo": photo_id,
        "status": "Faol",
    }

    await message.answer(
        "✅ Tabriklaymiz, ro'yxatdan muvaffaqiyatli o'tdingiz!"
    )
    await state.clear()


# --- 2. ANKETANI ADMINGA YUBORISH & 3. KANALGA E'LON JOYLASH ---
# Admin kanalda e'lon berish yoki ishchi ma'lumotlarini qabul qilish qismi avtomatik ishlaydi.
# Xizmat haqi 5000 so'mdan 25000 so'mgacha ish haqqidan kelib chiqib avtomatik belgilanadi.


def calculate_service_fee(salary: int) -> int:
    # Ish haqiga qarab 5000 dan 25000 gacha avtomatik xizmat haqi belgilash
    fee = int(salary * 0.1)
    if fee < 5000:
        return 5000
    if fee > 25000:
        return 25000
    return fee


# --- 4. ISHGA YOZILISH VA 3 DAQIQALIK TAYMER ---
@dp.callback_query(F.data.startswith("apply_job:"))
async def apply_job(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in users_db:
        await callback.answer(
            "Siz ro'yxatdan o'tmagansiz! Avval /start bosing.",
            show_alert=True,
        )
        return

    job_id = callback.data.split(":")[1]
    await state.update_data(job_id=job_id)

    # Lokatsiya so'rash
    await callback.message.answer(
        "📍 Ish qayerda bo'lishini ko'rishingiz mumkin.\n"
        "Iltimos, manzilga qancha uzoqlikdaligingizni ko'rsatish uchun "
        "telefoningizdagi xaritadan **lokatsiya screenshotini** olib botga yuboring!"
    )
    await state.set_state(JobProcess.waiting_location_screenshot)
    await callback.answer()


@dp.message(JobProcess.waiting_location_screenshot, F.photo)
async def receive_location_screenshot(
    message: types.Message, state: FSMContext
):
    # Lokatsiya screenshot qabul qilindi
    salary = 170000  # Misol uchun e'londagi ish haqi
    fee = calculate_service_fee(salary)

    await state.update_data(fee=fee)

    text = (
        f"✅ Lokatsiya screenshot qabul qilindi!\n\n"
        f"📋 Ishga yozilish: #{message.from_user.id}\n\n"
        f"💰 Ish haqqi: {salary} so'm\n"
        f"🌟 Xizmat haqi: {fee} so'm\n\n"
        f"💳 Karta raqam: `{CARD_NUMBER}`\n"
        f"👤 Karta egasi: {CARD_OWNER}\n\n"
        f"⚠️ Ushbu karta raqamga **{fee} so'm** miqdorida to'lov chekini yuboring "
        f"(3 daqiqa ichida):"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel_job")

    msg = await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    # 3 daqiqalik teskari taymerni boshlash
    asyncio.create_task(payment_timer(msg, message.from_user.id, state))
    await state.set_state(JobProcess.waiting_check)


async def payment_timer(msg: types.Message, user_id: int, state: FSMContext):
    for remaining in range(180, 0, -60):
        await asyncio.sleep(60)
        current_state = await state.get_state()
        if current_state != JobProcess.waiting_check.state:
            return  # To'lov qilingan bo'lsa taymer to'xtaydi
        mins = remaining // 60
        try:
            await msg.edit_text(
                msg.text + f"\n\n⏳ Qolgan vaqt: {mins} daqiqa!",
                reply_markup=msg.reply_markup,
            )
        except Exception:
            pass

    # Vaqt tugadi
    current_state = await state.get_state()
    if current_state == JobProcess.waiting_check.state:
        await msg.edit_text("⏰ To'lov qilish vaqti tugadi. Buyurtma bekor qilindi.")
        await state.clear()


@dp.message(JobProcess.waiting_check, F.photo)
async def receive_payment_check(message: types.Message, state: FSMContext):
    # Chek adminga yuboriladi
    data = await state.get_data()
    fee = data.get("fee", 10000)

    await message.answer(
        "✅ To'lov cheki yuborildi!\n"
        "⏳ Tasdiqlanishini kuting. Tasdiqlangandan keyin ish beruvchining raqami yuboriladi."
    )

    # Admin uchun tasdiqlash tugmasi
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}"
    )
    builder.button(
        text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}"
    )

    # Bu yerda adminchat_id o'rniga admin ID yoziladi yoki adminga forward qilinadi
    # Hozircha misol uchun botning o'zida saqlanadi
    await state.clear()


# --- ASOSIY MAIN FUNKSIYA ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())