import requests
import logging

logger = logging.getLogger(__name__)

class ScheduleAPIClient:
    """Клиент для работы с Go backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        logger.info(f"API Client initialized with base URL: {base_url}")
    
    def get_or_create_user(self, telegram_id: int, username: str = None, first_name: str = None):
        """Получает или создает пользователя"""
        try:
            # Сначала пытаемся получить пользователя
            response = self.session.get(
                f"{self.base_url}/api/users/{telegram_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"User found: {data}")
                return {"success": True, "data": data.get("user", data)}
            
            # Если пользователь не найден (404), создаем нового
            elif response.status_code == 404:
                user_data = {
                    "telegram_id": telegram_id,
                    "username": username,
                    "first_name": first_name
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/users",
                    json=user_data,
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    logger.info(f"User created: {data}")
                    return {"success": True, "data": data.get("user", data)}
                else:
                    logger.error(f"Failed to create user: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"Create failed: {response.status_code}"}
            
            else:
                logger.error(f"Unexpected status: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_by_telegram_id(self, telegram_id: int):
        """Получает пользователя по telegram_id"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/users/{telegram_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data.get("user", data)}
            elif response.status_code == 404:
                return {"success": False, "error": "User not found"}
            else:
                return {"success": False, "error": f"Status: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return {"success": False, "error": str(e)}
    
    def create_schedule_item(self, user_id: int, day_of_week: str, time_start: str, 
                            time_end: str, subject: str, description: str = ""):
        """Создает новое занятие в расписании"""
        try:
            schedule_data = {
                "user_id": user_id,
                "day_of_week": day_of_week,
                "time_start": time_start,
                "time_end": time_end,
                "subject": subject,
                "description": description
            }
            
            response = self.session.post(
                f"{self.base_url}/api/schedule",
                json=schedule_data,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {"success": True, "data": data.get("item", data)}
            else:
                logger.error(f"Failed to create schedule: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_schedule(self, user_id: int, day_of_week: str = None):
        """Получает расписание пользователя"""
        try:
            # Сначала получаем все расписания
            response = self.session.get(
                f"{self.base_url}/api/schedule",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                all_items = data.get("items", [])
                
                # Фильтруем по user_id
                user_items = [item for item in all_items if item.get("user_id") == user_id]
                
                # Если указан день недели, фильтруем дальше
                if day_of_week:
                    user_items = [item for item in user_items if item.get("day_of_week") == day_of_week]
                
                # Сортируем по времени начала
                user_items.sort(key=lambda x: x.get("time_start", ""))
                
                return {"success": True, "data": {"items": user_items}}
            else:
                return {"success": False, "error": f"Status: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_schedule_item(self, item_id: int):
        """Удаляет занятие из расписания"""
        # Если ваш API поддерживает DELETE
        try:
            response = self.session.delete(
                f"{self.base_url}/api/schedule/{item_id}",
                timeout=5
            )
            
            if response.status_code in [200, 204]:
                return {"success": True}
            else:
                return {"success": False, "error": f"Status: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return {"success": False, "error": str(e)}