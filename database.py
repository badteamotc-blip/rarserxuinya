# database.py
import json
import os
import logging
from datetime import datetime, timedelta
import sqlite3
from config import USERS_FILE, BLOCKED_NFT_FILE, TEMPLATES_FILE, USER_SETTINGS_FILE, DATA_DIR, DEFAULT_SEARCH_LIMIT

logger = logging.getLogger(__name__)

class Database:
    @staticmethod
    def load_data(filename, default_value=None):
        if default_value is None:
            default_value = {}
        if os.path.exists(filename):
            try:
                # Проверяем что файл не пустой
                if os.path.getsize(filename) == 0:
                    # Создаем корректный файл если он пустой
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(default_value, f, ensure_ascii=False, indent=2)
                    return default_value
                
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки {filename}: {e}")
                # Создаем корректный файл если он поврежден
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(default_value, f, ensure_ascii=False, indent=2)
                    return default_value
                except Exception as e2:
                    logger.error(f"Ошибка создания файла {filename}: {e2}")
                    return default_value
        else:
            # Создаем файл если его нет
            try:
                os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(default_value, f, ensure_ascii=False, indent=2)
                return default_value
            except Exception as e:
                logger.error(f"Ошибка создания файла {filename}: {e}")
                return default_value

    @staticmethod
    def save_data(filename, data):
        try:
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения {filename}: {e}")
            return False

    # Пользователи
    @staticmethod
    def load_users():
        return Database.load_data(USERS_FILE, {})

    @staticmethod
    def save_users(users):
        return Database.save_data(USERS_FILE, users)

    @staticmethod
    def add_user(user_id, username, first_name, last_name=""):
        users = Database.load_users()
        user_key = str(user_id)
        if user_key not in users:
            users[user_key] = {
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'join_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            Database.save_users(users)

    # Блокировки NFT
    @staticmethod
    def load_blocked_nft():
        return Database.load_data(BLOCKED_NFT_FILE, {})

    @staticmethod
    def save_blocked_nft(blocked_nft):
        return Database.save_data(BLOCKED_NFT_FILE, blocked_nft)

    @staticmethod
    def add_blocked_nft(user_id, nft_number):
        blocked_nft = Database.load_blocked_nft()
        user_key = str(user_id)
        
        if user_key not in blocked_nft:
            blocked_nft[user_key] = []
        
        if nft_number not in blocked_nft[user_key]:
            blocked_nft[user_key].append(nft_number)
            Database.save_blocked_nft(blocked_nft)
            return True
        return False

    @staticmethod
    def remove_blocked_nft(user_id, nft_number):
        blocked_nft = Database.load_blocked_nft()
        user_key = str(user_id)
        
        if user_key in blocked_nft and nft_number in blocked_nft[user_key]:
            blocked_nft[user_key].remove(nft_number)
            Database.save_blocked_nft(blocked_nft)
            return True
        return False

    @staticmethod
    def get_blocked_nft(user_id):
        blocked_nft = Database.load_blocked_nft()
        user_key = str(user_id)
        return blocked_nft.get(user_key, [])

    # Шаблоны
    @staticmethod
    def load_templates():
        return Database.load_data(TEMPLATES_FILE, {})

    @staticmethod
    def save_templates(templates):
        return Database.save_data(TEMPLATES_FILE, templates)

    @staticmethod
    def get_user_templates(user_id):
        templates = Database.load_templates()
        user_key = str(user_id)
        return templates.get(user_key, [])

    @staticmethod
    def add_user_template(user_id, template_name, template_text):
        templates = Database.load_templates()
        user_key = str(user_id)
        
        if user_key not in templates:
            templates[user_key] = []
        
        if len(templates[user_key]) >= 10:
            return False, "❌ Превышен лимит шаблонов (максимум 10)"
        
        templates[user_key].append({
            "name": template_name,
            "text": template_text
        })
        
        Database.save_templates(templates)
        return True, "✅ Шаблон успешно добавлен!"

    @staticmethod
    def delete_user_template(user_id, template_index):
        templates = Database.load_templates()
        user_key = str(user_id)
        
        if user_key in templates and 0 <= template_index < len(templates[user_key]):
            deleted_template = templates[user_key].pop(template_index)
            Database.save_templates(templates)
            return True, f"✅ Шаблон '{deleted_template['name']}' удален"
        
        return False, "❌ Шаблон не найден"

    # Настройки пользователя
    @staticmethod
    def get_user_settings(user_id):
        """Получает настройки пользователя"""
        settings = Database.load_data(USER_SETTINGS_FILE, {})
        user_key = str(user_id)
        
        if user_key not in settings:
            from config import DEFAULT_SEARCH_LIMIT
            settings[user_key] = {"search_limit": DEFAULT_SEARCH_LIMIT}
            Database.save_data(USER_SETTINGS_FILE, settings)
        
        return settings[user_key]

    @staticmethod
    def update_user_setting(user_id, setting_key, setting_value):
        """Обновляет настройку пользователя"""
        settings = Database.load_data(USER_SETTINGS_FILE, {})
        user_key = str(user_id)
        
        if user_key not in settings:
            settings[user_key] = {}
        
        settings[user_key][setting_key] = setting_value
        Database.save_data(USER_SETTINGS_FILE, settings)
        return True

    # Статистика пользователя - НОВЫЙ ФУНКЦИОНАЛ
    @staticmethod
    def get_user_stats(user_id):
        """Получает статистику пользователя"""
        stats_file = os.path.join(DATA_DIR, "user_stats.json")
        stats = Database.load_data(stats_file, {})
        user_key = str(user_id)
        
        if user_key not in stats:
            # Создаем запись с дефолтными значениями
            stats[user_key] = {
                "searches_count": 0,
                "total_found": 0,
                "last_search": None,
                "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "templates_created": 0,
                "nft_blocked": 0,
                "active_days": 1,
                "last_active": datetime.now().strftime('%Y-%m-%d'),
                "search_history": []
            }
            Database.save_data(stats_file, stats)
        
        return stats[user_key]

    @staticmethod
    def update_user_stats(user_id, stat_type, value=None, context_data=None):
        """Обновляет статистику пользователя"""
        stats_file = os.path.join(DATA_DIR, "user_stats.json")
        stats = Database.load_data(stats_file, {})
        user_key = str(user_id)
        
        if user_key not in stats:
            # Создаем запись с дефолтными значениями
            stats[user_key] = {
                "searches_count": 0,
                "total_found": 0,
                "last_search": None,
                "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "templates_created": 0,
                "nft_blocked": 0,
                "active_days": 1,
                "last_active": datetime.now().strftime('%Y-%m-%d'),
                "search_history": []
            }
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if stat_type == "search":
            stats[user_key]["searches_count"] = stats[user_key].get("searches_count", 0) + 1
            stats[user_key]["last_search"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Добавляем в историю поиска (максимум 50 записей)
            if "search_history" not in stats[user_key]:
                stats[user_key]["search_history"] = []
            
            history_entry = {
                "date": today,
                "found_count": value if value else 0,
                "mode": context_data if context_data else "unknown",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            stats[user_key]["search_history"].append(history_entry)
            
            # Ограничиваем историю
            if len(stats[user_key]["search_history"]) > 50:
                stats[user_key]["search_history"] = stats[user_key]["search_history"][-50:]
            
        elif stat_type == "found":
            stats[user_key]["total_found"] = stats[user_key].get("total_found", 0) + (value if value else 1)
            
        elif stat_type == "template_created":
            stats[user_key]["templates_created"] = stats[user_key].get("templates_created", 0) + 1
            
        elif stat_type == "nft_blocked":
            stats[user_key]["nft_blocked"] = stats[user_key].get("nft_blocked", 0) + 1
            
        elif stat_type == "active_day":
            # Проверяем, был ли сегодня уже засчитан активный день
            if "last_active" not in stats[user_key] or stats[user_key]["last_active"] != today:
                stats[user_key]["active_days"] = stats[user_key].get("active_days", 1) + 1
                stats[user_key]["last_active"] = today
        
        Database.save_data(stats_file, stats)
        return stats[user_key]

    @staticmethod
    def get_daily_stats(user_id, days=7):
        """Получает статистику за последние N дней"""
        stats = Database.get_user_stats(user_id)
        history = stats.get("search_history", [])
        
        daily_stats = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats[date] = {
                "searches": 0,
                "found": 0
            }
        
        for entry in history:
            date = entry["date"]
            if date in daily_stats:
                daily_stats[date]["searches"] += 1
                daily_stats[date]["found"] += entry.get("found_count", 0)
        
        return daily_stats

class SessionDatabase:
    def __init__(self):
        self.db_path = os.path.join(DATA_DIR, "sessions.db")
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        os.makedirs(DATA_DIR, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для сессий Telethon
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS telethon_sessions (
                user_id INTEGER PRIMARY KEY,
                session_data BLOB,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для активных рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_campaigns (
                campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                client_user_id INTEGER,
                found_users TEXT,
                template_text TEXT,
                current_index INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES telethon_sessions (user_id)
            )
        ''')
        
        # Таблица для статистики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sending_stats (
                user_id INTEGER,
                date DATE,
                messages_sent INTEGER DEFAULT 0,
                accounts_used INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_telethon_session(self, user_id, session_data, phone_number):
        """Сохраняет сессию Telethon в базу"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO telethon_sessions 
                (user_id, session_data, phone_number, last_used)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, session_data, phone_number))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения сессии: {e}")
            return False

    def load_telethon_session(self, user_id):
        """Загружает сессию Telethon из базы"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_data, phone_number FROM telethon_sessions 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'session_data': result[0],
                    'phone_number': result[1]
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка загрузки сессии: {e}")
            return None

    def create_campaign(self, user_id, client_user_id, found_users, template_text):
        """Создает кампанию рассылки"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            found_users_json = json.dumps(found_users)
            
            cursor.execute('''
                INSERT INTO active_campaigns 
                (user_id, client_user_id, found_users, template_text)
                VALUES (?, ?, ?, ?)
            ''', (user_id, client_user_id, found_users_json, template_text))
            
            campaign_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return campaign_id
        except Exception as e:
            logger.error(f"Ошибка создания кампании: {e}")
            return None

    def update_campaign_progress(self, campaign_id, current_index, success_count, fail_count):
        """Обновляет прогресс кампании"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE active_campaigns 
                SET current_index = ?, success_count = ?, fail_count = ?
                WHERE campaign_id = ?
            ''', (current_index, success_count, fail_count, campaign_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления прогресса: {e}")
            return False

    def get_active_campaigns(self, user_id=None):
        """Получает активные кампании"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT * FROM active_campaigns 
                    WHERE user_id = ? AND status = 'active'
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT * FROM active_campaigns 
                    WHERE status = 'active'
                ''')
            
            campaigns = []
            for row in cursor.fetchall():
                campaigns.append({
                    'campaign_id': row[0],
                    'user_id': row[1],
                    'client_user_id': row[2],
                    'found_users': json.loads(row[3]),
                    'template_text': row[4],
                    'current_index': row[5],
                    'success_count': row[6],
                    'fail_count': row[7],
                    'status': row[8],
                    'created_at': row[9]
                })
            
            conn.close()
            return campaigns
        except Exception as e:
            logger.error(f"Ошибка получения кампаний: {e}")
            return []

    def complete_campaign(self, campaign_id):
        """Завершает кампанию"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE active_campaigns 
                SET status = 'completed'
                WHERE campaign_id = ?
            ''', (campaign_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка завершения кампании: {e}")
            return False

    def update_daily_stats(self, user_id, messages_sent):
        """Обновляет дневную статистику"""
        try:
            today = datetime.now().date()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO sending_stats 
                (user_id, date, messages_sent, accounts_used)
                VALUES (?, ?, ?, COALESCE(
                    (SELECT accounts_used FROM sending_stats WHERE user_id = ? AND date = ?), 0
                ) + 1)
            ''', (user_id, today, messages_sent, user_id, today))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            return False

# Глобальный экземпляр базы данных
session_db = SessionDatabase()