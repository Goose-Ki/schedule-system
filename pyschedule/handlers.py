from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging

from api_client import ScheduleAPIClient
import keyboards as kb

router = Router()
api_client = ScheduleAPIClient()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для создания расписания
class ScheduleForm(StatesGroup):
    day = State()
    time_start = State()
    time_end = State()
    subject = State()
    description = State()

# старт
@router.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} started bot")
    
    # Регистрируем пользователя в API
    user_data = api_client.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    logger.info(f"User data response: {user_data}")
    
    if user_data.get("success"):
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n"
            "Я бот для управления расписанием.",
            reply_markup=kb.main
        )
    else:
        await message.answer(
            "Привет! 😊\n"
            "Я бот для управления расписанием.\n"
            "⚠️ Сервер временно недоступен",
            reply_markup=kb.main
        )

# помощь
@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        '📋 **Команды бота:**\n\n'
        '/start - Запуск бота\n'
        '/create - Добавить занятие\n' 
        '/schedule - Показать расписание\n'
        '/help - Помощь\n\n'
        '⏰ **Формат времени:** HH:MM (например, 14:30)'
    )

@router.message(F.text == 'Помощь и список команд')
async def help_button(message: Message):
    await cmd_help(message)

# создание расписания
@router.message(Command('create'))
async def start_create_schedule(message: Message, state: FSMContext):
    await message.answer(
        "📅 Выберите день недели:",
        reply_markup=kb.dn
    )
    await state.set_state(ScheduleForm.day)

