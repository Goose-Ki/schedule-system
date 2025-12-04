from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# старт
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Показать расписание'), KeyboardButton(text='Экспорт расписания')],
    [KeyboardButton(text='Помощь и список команд')],
    [KeyboardButton(text='Статистика')]
],
                            resize_keyboard=True,
                            input_field_placeholder='Выберите пункт меню.')

# дни недели
dn = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Понедельник')],
    [KeyboardButton(text='Вторник')],
    [KeyboardButton(text='Среда')],
    [KeyboardButton(text='Четверг')],
    [KeyboardButton(text='Пятница')],
    [KeyboardButton(text='Суббота')],
    [KeyboardButton(text='Воскресенье')]
],
                            resize_keyboard=True,
                            input_field_placeholder='Выберите день недели.')

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='❌ Отмена')]],
    resize_keyboard=True
)