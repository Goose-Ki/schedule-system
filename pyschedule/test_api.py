from api_client import ScheduleAPIClient

api = ScheduleAPIClient()

print("=" * 60)
print("Тестирование подключения к Go API")
print("=" * 60)

# Тест 1: Получение пользователя
print("\n1. Получение пользователя (ID: 1005049860):")
result = api.get_user_by_telegram_id(1005049860)
print(f"   Успех: {result.get('success')}")
print(f"   Данные: {result.get('data')}")
print(f"   Ошибка: {result.get('error', 'Нет')}")

# Тест 2: Создание расписания (если пользователь найден)
if result.get('success'):
    user_id = result['data']['id']
    print(f"\n2. Создание занятия для user_id: {user_id}:")
    
    create_result = api.create_schedule_item(
        user_id=user_id,
        day_of_week="monday",
        time_start="10:00",
        time_end="11:30",
        subject="Тест: Математика",
        description="Тестовое занятие"
    )
    
    print(f"   Успех: {create_result.get('success')}")
    print(f"   Данные: {create_result.get('data')}")
    print(f"   Ошибка: {create_result.get('error', 'Нет')}")

# Тест 3: Получение расписания
if result.get('success'):
    print(f"\n3. Получение расписания для user_id: {user_id}:")
    schedule_result = api.get_user_schedule(user_id, "monday")
    
    print(f"   Успех: {schedule_result.get('success')}")
    print(f"   Занятий: {len(schedule_result.get('data', {}).get('items', []))}")
    print(f"   Ошибка: {schedule_result.get('error', 'Нет')}")
    
    if schedule_result.get('success') and schedule_result['data']['items']:
        print("   Пример занятия:")
        for item in schedule_result['data']['items'][:2]:  # Первые 2
            print(f"     • {item['subject']} ({item['time_start']}-{item['time_end']})")

print("\n" + "=" * 60)