@router.message(ScheduleForm.day, F.text.in_(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']))
async def process_day(message: Message, state: FSMContext):
    day_mapping = {
        'Понедельник': 'monday',
        'Вторник': 'tuesday', 
        'Среда': 'wednesday',
        'Четверг': 'thursday',
        'Пятница': 'friday',
        'Суббота': 'saturday',
        'Воскресенье': 'sunday'
    }
    
    await state.update_data(day=day_mapping[message.text])
    await message.answer(
        "⏰ Введите время начала (формат HH:MM):\n"
        "Например: 09:00 или 14:30",
        reply_markup=kb.cancel_kb
    )
    await state.set_state(ScheduleForm.time_start)

@router.message(ScheduleForm.time_start, F.text.regexp(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'))
async def process_time_start(message: Message, state: FSMContext):
    await state.update_data(time_start=message.text)
    await message.answer("⏰ Введите время окончания (формат HH:MM):")
    await state.set_state(ScheduleForm.time_end)

@router.message(ScheduleForm.time_end, F.text.regexp(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'))
async def process_time_end(message: Message, state: FSMContext):
    await state.update_data(time_end=message.text)
    await message.answer("📚 Введите название предмета:")
    await state.set_state(ScheduleForm.subject)

@router.message(ScheduleForm.subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await message.answer("📝 Введите описание (или отправьте '-' чтобы пропустить):")
    await state.set_state(ScheduleForm.description)

@router.message(ScheduleForm.description)
async def process_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    description = message.text if message.text != '-' else ''
    
    # Получаем пользователя с логированием
    user_info = api_client.get_user_by_telegram_id(message.from_user.id)
    logger.info(f"User info response: {user_info}")
    
    if not user_info.get("success"):
        await message.answer("❌ Ошибка: пользователь не найден", reply_markup=kb.main)
        await state.clear()
        return
    
    # Безопасный доступ к данным пользователя
    user_data_response = user_info.get("data", {})
    user_id = user_data_response.get("id")
    
    if not user_id:
        logger.error(f"No user_id in response: {user_data_response}")
        await message.answer("❌ Ошибка: не удалось получить ID пользователя", reply_markup=kb.main)
        await state.clear()
        return
    
    logger.info(f"Creating schedule for user_id: {user_id}")
    logger.info(f"Schedule data: {user_data}")
    
    # Создаем занятие
    result = api_client.create_schedule_item(
        user_id=user_id,
        day_of_week=user_data['day'],
        time_start=user_data['time_start'],
        time_end=user_data['time_end'],
        subject=user_data['subject'],
        description=description
    )
    
    logger.info(f"Create schedule result: {result}")
    
    if result.get("success"):
        # Получаем русское название дня для ответа
        day_mapping_ru = {
            'monday': 'Понедельник',
            'tuesday': 'Вторник', 
            'wednesday': 'Среда',
            'thursday': 'Четверг',
            'friday': 'Пятница',
            'saturday': 'Суббота',
            'sunday': 'Воскресенье'
        }
        day_ru = day_mapping_ru.get(user_data['day'], user_data['day'])
        
        await message.answer(
            "✅ Занятие успешно добавлено!\n"
            f"📅 День: {day_ru}\n"
            f"⏰ Время: {user_data['time_start']}-{user_data['time_end']}\n"
            f"📚 Предмет: {user_data['subject']}",
            reply_markup=kb.main
        )
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await message.answer(
            f"❌ Ошибка: {error_msg}",
            reply_markup=kb.main
        )
    
    await state.clear()

# Отмена создания
@router.message(F.text == '❌ Отмена')
async def cancel_create(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание отменено", reply_markup=kb.main)

# расписание
@router.message(Command('schedule'))
async def show_schedule_menu(message: Message):
    await message.answer('Выберите день недели:', reply_markup=kb.dn)

@router.message(F.text == 'Показать расписание')
async def schedule_button(message: Message):
    await show_schedule_menu(message)

# Обработка выбора дня недели для просмотра
@router.message(F.text.in_(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']))
async def show_day_schedule(message: Message):
    logger.info(f"User {message.from_user.id} requested schedule for: {message.text}")
    
    day_mapping = {
        'Понедельник': 'monday',
        'Вторник': 'tuesday', 
        'Среда': 'wednesday',
        'Четверг': 'thursday',
        'Пятница': 'friday',
        'Суббота': 'saturday',
        'Воскресенье': 'sunday'
    }
    
    day_eng = day_mapping[message.text]
    
    # Получаем пользователя
    user_data = api_client.get_user_by_telegram_id(message.from_user.id)
    logger.info(f"User data for schedule: {user_data}")
    
    if not user_data.get("success"):
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    user_id = user_data["data"]["id"]
    
    # Получаем расписание
    schedule_data = api_client.get_user_schedule(user_id, day_eng)
    logger.info(f"Schedule data: {schedule_data}")
    
    if not schedule_data.get("success"):
        error_msg = schedule_data.get('error', 'Неизвестная ошибка')
        await message.answer(f"❌ Ошибка при получении расписания: {error_msg}")
        return
    
    items = schedule_data.get("data", {}).get("items", [])
    
    if not items:
        await message.answer(f"📭 На {message.text} занятий нет")
        return
    
    # Форматируем ответ
    schedule_text = f"📅 **{message.text}**:\n\n"
    
    for i, item in enumerate(items, 1):
        schedule_text += f"{i}. 🕒 {item['time_start']}-{item['time_end']}\n"
        schedule_text += f"   📚 {item['subject']}\n"
        if item.get('description'):
            schedule_text += f"   📝 {item['description']}\n"
        schedule_text += "\n"
    
    await message.answer(schedule_text)

# статистика
@router.message(Command('statistics'))
async def show_statistics(message: Message):
    # Получаем user_id
    user_data = api_client.get_user_by_telegram_id(message.from_user.id)
    
    if not user_data.get("success"):
        await message.answer("❌ Ошибка: пользователь не найден")
        return
    
    user_id = user_data["data"]["id"]
    
    # Получаем все занятия пользователя
    schedule_data = api_client.get_user_schedule(user_id)
    
    if not schedule_data.get("success"):
        await message.answer("❌ Ошибка при получении статистики")
        return
    
    items = schedule_data.get("data", {}).get("items", [])
    
    if not items:
        await message.answer("📊 У вас пока нет занятий в расписании")
        return
    
    # Считаем статистику
    total_items = len(items)
    
    # Группируем по дням
    days_count = {}
    for item in items:
        day = item['day_of_week']
        days_count[day] = days_count.get(day, 0) + 1
    
    # Форматируем статистику
    stats_text = "📊 **Ваша статистика:**\n\n"
    stats_text += f"📈 Всего занятий: {total_items}\n\n"
    
    day_names = {
        'monday': 'Понедельник', 'tuesday': 'Вторник', 'wednesday': 'Среда',
        'thursday': 'Четверг', 'friday': 'Пятница', 'saturday': 'Суббота', 
        'sunday': 'Воскресенье'
    }
    
    for day_eng, count in days_count.items():
        day_ru = day_names.get(day_eng, day_eng)
        stats_text += f"• {day_ru}: {count} занятий\n"
    
    await message.answer(stats_text)

@router.message(F.text == 'Статистика')
async def statistics_button(message: Message):
    await show_statistics(message)

# экспорт
@router.message(F.text == 'Экспорт расписания')
async def export_schedule(message: Message):
    await message.answer("📤 Функция экспорта скоро будет доступна!")

# Обработка неправильного ввода времени
@router.message(ScheduleForm.time_start)
@router.message(ScheduleForm.time_end)
async def process_time_invalid(message: Message):
    await message.answer("❌ Неверный формат времени. Используйте HH:MM (например, 09:30)")

# Обработка неправильного выбора дня
@router.message(ScheduleForm.day)
async def process_day_invalid(message: Message):
    await message.answer("❌ Пожалуйста, выберите день недели из клавиатуры")

# Обработка любых других сообщений
@router.message()
async def handle_other_messages(message: Message):
    await message.answer(
        "🤔 Я не понял ваше сообщение.\n"
        "Используйте кнопки меню или команду /help для справки.",
        reply_markup=kb.main
    )