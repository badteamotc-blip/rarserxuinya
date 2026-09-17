# globals.py
# Глобальные переменные для всего бота

# Пользователи в режиме авторассылки
auto_sender_users = {}

# Данные пользователей
user_data = {}

# Кэш поиска
search_cache = {}

# Статистика бота
bot_stats = {
    'total_users': 0,
    'active_users': 0,
    'total_searches': 0
}

# Шаблоны сообщений
templates = {}

# Заблокированные NFT
blocked_nfts = {}

# Настройки пользователей
user_settings = {}

# Глобальные переменные для хранения данных
user_cooldowns = {}
user_modes = {}
waiting_for_template = {}
verified_nft_cache = {}
waiting_broadcast = {}
user_templates = {}
user_search_limits = {}  # user_id -> limit

# Новые переменные для авторассылки
auto_sender_states = {}  # user_id -> состояние авторизации
auto_sender_data = {}    # user_id -> данные для рассылки
telethon_clients = {}    # user_id -> Telethon клиент

# Статистика пользователей (кэшированная)
user_stats = {}  # user_id -> статистика