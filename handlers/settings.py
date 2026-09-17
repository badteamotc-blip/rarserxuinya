# handlers/settings.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import DEFAULT_SEARCH_LIMIT, SEARCH_LIMIT_OPTIONS, MAX_SEARCH_LIMIT
from database import Database
from globals import user_search_limits

logger = logging.getLogger(__name__)

class SettingsHandler:
    @staticmethod
    async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню настроек (из /start)"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_settings = Database.get_user_settings(user_id)
        search_limit = user_settings.get("search_limit", DEFAULT_SEARCH_LIMIT)
        
        text = f"⚙️ <b>Настройки</b>\n\n"
        text += "Выберите категорию настроек:"
        
        keyboard = [
            [InlineKeyboardButton(f"🔢 Количество результатов ({search_limit})", callback_data="change_search_limit")],
            [InlineKeyboardButton("📝 Сменить шаблон", callback_data="select_template_for_search")],
            [InlineKeyboardButton("🎯 Выбрать режим", callback_data="change_mode")],
            [InlineKeyboardButton("🔧 Управление NFT", callback_data="block_management")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    @staticmethod
    async def change_search_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Изменение количества результатов"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_settings = Database.get_user_settings(user_id)
        current_limit = user_settings.get("search_limit", DEFAULT_SEARCH_LIMIT)
        
        text = f"🔢 <b>Установите количество результатов</b>\n\n"
        text += f"Текущее значение: {current_limit}\n"
        text += f"Максимум: {MAX_SEARCH_LIMIT}\n\n"
        text += "Выберите количество:"
        
        # Создаем кнопки в 2 ряда
        keyboard = []
        row = []
        for i, limit in enumerate(SEARCH_LIMIT_OPTIONS):
            row.append(InlineKeyboardButton(str(limit), callback_data=f"set_limit_{limit}"))
            if len(row) == 3 or i == len(SEARCH_LIMIT_OPTIONS) - 1:
                keyboard.append(row)
                row = []
        
        keyboard.append([InlineKeyboardButton("🔙 Назад в настройки", callback_data="settings_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    @staticmethod
    async def handle_limit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора лимита"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Извлекаем число из callback_data
        if data.startswith("set_limit_"):
            try:
                new_limit = int(data.replace("set_limit_", ""))
                
                if new_limit < 1 or new_limit > MAX_SEARCH_LIMIT:
                    await query.answer("❌ Недопустимое значение", show_alert=True)
                    return
                
                # Сохраняем настройку в базу
                Database.update_user_setting(user_id, "search_limit", new_limit)
                # И в глобальную переменную для быстрого доступа
                user_search_limits[user_id] = new_limit
                
                await query.answer(f"✅ Установлено: {new_limit} результатов", show_alert=True)
                
                # Возвращаемся в обычные настройки
                await SettingsHandler.settings_menu(update, context)
                
            except ValueError:
                await query.answer("❌ Ошибка при установке значения", show_alert=True)

    @staticmethod
    async def settings_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат из меню изменения лимита"""
        query = update.callback_query
        await query.answer()
        
        # Возвращаемся в обычные настройки
        await SettingsHandler.settings_menu(update, context)