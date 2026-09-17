# handlers/templates.py
import logging
import globals
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import Database
from globals import waiting_for_template, user_templates

logger = logging.getLogger(__name__)

class TemplatesHandler:
    @staticmethod
    async def templates_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню шаблонов"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        templates = Database.get_user_templates(user_id)
        
        text = "📝 *Управление шаблонами*\n\n"
        
        if templates:
            text += "📋 Ваши шаблоны:\n"
            for i, template in enumerate(templates, 1):
                text += f"{i}. {template['name']}\n"
        else:
            text += "❌ У вас пока нет шаблонов\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить шаблон", callback_data="add_template_dialog")],
        ]
        
        if templates:
            keyboard.append([InlineKeyboardButton("🗑 Удалить шаблон", callback_data="delete_template_menu")])
            keyboard.append([InlineKeyboardButton("👁 Просмотреть шаблоны", callback_data="view_templates")])
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        if from_results:
            keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="templates_menu_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def templates_menu_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат из меню шаблонов"""
        query = update.callback_query
        await query.answer()
        
        from_results = context.user_data.get("from_results", False)
        if from_results:
            # Возвращаемся в результаты поиска
            await TemplatesHandler.back_to_results_search(update, context)
        else:
            # Возвращаемся в обычные настройки
            from handlers.settings import SettingsHandler
            await SettingsHandler.settings_menu(update, context)

    @staticmethod
    async def back_to_results_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возврат к результатам поиска"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем тип поиска и возвращаемся к соответствующему виду
        from handlers.search import SearchHandler
        from handlers.model_search import ModelSearchHandler
        
        # Проверяем, есть ли данные о типе поиска
        if "selected_nft" in context.user_data and context.user_data["selected_nft"]:
            # Это поиск по модели
            await ModelSearchHandler.show_search_results_page(update, context, page=0)
        else:
            # Это рандом поиск
            await SearchHandler.show_search_results_page(update, context, page=0)

    @staticmethod
    async def delete_template_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню удаления шаблонов"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        templates = Database.get_user_templates(user_id)
        
        if not templates:
            await query.answer("❌ У вас нет шаблонов", show_alert=True)
            return
        
        text = "🗑 *Выберите шаблон для удаления:*\n\n"
        for i, template in enumerate(templates, 1):
            text += f"{i}. {template['name']}\n"
        
        keyboard = []
        for i, template in enumerate(templates):
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Удалить '{template['name']}'", 
                    callback_data=f"template_delete_{i}"
                )
            ])
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        if from_results:
            keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="templates_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def delete_template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаление шаблона"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Получаем индекс из callback данных
        template_index_str = query.data.replace("template_delete_", "")
        
        try:
            template_index = int(template_index_str)
        except ValueError:
            await query.answer("❌ Ошибка: неверный индекс шаблона", show_alert=True)
            return
        
        templates = Database.get_user_templates(user_id)
        
        # Проверяем валидность индекса
        if template_index < 0 or template_index >= len(templates):
            await query.answer("❌ Шаблон не найден", show_alert=True)
            return
        
        # Удаляем шаблон
        template_name = templates[template_index]["name"]
        success, message = Database.delete_user_template(user_id, template_index)
        
        if success:
            # Удаляем из активного шаблона если нужно
            if user_id in user_templates and user_templates[user_id].get("name") == template_name:
                del user_templates[user_id]
            
            await query.answer(f"✅ Шаблон '{template_name}' удален", show_alert=True)
            # Возвращаемся в меню
            await TemplatesHandler.templates_menu_callback(update, context)
        else:
            await query.answer(f"❌ Ошибка: {message}", show_alert=True)

    @staticmethod
    async def add_template_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление шаблона через команду /addtemplate"""
        user_id = update.effective_user.id
        
        if user_id in waiting_for_template:
            await update.message.reply_text("❌ Вы уже добавляете шаблон! Закончите текущее добавление.")
            return
        
        waiting_for_template[user_id] = {"step": "name"}
        await update.message.reply_text("📝 Введите название для нового шаблона:")

    @staticmethod
    async def add_template_dialog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало добавления шаблона через callback"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if user_id in waiting_for_template:
            await query.answer("❌ Вы уже добавляете шаблон!", show_alert=True)
            return
        
        waiting_for_template[user_id] = {"step": "name"}
        await query.edit_message_text("📝 Введите название для нового шаблона:")

    @staticmethod
    async def handle_template_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сообщений для шаблонов"""
        user_id = update.effective_user.id
        
        if user_id not in waiting_for_template:
            return
        
        step_data = waiting_for_template[user_id]
        message_text = update.message.text
        
        if step_data["step"] == "name":
            if len(message_text) > 50:
                await update.message.reply_text("❌ Название слишком длинное (максимум 50 символов). Введите другое название:")
                return
                
            waiting_for_template[user_id] = {
                "step": "text", 
                "name": message_text
            }
            await update.message.reply_text("📝 Теперь введите текст шаблона:")
        
        elif step_data["step"] == "text":
            template_name = step_data["name"]
            template_text = message_text
            
            success, message = Database.add_user_template(user_id, template_name, template_text)
            del waiting_for_template[user_id]
            
            if success:
                # ОБНОВЛЕНИЕ: Сразу устанавливаем новый шаблон как активный
                user_templates[user_id] = {"name": template_name, "text": template_text}
                
                # ОБНОВЛЕНИЕ: Собираем статистику
                Database.update_user_stats(user_id, "template_created")
                
                # Проверяем откуда пришли
                from_results = context.user_data.get("from_results", False)
                
                if from_results:
                    keyboard = [
                        [InlineKeyboardButton("🔍 Начать поиск NFT", callback_data="search")],
                        [InlineKeyboardButton("📝 Управление шаблонами", callback_data="templates_menu")],
                        [InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")],
                    ]
                else:
                    keyboard = [
                        [InlineKeyboardButton("🔍 Начать поиск NFT", callback_data="search")],
                        [InlineKeyboardButton("📝 Управление шаблонами", callback_data="templates_menu")],
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ {message}\n\n"
                    f"📝 *Шаблон установлен как активный!*\n"
                    f"Теперь вы можете начать поиск NFT с вашим шаблоном!",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ {message}")

    @staticmethod
    async def select_template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор шаблона для использования"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        template_index_str = query.data.replace("select_template_", "")
        
        try:
            template_index = int(template_index_str)
        except ValueError:
            await query.answer("❌ Ошибка: неверный индекс шаблона", show_alert=True)
            return
        
        templates = Database.get_user_templates(user_id)
        
        if 0 <= template_index < len(templates):
            # ОБНОВЛЕНИЕ: Обязательно сохраняем в user_templates
            user_templates[user_id] = templates[template_index]
            template_name = templates[template_index]["name"]
            
            await query.answer(f"✅ Выбран шаблон: {template_name}", show_alert=True)
            
            # Проверяем откуда пришли
            from_results = context.user_data.get("from_results", False)
            
            if from_results:
                # Возвращаемся к результатам поиска
                await TemplatesHandler.back_to_results_search(update, context)
            else:
                # Показываем сообщение с выбранным шаблоном
                from globals import user_modes
                
                text = f"✅ *Выбран шаблон:* {template_name}\n\n"
                
                if user_id in user_modes:
                    mode_key = user_modes[user_id]
                    from config import SEARCH_MODES
                    mode_name = SEARCH_MODES[mode_key]["name"]
                    text += f"🎯 *Режим:* {mode_name}\n\n"
                    text += "Нажмите кнопку ниже чтобы начать поиск:"
                    
                    keyboard = [
                        [InlineKeyboardButton("🔍 Начать поиск NFT", callback_data="search")],
                        [InlineKeyboardButton("🎯 Сменить режим", callback_data="change_mode")],
                        [InlineKeyboardButton("📝 Сменить шаблон", callback_data="select_template_for_search")],
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
                    ]
                else:
                    text += "🎯 *Режим:* не выбран\n\n"
                    text += "Выберите режим поиска или начните поиск с текущим шаблоном:"
                    
                    keyboard = [
                        [InlineKeyboardButton("🎯 Выбрать режим", callback_data="change_mode")],
                        [InlineKeyboardButton("🔍 Начать поиск NFT", callback_data="search")],
                        [InlineKeyboardButton("📝 Сменить шаблон", callback_data="select_template_for_search")],
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        else:
            await query.answer("❌ Шаблон не найден", show_alert=True)

    @staticmethod
    async def view_templates_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр шаблонов"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        templates = Database.get_user_templates(user_id)
        
        if not templates:
            await query.answer("❌ У вас нет шаблонов", show_alert=True)
            return
        
        text = "📝 *Ваши шаблоны:*\n\n"
        for i, template in enumerate(templates, 1):
            text += f"*{i}. {template['name']}*\n"
            text += f"`{template['text']}`\n\n"
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        
        if from_results:
            keyboard = [
                [InlineKeyboardButton("🎯 Выбрать шаблон", callback_data="select_template_for_search")],
                [InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🎯 Выбрать шаблон", callback_data="select_template_for_search")],
                [InlineKeyboardButton("🔙 Назад", callback_data="templates_menu")],
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def select_template_for_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор шаблона для поиска"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        templates = Database.get_user_templates(user_id)
        
        if not templates:
            await query.answer("❌ У вас нет шаблонов", show_alert=True)
            
            # Предлагаем создать шаблон
            keyboard = [
                [InlineKeyboardButton("➕ Добавить шаблон", callback_data="add_template_dialog")],
            ]
            
            from_results = context.user_data.get("from_results", False)
            if from_results:
                keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
            else:
                keyboard.append([InlineKeyboardButton("🔙 Назад к настройкам", callback_data="settings_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ У вас пока нет шаблонов\n\nДобавьте шаблон чтобы использовать его в поиске:",
                reply_markup=reply_markup
            )
            return
        
        text = "📝 *Выберите шаблон для поиска:*\n\n"
        
        keyboard = []
        for i, template in enumerate(templates):
            keyboard.append([
                InlineKeyboardButton(
                    f"{i+1}. {template['name']}", 
                    callback_data=f"select_template_{i}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Добавить шаблон", callback_data="add_template_dialog")])
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        
        if from_results:
            keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Назад к настройкам", callback_data="back_to_current_settings")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')