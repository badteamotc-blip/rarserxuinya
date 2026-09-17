# handlers/search.py
import random
import time
import asyncio
import aiohttp
import logging
import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import SEARCH_MODES, SEARCH_ANIMATION, CONCURRENT_REQUESTS, HTTP_TIMEOUT, HEADERS, EXCLUDED_NFT
from database import Database
from utils import Utils
from globals import user_modes, user_cooldowns, verified_nft_cache, user_templates

logger = logging.getLogger(__name__)

class SearchHandler:
    @staticmethod
    async def show_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает выбор режима поиска"""
        query = update.callback_query
        if query:
            await query.answer()
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        
        # Определяем контекст
        is_from_random_search = False
        if query:
            message_text = query.message.text
            is_from_random_search = message_text and "Рандом поиск" in message_text
        
        text = "🎯 *Выберите режим поиска:*\n\n"
        
        for mode_key, mode_data in SEARCH_MODES.items():
            text += f"{mode_data['name']}\n"
            text += f"{mode_data['description']}\n\n"
        
        keyboard = []
        for mode_key in SEARCH_MODES.keys():
            mode_name = SEARCH_MODES[mode_key]["name"]
            keyboard.append([InlineKeyboardButton(mode_name, callback_data=f"mode_{mode_key}")])
        
        # Добавляем кнопку назад в зависимости от контекста
        if from_results:
            keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
        elif is_from_random_search:
            # Если пришли из меню выбора типа поиска (Рандом поиск)
            keyboard.append([InlineKeyboardButton("🔙 Назад к выбору типа", callback_data="search_type_selection")])
            keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def random_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /random"""
        user_id = update.effective_user.id
        from globals import user_modes
        
        if user_id not in user_modes:
            await update.message.reply_text(
                "❌ *Сначала выберите режим поиска!*\nИспользуйте команду /mode",
                parse_mode='Markdown'
            )
            return
        
        await SearchHandler.random_nft_search(update, context)

    @staticmethod
    async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора режима"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        mode_key = query.data.replace("mode_", "")
        
        if mode_key not in SEARCH_MODES:
            await query.answer("❌ Неизвестный режим")
            return
        
        # Сохраняем выбранный режим
        user_modes[user_id] = mode_key
        mode_name = SEARCH_MODES[mode_key]["name"]
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        
        # ОПРЕДЕЛЯЕМ ИСТОЧНИК ВЫЗОВА
        # Проверяем, пришли ли мы из меню выбора типа поиска или из рандом поиска
        message_text = query.message.text
        is_from_search_type = message_text and "Выберите тип поиска" in message_text
        is_from_random_search = message_text and "Выберите режим поиска" in message_text
        
        # Получаем шаблоны пользователя
        templates = Database.get_user_templates(user_id)
        
        if templates:
            # Если есть шаблоны, предлагаем выбрать
            text = f"✅ *Выбран режим:* {mode_name}\n\n"
            text += "📝 *Теперь выберите шаблон сообщения:*\n\n"
            
            keyboard = []
            for i, template in enumerate(templates):
                keyboard.append([
                    InlineKeyboardButton(
                        f"{i+1}. {template['name']}", 
                        callback_data=f"select_template_{i}"
                    )
                ])
            
            # Добавляем кнопку добавления шаблона
            keyboard.append([InlineKeyboardButton("➕ Добавить новый шаблон", callback_data="add_template_dialog")])
            keyboard.append([InlineKeyboardButton("🔍 Начать поиск со стандартным", callback_data="search_with_default")])
            
            # Кнопка назад В ЗАВИСИМОСТИ ОТ КОНТЕКСТА
            if from_results:
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="change_mode_from_results")])
                keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
            elif is_from_search_type:
                # Если пришли из меню выбора типа поиска
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="random_search")])
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
            elif is_from_random_search:
                # Если пришли из меню рандом поиска
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="change_mode")])
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
            else:
                # По умолчанию
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="change_mode")])
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            # Если шаблонов нет, используем стандартный и показываем кнопку поиска
            user_templates[user_id] = {"name": "Стандартный", "text": "Здравствуйте, заинтересовался вашим NFT подарком, могу купить у вас его."}
            
            text = f"✅ *Выбран режим:* {mode_name}\n"
            text += f"📝 *Шаблон:* Стандартный\n\n"
            text += "Нажмите кнопку ниже чтобы начать поиск:"
            
            keyboard = [
                [InlineKeyboardButton("🔍 Начать поиск NFT", callback_data="search")],
                [InlineKeyboardButton("📝 Добавить шаблон", callback_data="add_template_dialog")],
            ]
            
            # Кнопка назад В ЗАВИСИМОСТИ ОТ КОНТЕКСТА
            if from_results:
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="change_mode_from_results")])
                keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_search")])
            elif is_from_search_type:
                # Если пришли из меню выбора типа поиска
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="random_search")])
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
            elif is_from_random_search:
                # Если пришли из меню рандом поиска
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="change_mode")])
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
            else:
                # По умолчанию
                keyboard.append([InlineKeyboardButton("🔙 Назад к режимам", callback_data="change_mode")])
                keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def search_with_default_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поиск со стандартным шаблоном"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Устанавливаем стандартный шаблон
        user_templates[user_id] = {"name": "Стандартный", "text": "Здравствуйте, заинтересовался вашим NFT подарком, могу купить у вас его."}
        
        # Запускаем поиск
        await SearchHandler.random_nft_search(update, context)

    @staticmethod
    async def template_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора шаблона"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        template_index_str = query.data.replace("template_", "")
        
        try:
            template_index = int(template_index_str)
        except ValueError:
            await query.answer("❌ Ошибка: неверный индекс шаблона", show_alert=True)
            return
        
        templates = Database.get_user_templates(user_id)
        
        if 0 <= template_index < len(templates):
            user_templates[user_id] = templates[template_index]
            template_name = templates[template_index]["name"]
            template_text = templates[template_index]["text"]
            
            await query.answer(f"✅ Выбран шаблон: {template_name}", show_alert=True)
            
            # Показываем сообщение с выбранным шаблоном и кнопкой поиска
            from globals import user_modes
            
            text = f"✅ *Выбран шаблон:* {template_name}\n\n"
            text += f"📝 *Текст шаблона:*\n`{template_text}`\n\n"
            
            if user_id in user_modes:
                mode_key = user_modes[user_id]
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
    def is_cooldown(user_id: int):
        """Проверяет кулдаун пользователя"""
        now = time.time()
        if user_id in user_cooldowns:
            last_time = user_cooldowns[user_id]
            if now - last_time < 60:
                remaining = 60 - int(now - last_time)
                return True, remaining
        user_cooldowns[user_id] = now
        return False, 0

    @staticmethod
    def get_filtered_collections(user_id, mode_name=None):
        """Получает коллекции с учетом заблокированных NFT"""
        from handlers.nft_management import NFTManagementHandler
        blocked_nft = Database.get_blocked_nft(user_id)
        filtered_collections = []
        
        if mode_name and mode_name in SEARCH_MODES:
            modes_to_check = {mode_name: SEARCH_MODES[mode_name]}
        else:
            modes_to_check = SEARCH_MODES
        
        for current_mode_name, mode_data in modes_to_check.items():
            for collection in mode_data["collections"]:
                if collection["name"] not in EXCLUDED_NFT:
                    nft_info = NFTManagementHandler.get_nft_by_name_and_mode(collection["name"], current_mode_name)
                    if nft_info and nft_info["number"] not in blocked_nft:
                        filtered_collections.append(collection)
        
        return filtered_collections

    @staticmethod
    async def fetch_random_nft_fast(session: aiohttp.ClientSession, collection: dict):
        """Быстрый поиск случайного NFT"""
        collection_name = collection["name"]
        min_id, max_id = collection["id_range"]
        
        if min_id == max_id:
            random_id = random.randint(max(1, min_id - 1000), min_id + 1000)
        else:
            random_id = random.randint(min_id, max_id)
        
        url = f"https://t.me/nft/{collection_name}-{random_id}"
        
        if url in verified_nft_cache:
            return verified_nft_cache[url]
        
        try:
            html = await Utils.fetch_html_fast(session, url)
            if not html:
                verified_nft_cache[url] = None
                return None
            
            if "not be found" in html or "tgme_page_error_title" in html:
                verified_nft_cache[url] = None
                return None
            
            username = Utils.extract_real_username(html)
            
            if not username or username == "@Telegram" or username.lower() == "@m":
                verified_nft_cache[url] = None
                return None
                
            result = (url, username)
            verified_nft_cache[url] = result
            return result
            
        except Exception as e:
            logger.warning(f"Ошибка при поиске NFT {url}: {e}")
        
        verified_nft_cache[url] = None
        return None

    @staticmethod
    def get_user_search_limit(user_id):
        """Получает лимит поиска для пользователя"""
        from globals import user_search_limits
        
        # Сначала проверяем глобальные переменные
        if user_id in user_search_limits:
            return user_search_limits[user_id]
        
        # Если нет в глобальных, проверяем в базе данных
        user_settings = Database.get_user_settings(user_id)
        limit = user_settings.get("search_limit", 15)
        
        # Сохраняем в глобальные для быстрого доступа
        user_search_limits[user_id] = limit
        return limit

    @staticmethod
    async def random_nft_search(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
        """Основная функция поиска NFT"""
        user_id = update.effective_user.id
        
        # Проверяем выбран ли режим
        if user_id not in user_modes:
            # Если режим не выбран, показываем выбор режима
            if update.callback_query:
                await update.callback_query.answer("❌ Сначала выберите режим!", show_alert=True)
                await SearchHandler.show_mode_selection(update, context)
            else:
                await update.message.reply_text(
                    "❌ *Сначала выберите режим поиска!*",
                    parse_mode='Markdown'
                )
                await SearchHandler.show_mode_selection(update, context)
            return
        
        # Проверяем кулдаун
        cooldown, remaining = SearchHandler.is_cooldown(user_id)
        if cooldown:
            if update.callback_query:
                await update.callback_query.answer(f"⏳ Подождите {remaining} секунд", show_alert=True)
            return
        
        selected_mode = user_modes[user_id]
        mode_info = SEARCH_MODES[selected_mode]
        
        # Получаем выбранный шаблон - ОБНОВЛЕНИЕ: проверяем базу данных
        template_text = "Здравствуйте, заинтересовался вашим NFT подарком, могу купить у вас его."
        template_name = "Стандартный"
        
        # Проверяем сначала в user_templates
        if user_id in user_templates:
            template_text = user_templates[user_id]["text"]
            template_name = user_templates[user_id]["name"]
        else:
            # Если нет в user_templates, проверяем в базе данных
            templates = Database.get_user_templates(user_id)
            if templates:
                # Используем первый шаблон из базы
                template_text = templates[0]["text"]
                template_name = templates[0]["name"]
                # Сохраняем в user_templates для быстрого доступа
                user_templates[user_id] = {"name": template_name, "text": template_text}
        
        search_limit = SearchHandler.get_user_search_limit(user_id)
        
        # Отправляем начальное сообщение
        if update.callback_query:
            status_message = await update.callback_query.edit_message_text(
                f"🎯 Режим: {mode_info['name']}\n"
                f"📝 Шаблон: {template_name}\n"
                f"🔢 Количество: {search_limit}\n\n"
                f"{SEARCH_ANIMATION[0]}\n✅ Найдено: 0/{search_limit}",
                parse_mode='Markdown'
            )
        else:
            status_message = await update.message.reply_text(
                f"🎯 Режим: {mode_info['name']}\n"
                f"📝 Шаблон: {template_name}\n"
                f"🔢 Количество: {search_limit}\n\n"
                f"{SEARCH_ANIMATION[0]}\n✅ Найдено: 0/{search_limit}",
                parse_mode='Markdown'
            )
        
        start_time = time.time()
        found_nfts = []
        
        try:
            connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS, ssl=False)
            
            async with aiohttp.ClientSession(
                headers=HEADERS,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            ) as session:
                
                # Запускаем анимацию
                async def run_animation():
                    frame = 0
                    while len(found_nfts) < search_limit:
                        animation_frame = SEARCH_ANIMATION[frame % len(SEARCH_ANIMATION)]
                        progress = f"✅ Найдено: {len(found_nfts)}/{search_limit}"
                        text = f"🎯 Режим: {mode_info['name']}\n📝 Шаблон: {template_name}\n🔢 Количество: {search_limit}\n\n{animation_frame}\n{progress}"
                        
                        try:
                            await status_message.edit_text(text, parse_mode='Markdown')
                        except:
                            pass
                        
                        frame += 1
                        await asyncio.sleep(0.5)
                
                animation_task = asyncio.create_task(run_animation())
                
                # Получаем отфильтрованные коллекции
                collections = SearchHandler.get_filtered_collections(user_id, selected_mode)
                
                if not collections:
                    if animation_task:
                        animation_task.cancel()
                    await status_message.edit_text(
                        "❌ Все NFT в этом режиме заблокированы!\nИспользуйте /myblock для просмотра и /unblock для разблокировки."
                    )
                    return
                
                # Основной поиск
                for wave in range(15):  # Увеличиваем количество волн для большего лимита
                    if len(found_nfts) >= search_limit:
                        break
                        
                    tasks = []
                    for _ in range(min(80, (search_limit - len(found_nfts)) * 5)):
                        random_collection = random.choice(collections)
                        task = SearchHandler.fetch_random_nft_fast(session, random_collection)
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, tuple) and len(result) == 2:
                            url, username = result
                            if url and username:
                                if not any(nft[1] == username for nft in found_nfts):
                                    found_nfts.append((url, username))
                                    if len(found_nfts) >= search_limit:
                                        break
                     
                    await asyncio.sleep(0.1)

            # Останавливаем анимацию
            if animation_task:
                animation_task.cancel()
            
            search_time = int(time.time() - start_time)
            
            # СОБИРАЕМ СТАТИСТИКУ
            Database.update_user_stats(user_id, "search")
            Database.update_user_stats(user_id, "found", len(found_nfts))
            Database.update_user_stats(user_id, "active_day")
            Database.update_user_stats(user_id, "search", len(found_nfts), selected_mode)
            
            # Сохраняем найденных пользователей для пагинации
            context.user_data["found_users"] = found_nfts
            context.user_data["current_page"] = page
            context.user_data["search_limit"] = search_limit
            
            # Показываем результат с пагинацией
            await SearchHandler.show_search_results_page(update, context, page=page)
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            keyboard = [
                [InlineKeyboardButton("🔄 Искать снова", callback_data="search_again")],
                [InlineKeyboardButton("📱 Главное меню", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_message.edit_text(
                "❌ Ошибка при поиске NFT\nПопробуйте еще раз!",
                reply_markup=reply_markup
            )

    @staticmethod
    async def show_search_results_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
        """Показывает страницу с результатами поиска"""
        user_id = update.effective_user.id
        found_users = context.user_data.get("found_users", [])
        search_limit = context.user_data.get("search_limit", 15)
        
        if not found_users:
            keyboard = [
                [InlineKeyboardButton("🔄 Искать снова", callback_data="search_again")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    "❌ Нет результатов для отображения",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    "❌ Нет результатов для отображения",
                    reply_markup=reply_markup
                )
            return
        
        # Получаем выбранный шаблон
        template_text = "Здравствуйте, заинтересовался вашим NFT подарком, могу купить у вас его."
        if user_id in user_templates:
            template_text = user_templates[user_id]["text"]
        else:
            templates = Database.get_user_templates(user_id)
            if templates:
                template_text = templates[0]["text"]
        
        # Получаем информацию о режиме
        mode_name = "Неизвестный режим"
        if user_id in user_modes:
            mode_key = user_modes[user_id]
            mode_name = SEARCH_MODES[mode_key]["name"]
        
        # Настройки пагинации
        items_per_page = 10  # 10 результатов на страницу
        total_pages = math.ceil(len(found_users) / items_per_page)
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_users = found_users[start_idx:end_idx]
        
        # Формируем текст результата
        response_text = f"🎯 Режим: {mode_name}\n"
        response_text += f"📝 Шаблон: {user_templates.get(user_id, {}).get('name', 'Стандартный')}\n\n"
        
        # Отображаем пользователей на текущей странице
        for i, (url, username) in enumerate(current_users, start_idx + 1):
            message_link = Utils.create_message_link(username, template_text)
            response_text += f'{i:2d}. {username} | <a href="{message_link}">Написать</a>\n'
        
        response_text += f"\n📊 Страница {page + 1}/{total_pages}"
        response_text += f"\n🔍 Найдено: {len(found_users)} пользователей"
        
        # Создаем клавиатуру с пагинацией
        keyboard = []
        
        # Кнопки пагинации
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"random_results_page_{page-1}"))
        
        pagination_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"random_results_page_{page+1}"))
        
        if pagination_buttons:
            keyboard.append(pagination_buttons)
        
        # Основные кнопки - БЕЗ КНОПКИ НАСТРОЕК
        keyboard.extend([
            [InlineKeyboardButton("🔄 Искать снова", callback_data="search_again")],
            [InlineKeyboardButton("📱 Главное меню", callback_data="back_to_menu")],
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    response_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            except Exception as e:
                if "not modified" not in str(e):
                    await update.callback_query.answer("⚠️ Обновлено", show_alert=True)
        else:
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )

    @staticmethod
    async def handle_results_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик переключения страниц результатов"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("random_results_page_"):
            try:
                page = int(data.replace("random_results_page_", ""))
                await SearchHandler.show_search_results_page(update, context, page)
            except ValueError:
                await query.answer("❌ Ошибка переключения страницы", show_alert=True)
        elif data == "current_page":
            await query.answer(f"Текущая страница", show_alert=False)

    @staticmethod
    async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает результаты поиска с кнопкой авторассылки"""
        # Перенаправляем на первую страницу
        await SearchHandler.show_search_results_page(update, context, page=0)