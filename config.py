# config.py — единый конфиг бота
import os

# Render Web Service
# PORT задаёт Render автоматически. HOST обязан быть 0.0.0.0.
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "10000"))
HEALTH_PATH = "/health"

# Пути к файлам данных
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BLOCKED_NFT_FILE = os.path.join(DATA_DIR, "blocked_nft.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")
USER_SETTINGS_FILE = os.path.join(DATA_DIR, "user_settings.json")

# Создаем папку data если ее нет
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Конфигурация бота
# Вставь сюда токен бота от @BotFather.
BOT_TOKEN = "8905795275:AAFMX9qCTX8javvHSkYH6tEp_SHhpUbDxb4"
ADMINS = [8794223703]

# Настройки группы - ОБНОВЛЕНО
REQUIRED_CHANNEL_LINK = "https://t.me/bad_team_ton"
REQUIRED_CHANNEL_ID = -1003984671410

# Настройки количества результатов
SEARCH_LIMIT_OPTIONS = [10, 15, 20, 30, 40, 50]
DEFAULT_SEARCH_LIMIT = 15
MAX_SEARCH_LIMIT = 50

# Настройки поиска
HTTP_TIMEOUT = 2.0
CONCURRENT_REQUESTS = 30
REQUEST_DELAY = 0.01

# Заголовки для запросов
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Запрещенные юзернеймы
BANNED_USERNAMES = [
    "giftstoportals", "cryptolordnn", "turbo_ultra", "ballsbank", 
    "giftrelayer", "mrktbank", "rolls_transfer", "sho_tak0e", 
    "@snoopdogg", '@gemsrelayer', "@GiftsDefender", "@gifton_transfer"
]

