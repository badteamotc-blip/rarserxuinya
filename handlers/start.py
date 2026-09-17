# handlers/start.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import REQUIRED_CHANNEL_LINK, ADMINS
from database import Database
from utils import Utils

logger = logging.getLogger(__name__)

class StartHandler:
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        Database.add_user(user.id, user.username, user.first_name, user.last_name)
        
        # ПРОВЕРКА ПОДПИСКИ
        if not await Utils.check_subscription(user.id, context):
            await Utils.require_subscription(update, context)
            return
        
        await StartHandler.show_main_menu(update, context)

    @staticmethod
    async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("🔍 Поиск NFT", callback_data="search_type_selection")],
            [InlineKeyboardButton("👤 Мой профиль", callback_data="profile_menu")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings_menu")],
            [InlineKeyboardButton("📚 Мануал по ворку", callback_data="work_manual")],
        ]
        
        if user.id in ADMINS:
            keyboard.append([InlineKeyboardButton("👨‍💻 Админ панель", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        username = f"@{user.username}" if user.username else user.first_name
        welcome_text = f"👋 Привет, {username}! Это парсер для поиска мамонтов."

        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки стартового сообщения: {e}")