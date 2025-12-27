from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from api_client import ScheduleAPIClient
import keyboards as kb

router = Router()
api_client = ScheduleAPIClient()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_schedule_actions_keyboard(schedule_id: int):
    """Создает inline-кнопки для одной записи расписания"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"edit_{schedule_id}")
    builder.button(text="🗑️ Удалить", callback_data=f"delete_{schedule_id}")
    builder.adjust(2)
    return builder.as_markup()

# Состояния для создания расписания
class ScheduleForm(StatesGroup):
    day = State()
    time_start = State()
    time_end = State()
    subject = State()
    description = State()

# Состояния для редактирования (без дня недели)
class EditScheduleForm(StatesGroup):
    choosing_schedule = State()
    choosing_field = State()
    entering_value = State()
    confirm_edit = State()

# Состояния для удаления
class DeleteScheduleForm(StatesGroup):
    choosing_schedule = State()
    confirmation = State()

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
        '/update - Редактировать занятие\n' 
        '/delete - Удалить занятие\n' 
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

@router.message(F.text == 'Добавить занятие')
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
    
    # Безопасный доступ к данных пользователя
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
    
    # Отправляем заголовок дня
    await message.answer(f"📅 **{message.text}:**")
    
    # Отправляем каждое занятие отдельным сообщением с кнопками
    for i, item in enumerate(items, 1):
        # Форматируем одну запись
        item_text = f"{i}. 🕒 {item['time_start']}-{item['time_end']}\n"
        item_text += f"   📚 {item['subject']}\n"
        if item.get('description'):
            item_text += f"   📝 {item['description']}\n"
        
        # Отправляем запись с кнопками действий
        await message.answer(
            item_text,
            reply_markup=get_schedule_actions_keyboard(item['id'])
        )

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

# Главное меню
@router.message(F.text == "Главное меню")
async def back_to_main_menu(message: Message):
    await message.answer("Вы в главном меню", reply_markup=kb.main)

# ==================== УДАЛЕНИЕ ====================

# Обработчик кнопки "Удалить занятие"
@router.message(F.text == "Удалить занятие")
async def start_delete_schedule(message: Message, state: FSMContext):
    """Начинаем процесс удаления - показываем список занятий"""
    # Получаем пользователя
    user_data = api_client.get_user_by_telegram_id(message.from_user.id)
    
    if not user_data.get("success"):
        await message.answer("❌ Сначала зарегистрируйтесь через /start", reply_markup=kb.main)
        return
    
    user_id = user_data["data"]["id"]
    
    # Получаем ВСЕ занятия пользователя (без фильтра по дню)
    schedule_data = api_client.get_user_schedule(user_id)
    
    if not schedule_data.get("success") or not schedule_data.get("data", {}).get("items"):
        await message.answer("📭 У вас нет занятий для удаления", reply_markup=kb.main)
        return
    
    items = schedule_data["data"]["items"]
    
    # Формируем клавиатуру с занятиями
    builder = InlineKeyboardBuilder()
    
    day_names = {
        'monday': 'Пн', 'tuesday': 'Вт', 'wednesday': 'Ср',
        'thursday': 'Чт', 'friday': 'Пт', 'saturday': 'Сб', 
        'sunday': 'Вс'
    }
    
    for item in items:
        day_ru = day_names.get(item['day_of_week'], item['day_of_week'])
        button_text = f"{item['subject']} ({day_ru} {item['time_start']})"
        builder.button(text=button_text, callback_data=f"select_delete_{item['id']}")
    
    builder.button(text="❌ Отмена", callback_data="cancel_delete")
    builder.adjust(1)
    
    await message.answer(
        "🗑️ **Выберите занятие для удаления:**",
        reply_markup=builder.as_markup()
    )
    await state.set_state(DeleteScheduleForm.choosing_schedule)

# Обработчик выбора занятия для удаления
@router.callback_query(F.data.startswith("select_delete_"))
async def select_schedule_for_delete(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал занятие - запрашиваем подтверждение"""
    schedule_id = int(callback.data.split("_")[2])
    
    # Сохраняем ID в состоянии
    await state.update_data(schedule_id=schedule_id)
    
    # Запрашиваем подтверждение
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_delete_{schedule_id}")
    builder.button(text="❌ Нет, отменить", callback_data="cancel_delete")
    builder.adjust(2)
    
    await callback.message.answer(
        "❓ **Вы уверены, что хотите удалить это занятие?**",
        reply_markup=builder.as_markup()
    )
    await state.set_state(DeleteScheduleForm.confirmation)
    await callback.answer()

# Обработчик подтверждения удаления
@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_schedule(callback: CallbackQuery, state: FSMContext):
    """Финальное удаление занятия"""
    schedule_id = int(callback.data.split("_")[2])
    
    # Вызываем API для удаления
    result = api_client.delete_schedule_item(schedule_id)
    
    if result.get("success"):
        # Удаляем сообщение с кнопками
        await callback.message.delete()
        await callback.message.answer("✅ Занятие успешно удалено!", reply_markup=kb.main)
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await callback.message.answer(f"❌ Ошибка при удалении: {error_msg}", reply_markup=kb.main)
    
    await state.clear()
    await callback.answer()

