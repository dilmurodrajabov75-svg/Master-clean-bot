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

ADMIN_IDS = [8554402317]
CHANNEL_ID = "@ish_keremidi"  # E'lon boradigan kanal username'si

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

users_db = {}
posts_db = {}


# --- FSM (HOLATLAR) ---
class Registration(StatesGroup):
    full_name = State()
    phone = State()
    age = State()
    gender = State()
    region = State()
    photo = State()


class JobPost(StatesGroup):
    waiting_text = State()
    waiting_workers_count = State()
    waiting_salary = State()


class WorkerApply(StatesGroup):
    waiting_location_screenshot = State()
    waiting_payment_check = State()


# --- 1. RO'YXATDAN O'TISH ---
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in users_db:
        builder = ReplyKeyboardBuilder()
        builder.button(text="📝 E'lon berish")
        builder.button(text="👤 Mening ma'lumotlarim")
        builder.adjust(1)
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz!",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
        return

    await message.answer(
        "Assalomu alaykum! Ro'yxatdan o'tish uchun Ism va familiyangizni kiriting:\n"
        "Misol: Dilmurod Rajabov"
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
    builder.button(text="👨 Erkak", callback_data="gender_Erkak")
    builder.button(text="👩 Ayol", callback_data="gender_Ayol")
    builder.adjust(2)

    await message.answer("Jinsingizni tanlang:", reply_markup=builder.as_markup())
    await state.set_state(Registration.gender)


@dp.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback.message.edit_text("Qayerdansiz? (Viloyat, tuman yoki shahar):")
    await state.set_state(Registration.region)
    await callback.answer()


@dp.message(Registration.region)
async def process_region(message: types.Message, state: FSMContext):
    await state.update_data(region=message.text)
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
        "photo": photo_id,
        "status": "Faol",
    }

    # Anketani adminga yuborish
    admin_text = (
        f"👤 **Yangi ishchi ro'yxatdan o'tdi!**\n\n"
        f"F.I.O: {data['full_name']}\n"
        f"Tel: {data['phone']}\n"
        f"Yosh: {data['age']}\n"
        f"Jins: {data['gender']}\n"
        f"Hudud: {data['region']}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=photo_id, caption=admin_text, parse_mode="Markdown")
        except Exception:
            pass

    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 E'lon berish")
    builder.button(text="👤 Mening ma'lumotlarim")
    builder.adjust(1)

    await message.answer(
        "✅ Tabriklaymiz, ro'yxatdan muvaffaqiyatli o'tdingiz!",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
    await state.clear()


# --- 2. E'LON BERISH VA AVTO HISOBLASH ---
@dp.message(F.text == "📝 E'lon berish")
async def start_job_post(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 E'lon matnini kiriting (Masalan: Ish vaqti, ovqat, manzil, avtobuslar va qo'shimcha ma'lumotlar):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(JobPost.waiting_text)


@dp.message(JobPost.waiting_text)
async def process_job_text(message: types.Message, state: FSMContext):
    await state.update_data(job_text=message.text)
    
    builder = ReplyKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=str(i))
    builder.adjust(3)
    
    await message.answer("👥 Ishga nechta odam kerak? Pastdan tugmani bosing yoki yozing:", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(JobPost.waiting_workers_count)


@dp.message(JobPost.waiting_workers_count)
async def process_workers_count(message: types.Message, state: FSMContext):
    await state.update_data(workers_count=message.text)
    await message.answer(
        "💵 **Xizmat haqqi** (ishchiga beriladigan kunlik ish haqi miqdorini raqamda kiriting, masalan: 170000):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(JobPost.waiting_salary)


@dp.message(JobPost.waiting_salary)
async def process_salary_and_publish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting (masalan: 170000):")
        return
    
    salary = int(message.text)
    
    # Avtomatik xizmat haqini belgilash (5000 dan 25000 gacha)
    if salary <= 100000:
        fee = 5000
    elif salary <= 200000:
        fee = 10000
    elif salary <= 300000:
        fee = 15000
    elif salary <= 400000:
        fee = 20000
    else:
        fee = 25000

    data = await state.get_data()
    post_id = len(posts_db) + 1
    posts_db[post_id] = {**data, "salary": salary, "fee": fee}

    # Siz so'ragan aniq ko'rinish
    channel_text = (
        f"💰 Ish haqi: {salary:,} so'm\n"
        f"📝 {data['job_text']}\n\n"
        f"🌟 Xizmat haqi: {fee:,} so'm\n"
        f"🟢 Holat: Faol\n"
        f"📅 Bugun\n"
        f"№ {post_id}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Ishga yozilish", callback_data=f"apply_{post_id}")

    try:
        sent_msg = await bot.send_message(chat_id=CHANNEL_ID, text=channel_text, reply_markup=builder.as_markup())
        posts_db[post_id]["message_id"] = sent_msg.message_id
        await message.answer("✅ E'lon muvaffaqiyatli kanalga joylandi!")
    except Exception as e:
        await message.answer(f"❌ Kanalga joylashda xatolik (Bot kanalga admin qilinganligini tekshiring): {e}")

    builder_menu = ReplyKeyboardBuilder()
    builder_menu.button(text="📝 E'lon berish")
    builder_menu.button(text="👤 Mening ma'lumotlarim")
    builder_menu.adjust(1)
    await message.answer("Asosiy menyu:", reply_markup=builder_menu.as_markup(resize_keyboard=True))
    await state.clear()


# --- 3. ISHGA YOZILISH VA LOKATSIYA ---
@dp.callback_query(F.data.startswith("apply_"))
async def apply_to_job(callback: types.CallbackQuery, state: FSMContext):
    post_id = int(callback.data.split("_")[1])
    await state.update_data(post_id=post_id)
    
    await callback.message.answer(
        "📍 Ish joyiga qanchalik yaqinligingizni bilishimiz uchun **hozirgi lokatsiyangizdan skrinshot (screenshot)** olib shu yerga yuboring:"
    )
    await state.set_state(WorkerApply.waiting_location_screenshot)
    await callback.answer()


@dp.message(WorkerApply.waiting_location_screenshot, F.photo)
async def receive_location_screenshot(message: types.Message, state: FSMContext):
    payment_text = (
        f"💳 **To'lov qilish uchun karta:**\n"
        f"`{CARD_NUMBER}`\n"
        f"Karta egasi: {CARD_OWNER}\n"
        f"📞 Operator: {PHONE_NUMBER}\n\n"
        f"⏱ **To'lov qilish uchun vaqt: 3 daqiqa!**\n"
        f"Iltimos, to'lovni amalga oshirib chekni yuboring:"
    )
    await message.answer(payment_text, parse_mode="Markdown")
    await state.set_state(WorkerApply.waiting_payment_check)


@dp.message(WorkerApply.waiting_payment_check, F.photo)
async def receive_payment_check(message: types.Message, state: FSMContext):
    check_photo = message.photo[-1].file_id
    user = message.from_user

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"adm_approve_{user.id}")
    builder.button(text="❌ Rad etish", callback_data=f"adm_reject_{user.id}")
    builder.adjust(2)

    admin_msg = (
        f"🔔 **Yangi to'lov cheki keldi!**\n\n"
        f"👤 Foydalanuvchi: {user.full_name} (@{user.username})\n"
        f"🆔 ID: {user.id}"
    )

    for admin_id in ADMIN_IDS:
        await bot.send_photo(chat_id=admin_id, photo=check_photo, caption=admin_msg, reply_markup=builder.as_markup())

    await message.answer("⏳ To'lov chekingiz adminga yuborildi. Tez orada tasdiqlanadi!")
    await state.clear()


# Admin tasdiqlashi
@dp.callback_query(F.data.startswith("adm_approve_"))
async def admin_approve(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    
    success_text = (
        f"✅ **To'lovingiz tasdiqlandi!**\n\n"
        f"📍 Manzil: Toshkent shahar\n"
        f"📞 Ish beruvchi raqami: {PHONE_NUMBER}\n"
        f"🛠 Ma'lumotlar ochildi."
    )
    await bot.send_message(chat_id=user_id, text=success_text)
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **TASDIQLANDI**")
    await callback.answer("Muvaffaqiyatli tasdiqlandi!")


@dp.callback_query(F.data.startswith("adm_reject_"))
async def admin_reject(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    await bot.send_message(chat_id=user_id, text="❌ To'lovingiz rad etildi.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **RAD ETILDI**")
    await callback.answer("Rad etildi!")


# --- PROFIL ---
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
        f"Holat: {user['status']}"
    )
    await message.answer(text, parse_mode="Markdown")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
