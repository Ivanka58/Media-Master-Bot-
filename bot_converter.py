import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from moviepy.editor import VideoFileClip
from docx import Document
from fpdf import FPDF # Для конвертации DOCX в PDF

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Поддерживаемые форматы (для примера)
FORMATS = {
    "Документы": ["DOCX", "PDF", "TXT"],
    "Медиа": ["MP4", "MP3", "WAV"],
}

# --- СОСТОЯНИЯ FSM ---
class ConvertState(StatesGroup):
    waiting_for_action = State()
    waiting_for_input_format = State()
    waiting_for_output_format = State()
    waiting_for_file = State()

class MediaState(StatesGroup):
    waiting_for_video_audio = State()
    waiting_for_video_delete = State()

# --- ОСНОВНЫЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def start(message: Message):
    kb = [
        [types.KeyboardButton(text="Конвертировать файл")],
        [types.KeyboardButton(text="Извлечь музыку из видео")],
        [types.KeyboardButton(text="Удалить музыку из видео")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        "Привет! В этом боте ты можешь конвертировать файлы и работать с медиа!\n"
        "Воспользуйся кнопками ниже.", 
        reply_markup=keyboard
    )

# --- БЛОК КОНВЕРТАЦИИ ФАЙЛОВ ---
@dp.message(F.text == "Конвертировать файл")
async def start_convert(message: Message, state: FSMContext):
    kb = [[types.KeyboardButton(text=f)] for f in FORMATS["Документы"]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выбери начальный формат файла:", reply_markup=keyboard)
    await state.set_state(ConvertState.waiting_for_input_format)

@dp.message(ConvertState.waiting_for_input_format, F.text.in_(FORMATS["Документы"]))
async def select_output_format(message: Message, state: FSMContext):
    input_format = message.text
    await state.update_data(input_format=input_format)
    
    # Предлагаем все форматы, кроме выбранного
    output_options = [f for f in FORMATS["Документы"] if f != input_format]
    kb = [[types.KeyboardButton(text=f)] for f in output_options]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer("Теперь выбери желаемый формат файла:", reply_markup=keyboard)
    await state.set_state(ConvertState.waiting_for_output_format)

@dp.message(ConvertState.waiting_for_output_format, F.text.in_(FORMATS["Документы"]))
async def ask_for_file(message: Message, state: FSMContext):
    output_format = message.text
    await state.update_data(output_format=output_format)
    await message.answer("Теперь отправь мне файл.")
    await state.set_state(ConvertState.waiting_for_file)

@dp.message(ConvertState.waiting_for_file, F.document)
async def process_conversion(message: Message, state: FSMContext):
    data = await state.get_data()
    input_format = data['input_format'].lower()
    output_format = data['output_format'].lower()
    
    msg = await message.answer("Подождите пожалуйста...")
    
    # Скачивание файла
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    input_path = f"temp_input.{input_format}"
    output_path = f"temp_output.{output_format}"
    await bot.download_file(file.file_path, input_path)

    # --- ЛОГИКА КОНВЕРТАЦИИ (ПРИМЕР DOCX -> PDF) ---
    if input_format == 'docx' and output_format == 'pdf':
        try:
            # Здесь нужна более сложная библиотека, но для примера:
            # FPDF не умеет напрямую читать DOCX, это заглушка для демонстрации структуры
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Конвертированный документ (Имитация)", ln=1, align="C")
            pdf.output(output_path)
            
            await message.answer_document(FSInputFile(output_path), caption="Спасибо что пользуетесь нашим ботом!\nСделано @ivanka58")
        except Exception as e:
            await message.answer(f"Ошибка конвертации: {e}")
    else:
        # В реальной жизни тут будет логика для каждого формата
        await message.answer("Конвертация в этот формат пока не поддерживается.")
        
    # Очистка
    await bot.delete_message(message.chat.id, msg.message_id)
    os.remove(input_path)
    if os.path.exists(output_path):
        os.remove(output_path)
    await state.clear()


# --- БЛОК МЕДИА (ИЗВЛЕЧЕНИЕ/УДАЛЕНИЕ ЗВУКА) ---
# (Код из предыдущего сообщения, но с FSM)

@dp.message(F.text == "Извлечь музыку из видео")
async def extract_voice_start(message: Message, state: FSMContext):
    await message.answer("Отправьте видео или кружок для извлечения звука")
    await state.set_state(MediaState.waiting_for_video_audio)

@dp.message(MediaState.waiting_for_video_audio, F.video | F.video_note)
async def process_extraction(message: Message, state: FSMContext):
    msg = await message.answer("Подождите пожалуйста...")
    # ... (логика извлечения звука) ...
    # (Вставь сюда логику извлечения звука из предыдущего сообщения)
    await state.clear()

@dp.message(F.text == "Удалить музыку из видео")
async def delete_voice_start(message: Message, state: FSMContext):
    await message.answer("Отправьте ваше видео или кружок для удаления звука")
    await state.set_state(MediaState.waiting_for_video_delete)

@dp.message(MediaState.waiting_for_video_delete, F.video | F.video_note)
async def process_deletion(message: Message, state: FSMContext):
    msg = await message.answer("Подождите пожалуйста...")
    # ... (логика удаления звука) ...
    # (Вставь сюда логику удаления звука из предыдущего сообщения)
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