# ==================== РЕДАКТИРОВАНИЕ (БЕЗ ДНЯ НЕДЕЛИ) ====================

# Обработчик кнопки "Редактировать занятие"
@router.message(F.text == "Редактировать занятие")
async def start_edit_schedule(message: Message, state: FSMContext):
    """Начинаем процесс редактирования - показываем список занятий"""
    # Получаем пользователя
    user_data = api_client.get_user_by_telegram_id(message.from_user.id)
    
    if not user_data.get("success"):
        await message.answer("❌ Сначала зарегистрируйтесь через /start", reply_markup=kb.main)
        return
    
    user_id = user_data["data"]["id"]
    
    # Получаем ВСЕ занятия пользователя
    schedule_data = api_client.get_user_schedule(user_id)
    
    if not schedule_data.get("success") or not schedule_data.get("data", {}).get("items"):
        await message.answer("📭 У вас нет занятий для редактирования", reply_markup=kb.main)
        return
    
    items = schedule_data["data"]["items"]
    
    # Формируем клавиатуру с занятиями
    builder = InlineKeyboardBuilder()
    
    day_names = {
        'monday': 'Пн', 'tuesday': 'Вт', 'wednesday': 'Ср',
        'thursday': 'Чт', 'friday': 'Пт', 'saturday': 'Сб', 
        'sunday': 'Вс'
    }
    
    for item in items:
        day_ru = day_names.get(item['day_of_week'], item['day_of_week'])
        button_text = f"{item['subject']} ({day_ru} {item['time_start']})"
        builder.button(text=button_text, callback_data=f"select_edit_{item['id']}")
    
    builder.button(text="❌ Отмена", callback_data="cancel_edit")
    builder.adjust(1)
    
    await message.answer(
        "✏️ **Выберите занятие для редактирования:**",
        reply_markup=builder.as_markup()
    )
    await state.set_state(EditScheduleForm.choosing_schedule)

