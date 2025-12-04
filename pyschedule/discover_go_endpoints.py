import requests

def discover_endpoints():
    base_url = "http://localhost:8080"
    
    print("🔍 Поиск endpoints Go API...")
    print("=" * 60)
    
    # Основные endpoints для проверки
    test_cases = [
        # Health и общие
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/api"),
        ("GET", "/api/"),
        
        # Пользователи
        ("GET", "/api/users"),
        ("GET", "/api/users/1005049860"),
        ("POST", "/api/users"),
        
        # Расписание
        ("GET", "/api/schedule"),
        ("GET", "/api/schedule/1005049860"),
        ("POST", "/api/schedule"),
        
        # Уроки
        ("GET", "/api/lessons"),
        ("GET", "/api/lessons/1005049860"),
        ("POST", "/api/lessons"),
        
        # Возможные варианты
        ("GET", "/api/user/1005049860/schedule"),
        ("GET", "/api/student/1005049860/schedule"),
        ("GET", "/v1/users/1005049860"),
        ("GET", "/v1/schedule/1005049860"),
    ]
    
    found_endpoints = []
    
    for method, endpoint in test_cases:
        url = base_url + endpoint
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=3)
            elif method == "POST":
                # Для POST отправляем минимальные данные
                data = {"telegram_id": 1005049860}
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=data, headers=headers, timeout=3)
            
            if response.status_code != 404:
                print(f"✅ {method} {endpoint} -> {response.status_code}")
                if response.text:
                    print(f"   Ответ: {response.text[:100]}")
                found_endpoints.append((method, endpoint, response.status_code))
            else:
                print(f"❌ {method} {endpoint} -> 404 (Не найден)")
                
        except requests.exceptions.ConnectionError:
            print(f"💥 {method} {endpoint} -> Нет подключения")
        except Exception as e:
            print(f"⚠️  {method} {endpoint} -> Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("📊 Найдены следующие endpoints:")
    for method, endpoint, status in found_endpoints:
        print(f"  {method} {endpoint} ({status})")

if __name__ == "__main__":
    discover_endpoints()