# Режимы поиска
SEARCH_MODES = {
    "easy": {
        "name": "🟢 Легкий режим",
        "description": "Недорогие подарки до 3 TON\nСамые неопытные пользователи",
        "collections": [
            {"name": "BDayCandle", "id_range": (20000, 30000)},
            {"name": "CandyCane", "id_range": (140000, 150000)},
            {"name": "CloverPin", "id_range": (50000, 60000)},
            {"name": "DeskCalendar", "id_range": (10000, 13000)},
            {"name": "FaithAmulet", "id_range": (50000, 60000)},
            {"name": "FreshSocks", "id_range": (90000, 100000)},
            {"name": "GingerCookie", "id_range": (50000, 60000)},
            {"name": "HappyBrownie", "id_range": (50000, 60000)},
            {"name": "HolidayDrink", "id_range": (50000, 60000)},
            {"name": "HomemadeCake", "id_range": (120000, 130000)},
            {"name": "IceCream", "id_range": (50000, 60000)},
            {"name": "InstantRamen", "id_range": (50000, 60000)},
            {"name": "JesterHat", "id_range": (50000, 60000)},
            {"name": "JingleBells", "id_range": (50000, 60000)},
            {"name": "LolPop", "id_range": (120000, 130000)},
            {"name": "LunarSnake", "id_range": (250000, 250000)},
            {"name": "PetSnake", "id_range": (554, 554)},
            {"name": "SnakeBox", "id_range": (50000, 55000)},
            {"name": "SnoopDogg", "id_range": (576241, 576241)},
            {"name": "SpicedWine", "id_range": (93557, 93557)},
            {"name": "WhipCupcake", "id_range": (160000, 170000)},
            {"name": "WinterWreath", "id_range": (65311, 65311)},
            {"name": "XmasStocking", "id_range": (177478, 177478)},
        ]
    },
    "medium": {
        "name": "🟡 Средний режим",
        "description": "Хорошие подарки от 3 до 15 TON\nБолее опытные пользователи",
        "collections": [
            {"name": "BerryBox", "id_range": (50000, 60000)},
            {"name": "BigYear", "id_range": (50000, 60000)},
            {"name": "BowTie", "id_range": (46000, 47000)},
            {"name": "BunnyMuffin", "id_range": (50000, 60000)},
            {"name": "CookieHeart", "id_range": (50000, 60000)},
            {"name": "EasterEgg", "id_range": (50000, 60000)},
            {"name": "EternalCandle", "id_range": (50000, 60000)},
            {"name": "EvilEye", "id_range": (50000, 60000)},
            {"name": "HexPot", "id_range": (40000, 50000)},
            {"name": "HypnoLollipop", "id_range": (50000, 60000)},
            {"name": "InputKey", "id_range": (70000, 80000)},
            {"name": "JackInTheBox", "id_range": (50000, 60000)},
            {"name": "JellyBunny", "id_range": (50000, 60000)},
            {"name": "JollyChimp", "id_range": (20000, 25000)},
            {"name": "JoyfulBundle", "id_range": (50000, 60000)},
            {"name": "LightSword", "id_range": (100000, 110000)},
            {"name": "LushBouquet", "id_range": (50000, 60000)},
            {"name": "MousseCake", "id_range": (119126, 119126)},
            {"name": "PartySparkler", "id_range": (161722, 161722)},
            {"name": "RestlessJar", "id_range": (22000, 23000)},
            {"name": "SantaHat", "id_range": (19289, 19289)},
            {"name": "SnoopCigar", "id_range": (50000, 60000)},
            {"name": "SnowGlobe", "id_range": (48029, 48029)},
            {"name": "SnowMittens", "id_range": (64057, 64057)},
            {"name": "SpringBasket", "id_range": (140160, 140160)},
            {"name": "SpyAgaric", "id_range": (84274, 84274)},
            {"name": "StarNotepad", "id_range": (20000, 25000)},
            {"name": "StellarRocket", "id_range": (34000, 35000)},
            {"name": "SwagBag", "id_range": (3000, 5000)},
            {"name": "TamaGadget", "id_range": (95205, 95205)},
            {"name": "ValentineBox", "id_range": (229868, 229868)},
            {"name": "WitchHat", "id_range": (6000, 7000)},
        ]
    },
    "hard": {
        "name": "🔴 Жирный режим",
        "description": "Дорогие подарки от 15 до 600 TON\nОпытные коллекционеры",
        "collections": [
            {"name": "ArtisanBrick", "id_range": (6000, 7000)},
            {"name": "AstralShard", "id_range": (50000, 60000)},
            {"name": "BondedRing", "id_range": (2000, 3000)},
            {"name": "CupidCharm", "id_range": (50000, 60000)},
            {"name": "DiamondRing", "id_range": (50000, 60000)},
            {"name": "DurovsCap", "id_range": (50000, 60000)},
            {"name": "EternalRose", "id_range": (50000, 60000)},
            {"name": "FlyingBroom", "id_range": (50000, 60000)},
            {"name": "GemSignet", "id_range": (50000, 60000)},
            {"name": "GenieLamp", "id_range": (50000, 60000)},
            {"name": "GustalBall", "id_range": (50000, 60000)},
            {"name": "HeartLocket", "id_range": (50000, 60000)},
            {"name": "HeroicHelmet", "id_range": (50000, 60000)},
            {"name": "IonGem", "id_range": (50000, 60000)},
            {"name": "IonicDryer", "id_range": (50000, 60000)},
            {"name": "KissedFrog", "id_range": (50000, 60000)},
            {"name": "LootBag", "id_range": (50000, 60000)},
            {"name": "LoveCandle", "id_range": (50000, 60000)},
            {"name": "LovePotion", "id_range": (50000, 60000)},
            {"name": "LowRider", "id_range": (50000, 60000)},
            {"name": "MadPumpkin", "id_range": (96227, 96227)},
            {"name": "MagicPotion", "id_range": (4764, 4764)},
            {"name": "MightyArm", "id_range": (150000, 150000)},
            {"name": "MiniOscar", "id_range": (4764, 4764)},
            {"name": "NailBracelet", "id_range": (119126, 119126)},
            {"name": "NekoHelmet", "id_range": (15431, 15431)},
            {"name": "PerfumeBottle", "id_range": (151632, 151632)},
            {"name": "PreciousPeach", "id_range": (2981, 2981)},
            {"name": "RecordPlayer", "id_range": (554, 554)},
            {"name": "ScaredCat", "id_range": (8029, 8029)},
            {"name": "SharpTongue", "id_range": (16430, 16430)},
            {"name": "SignetRing", "id_range": (16430, 16430)},
            {"name": "SkullFlower", "id_range": (21428, 21428)},
            {"name": "SkyStilettos", "id_range": (47465, 47465)},
            {"name": "SleighBell", "id_range": (48029, 48029)},
            {"name": "SwissWatch", "id_range": (25121, 25121)},
            {"name": "TopHat", "id_range": (32648, 32648)},
            {"name": "ToyBear", "id_range": (50000, 60000)},
            {"name": "TrappedHeart", "id_range": (24656, 24656)},
            {"name": "VintageCigar", "id_range": (17000, 18000)},
            {"name": "VoodooDoll", "id_range": (26658, 26658)},
            {"name": "WestsideSign", "id_range": (11356, 11356)},
        ]
    }
}

EXCLUDED_NFT = ["PlushPepe"]

# Анимация поиска
SEARCH_ANIMATION = [
    "🔍 ▰▱▱▱▱▱▱▱▱ Поиск NFT...",
    "🔍 ▰▰▱▱▱▱▱▱▱ Поиск NFT...", 
    "🔍 ▰▰▰▱▱▱▱▱▱ Поиск NFT...",
    "🔍 ▰▰▰▰▱▱▱▱▱ Поиск NFT...",
    "🔍 ▰▰▰▰▰▱▱▱▱ Поиск NFT...",
    "🔍 ▰▰▰▰▰▰▱▱▱ Поиск NFT...",
    "🔍 ▰▰▰▰▰▰▰▱▱ Поиск NFT...",
    "🔍 ▰▰▰▰▰▰▰▰▱ Поиск NFT...",
    "🔍 ▰▰▰▰▰▰▰▰▰ Поиск NFT...",
    "🔍 Анализ результатов..."
]