# Обработчик выбора занятия для редактирования
@router.callback_query(F.data.startswith("select_edit_"))
async def select_schedule_for_edit(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал занятие - спрашиваем что редактировать"""
    schedule_id = int(callback.data.split("_")[2])
    
    # Сохраняем ID в состоянии
    await state.update_data(schedule_id=schedule_id)
    
    # Получаем данные занятия для отображения
    schedule_data = api_client.get_schedule_by_id(schedule_id)
    
    if not schedule_data.get("success"):
        await callback.message.answer("❌ Не удалось получить данные занятия", reply_markup=kb.main)
        await state.clear()
        return
    
    # Показываем что редактировать (БЕЗ ДНЯ НЕДЕЛИ)
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Предмет", callback_data=f"edit_field_subject")
    builder.button(text="⏰ Время начала", callback_data=f"edit_field_time_start")
    builder.button(text="⏰ Время окончания", callback_data=f"edit_field_time_end")
    builder.button(text="📝 Описание", callback_data=f"edit_field_description")
    builder.button(text="❌ Отмена", callback_data="cancel_edit")
    builder.adjust(2, 2)  # Теперь 4 кнопки в 2 строки
    
    await callback.message.answer(
        "✏️ **Что вы хотите изменить?**",
        reply_markup=builder.as_markup()
    )
    await state.set_state(EditScheduleForm.choosing_field)
    await callback.answer()

# Обработчик выбора поля для редактирования
@router.callback_query(F.data.startswith("edit_field_"))
async def choose_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал поле - запрашиваем новое значение"""
    field = callback.data.split("_")[2]
    
    # Сохраняем выбранное поле в состоянии
    await state.update_data(field_to_edit=field)
    
    # Показываем подсказку в зависимости от поля (БЕЗ ДНЯ)
    field_hints = {
        'subject': '📚 Введите новое название предмета:',
        'time_start': '⏰ Введите новое время начала (HH:MM):',
        'time_end': '⏰ Введите новое время окончания (HH:MM):',
        'description': '📝 Введите новое описание:'
    }
    
    hint = field_hints.get(field, 'Введите новое значение:')
    
    await callback.message.answer(hint, reply_markup=kb.cancel_kb)
    await state.set_state(EditScheduleForm.entering_value)
    await callback.answer()

# Обработчик ввода нового значения
@router.message(EditScheduleForm.entering_value)
async def process_new_value(message: Message, state: FSMContext):
    """Обработка нового значения для поля"""
    user_data = await state.get_data()
    field = user_data.get('field_to_edit')
    schedule_id = user_data.get('schedule_id')
    
    if not field or not schedule_id:
        await message.answer("❌ Ошибка: данные не найдены", reply_markup=kb.main)
        await state.clear()
        return
    
    new_value = message.text
    
    # Валидация только для времени (дня недели больше нет)
    if field in ['time_start', 'time_end']:
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', new_value):
            await message.answer("❌ Неверный формат времени. Используйте HH:MM")
            return
    
    # Сохраняем новое значение
    await state.update_data(new_value=new_value)
    
    # Запрашиваем подтверждение
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, сохранить", callback_data="confirm_edit")
    builder.button(text="❌ Отмена", callback_data="cancel_edit")
    builder.adjust(2)
    
    await message.answer(
        f"📝 **Подтвердите изменение:**\n"
        f"Поле: {field}\n"
        f"Новое значение: {new_value}\n\n"
        f"Сохранить изменения?",
        reply_markup=builder.as_markup()
    )
    await state.set_state(EditScheduleForm.confirm_edit)

# Обработчик подтверждения редактирования
@router.callback_query(F.data == "confirm_edit")
async def confirm_edit_schedule(callback: CallbackQuery, state: FSMContext):
    """Финальное сохранение изменений"""
    user_data = await state.get_data()
    schedule_id = user_data.get('schedule_id')
    field = user_data.get('field_to_edit')
    new_value = user_data.get('new_value')

    logger.info(f"CONFIRM EDIT: schedule_id={schedule_id}, field={field}, new_value={new_value}")
    
    if not all([schedule_id, field, new_value]):
        await callback.message.answer("❌ Ошибка: данные не найдены", reply_markup=kb.main)
        await state.clear()
        await callback.answer()
        return
    
    # Создаем данные для обновления
    update_data = {field: new_value}
    
    logger.info(f"Sending to API: {update_data}")
    
    # Вызываем API для обновления
    result = api_client.update_schedule_item(schedule_id, update_data)
    
    logger.info(f"API response: {result}")
    
    if result.get("success"):
        await callback.message.answer("✅ Изменения успешно сохранены!", reply_markup=kb.main)
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await callback.message.answer(f"❌ Ошибка при сохранении: {error_msg}", reply_markup=kb.main)
    
    await state.clear()
    await callback.answer()

# ==================== ОБЩИЕ ОБРАБОТЧИКИ ====================

# Обработчик inline-кнопки удаления (из расписания)
@router.callback_query(F.data.startswith("delete_"))
async def delete_schedule_inline(callback: CallbackQuery):
    """Удаление через inline-кнопку из расписания"""
    schedule_id = int(callback.data.split("_")[1])
    
    # Запрашиваем подтверждение
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_inline_delete_{schedule_id}")
    builder.button(text="❌ Отмена", callback_data="cancel_inline_action")
    builder.adjust(2)
    
    await callback.message.answer(
        "❓ **Удалить это занятие?**",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# Обработчик подтверждения удаления из inline
@router.callback_query(F.data.startswith("confirm_inline_delete_"))
async def confirm_inline_delete(callback: CallbackQuery):
    """Подтверждение удаления из inline-кнопки"""
    schedule_id = int(callback.data.split("_")[3])
    
    result = api_client.delete_schedule_item(schedule_id)
    
    if result.get("success"):
        await callback.message.delete()  # Удаляем сообщение с занятием
        await callback.message.answer("✅ Занятие удалено!", reply_markup=kb.main)
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        await callback.message.answer(f"❌ Ошибка: {error_msg}", reply_markup=kb.main)
    
    await callback.answer()

# Обработчик inline-кнопки редактирования (из расписания)
@router.callback_query(F.data.startswith("edit_"))
async def edit_schedule_inline(callback: CallbackQuery, state: FSMContext):
    """Редактирование через inline-кнопку из расписания"""
    schedule_id = int(callback.data.split("_")[1])
    
    # Начинаем процесс редактирования
    await state.update_data(schedule_id=schedule_id)
    
    # Показываем выбор поля для редактирования (БЕЗ ДНЯ НЕДЕЛИ)
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Предмет", callback_data=f"edit_field_subject")
    builder.button(text="⏰ Время начала", callback_data=f"edit_field_time_start")
    builder.button(text="⏰ Время окончания", callback_data=f"edit_field_time_end")
    builder.button(text="📝 Описание", callback_data=f"edit_field_description")
    builder.button(text="❌ Отмена", callback_data="cancel_inline_action")
    builder.adjust(2, 2)  # 4 кнопки в 2 строки
    
    await callback.message.answer(
        "✏️ **Что вы хотите изменить?**",
        reply_markup=builder.as_markup()
    )
    await state.set_state(EditScheduleForm.choosing_field)
    await callback.answer()

# Обработчики отмены
@router.callback_query(F.data == "cancel_delete")
@router.callback_query(F.data == "cancel_edit")
@router.callback_query(F.data == "cancel_inline_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена любого действия"""
    await callback.message.answer("❌ Действие отменено", reply_markup=kb.main)
    await state.clear()
    await callback.answer()

# Обработка любых других сообщений
@router.message()
async def handle_other_messages(message: Message):
    await message.answer(
        "🤔 Я не понял ваше сообщение.\n"
        "Используйте кнопки меню или команду /help для справки.",
        reply_markup=kb.main
    )