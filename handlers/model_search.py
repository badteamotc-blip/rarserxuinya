# handlers/model_search.py
import logging
import random
import asyncio
import aiohttp
import time
import math
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import SEARCH_MODES, EXCLUDED_NFT, CONCURRENT_REQUESTS, HTTP_TIMEOUT, HEADERS, SEARCH_ANIMATION
from database import Database
from utils import Utils
from globals import user_cooldowns, verified_nft_cache, user_templates

logger = logging.getLogger(__name__)

class ModelSearchHandler:
    @staticmethod
    async def show_search_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает выбор типа поиска"""
        query = update.callback_query
        if query:
            await query.answer()
        
        # Сбрасываем настройки при входе в меню
        if "selected_nft" in context.user_data:
            del context.user_data["selected_nft"]
        if "available_nft" in context.user_data:
            del context.user_data["available_nft"]
        
        text = "🔍 *Выберите тип поиска:*\n\n"
        text += "🎲 *Рандом поиск* - поиск по режимам (легкий, средний, жирный)\n"
        text += "🎯 *Поиск по модели* - точный поиск по конкретным NFT\n"
        
        keyboard = [
            [InlineKeyboardButton("🎲 Рандом поиск", callback_data="random_search")],
            [InlineKeyboardButton("🎯 Поиск по модели", callback_data="model_search")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def show_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
        """Показывает выбор моделей NFT с пагинацией"""
        query = update.callback_query
        if query:
            await query.answer()
        
        # Проверяем откуда пришли
        from_results = context.user_data.get("from_results", False)
        
        # Получаем все NFT из всех режимов
        all_nft = []
        for mode_name, mode_data in SEARCH_MODES.items():
            for collection in mode_data["collections"]:
                if collection["name"] not in EXCLUDED_NFT:
                    all_nft.append({
                        "name": collection["name"],
                        "mode": mode_name,
                        "id_range": collection["id_range"],
                        "url_template": collection.get("url_template", "https://nft.ton.diamonds/api/v1/nft/{id}")
                    })
        
        # Сохраняем список NFT в контексте
        context.user_data["available_nft"] = all_nft
        if "selected_nft" not in context.user_data:
            context.user_data["selected_nft"] = []
        
        # Настройки пагинации
        items_per_page = 15
        total_pages = (len(all_nft) + items_per_page - 1) // items_per_page
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_nft = all_nft[start_idx:end_idx]
        
        selected_nft = context.user_data.get("selected_nft", [])
        selected_names = [nft["name"] for nft in selected_nft]
        
        text = f"🎯 *Выберите модели NFT для поиска (стр. {page+1}/{total_pages}):*\n\n"
        text += f"✅ Выбрано: {len(selected_nft)} моделей\n"
        text += f"📋 Всего доступно: {len(all_nft)} моделей\n\n"
        
        # Создаем клавиатуру с моделями
        keyboard = []
        
        for nft in current_nft:
            is_selected = nft["name"] in selected_names
            icon = "✅" if is_selected else "⚪"
            btn_text = f"{icon} {nft['name']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"toggle_nft_{nft['name']}")])
        
        # Кнопки пагинации
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"nft_page_{page-1}"))
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"nft_page_{page+1}"))
        
        if pagination_buttons:
            keyboard.append(pagination_buttons)
        
        # Кнопки управления
        control_buttons = []
        if selected_nft:
            control_buttons.append(InlineKeyboardButton("🔍 Начать поиск", callback_data="start_model_search"))
        
        control_buttons.append(InlineKeyboardButton("🔄 Сбросить выбор", callback_data="reset_nft_selection"))
        keyboard.append(control_buttons)
        
        # Кнопка назад в зависимости от контекста
        if from_results:
            keyboard.append([InlineKeyboardButton("🔙 Назад к результатам", callback_data="back_to_results_model")])
        else:
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="search_type_selection")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            try:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            except Exception as e:
                if "not modified" not in str(e):
                    raise e
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    @staticmethod
    async def handle_nft_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает выбор NFT"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "reset_nft_selection":
            # Сбрасываем выбор
            context.user_data["selected_nft"] = []
            await query.answer("✅ Выбор сброшен", show_alert=True)
            await ModelSearchHandler.show_model_selection(update, context, 0)
            return
        
        elif data == "start_model_search":
            # Начинаем поиск
            selected_nft = context.user_data.get("selected_nft", [])
            if not selected_nft:
                await query.answer("❌ Выберите хотя бы одну модель NFT", show_alert=True)
                return
            
            # Проверяем, что кнопка работает
            await query.answer("🔄 Запускаем поиск...")
            await ModelSearchHandler.start_model_search(update, context)
            return
        
        elif data.startswith("nft_page_"):
            # Переход по страницам
            page = int(data.replace("nft_page_", ""))
            await ModelSearchHandler.show_model_selection(update, context, page)
            return
        
        elif data.startswith("toggle_nft_"):
            # Переключение выбора NFT
            nft_name = data.replace("toggle_nft_", "")
            all_nft = context.user_data.get("available_nft", [])
            selected_nft = context.user_data.get("selected_nft", [])
            
            # Находим NFT по имени
            nft_to_toggle = None
            for nft in all_nft:
                if nft["name"] == nft_name:
                    nft_to_toggle = nft
                    break
            
            if nft_to_toggle:
                # Проверяем, выбран ли уже этот NFT
                nft_in_selected = any(s["name"] == nft_name for s in selected_nft)
                if nft_in_selected:
                    selected_nft = [s for s in selected_nft if s["name"] != nft_name]
                    await query.answer(f"❌ {nft_name} удален из выбора", show_alert=True)
                else:
                    selected_nft.append(nft_to_toggle)
                    await query.answer(f"✅ {nft_name} добавлен в выбор", show_alert=True)
                
                context.user_data["selected_nft"] = selected_nft
            
            # Получаем текущую страницу для обновления
            current_page = 0
            if "available_nft" in context.user_data:
                all_nft = context.user_data["available_nft"]
                for idx, nft in enumerate(all_nft):
                    if nft["name"] == nft_name:
                        current_page = idx // 15  # items_per_page = 15
                        break
            
            await ModelSearchHandler.show_model_selection(update, context, current_page)

    @staticmethod
    async def start_model_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запускает поиск по выбранным моделям"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Проверяем кулдаун
        from handlers.search import SearchHandler
        cooldown, remaining = SearchHandler.is_cooldown(user_id)
        if cooldown:
            await query.answer(f"⏳ Подождите {remaining} секунд", show_alert=True)
            return
        
        # Получаем выбранные NFT
        selected_nft = context.user_data.get("selected_nft", [])
        
        if not selected_nft:
            await query.answer("❌ Не выбраны модели", show_alert=True)
            return
        
        # Получаем выбранный шаблон
        template_text = "Здравствуйте, заинтересовался вашим NFT подарком, могу купить у вас его."
        template_name = "Стандартный"
        if user_id in user_templates:
            template_text = user_templates[user_id]["text"]
            template_name = user_templates[user_id]["name"]
        
        # Получаем лимит поиска для пользователя
        search_limit = SearchHandler.get_user_search_limit(user_id)
        
        # Отправляем начальное сообщение
        nft_names = ", ".join([nft["name"] for nft in selected_nft[:3]])
        if len(selected_nft) > 3:
            nft_names += f" и еще {len(selected_nft) - 3}"
        
        status_message = await query.edit_message_text(
            f"🎯 *Поиск по модели*\n"
            f"📋 Модели: {nft_names}\n"
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
                
                # Анимация поиска
                async def run_animation():
                    frame = 0
                    while len(found_nfts) < search_limit:
                        animation_frame = SEARCH_ANIMATION[frame % len(SEARCH_ANIMATION)]
                        progress = f"✅ Найдено: {len(found_nfts)}/{search_limit}"
                        text = f"🎯 *Поиск по модели*\n📋 Модели: {nft_names}\n📝 Шаблон: {template_name}\n🔢 Количество: {search_limit}\n\n{animation_frame}\n{progress}"
                        
                        try:
                            await status_message.edit_text(text, parse_mode='Markdown')
                        except:
                            pass
                        
                        frame += 1
                        await asyncio.sleep(0.5)
                
                animation_task = asyncio.create_task(run_animation())
                
                # Основной поиск
                for wave in range(15):  # Увеличиваем количество волн для большего лимита
                    if len(found_nfts) >= search_limit:
                        break
                    
                    # Создаем задачи для поиска
                    tasks = []
                    for _ in range(min(80, (search_limit - len(found_nfts)) * 5)):
                        # Выбираем случайную NFT из выбранных
                        random_nft = random.choice(selected_nft)
                        
                        # Создаем задачу используя метод из SearchHandler
                        task = SearchHandler.fetch_random_nft_fast(session, random_nft)
                        tasks.append(task)
                    
                    # Ждем завершения всех задач
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Обрабатываем результаты
                    for result in results:
                        if isinstance(result, Exception):
                            continue
                            
                        if isinstance(result, tuple) and len(result) == 2:
                            url, username = result
                            if url and username:
                                # Проверяем дубликаты
                                if not any(nft[1] == username for nft in found_nfts):
                                    found_nfts.append((url, username))
                                    if len(found_nfts) >= search_limit:
                                        break
                    
                    # Небольшая пауза между волнами
                    await asyncio.sleep(0.1)
                
                # Останавливаем анимацию
                if animation_task:
                    animation_task.cancel()
            
            search_time = int(time.time() - start_time)
            
            # СОБИРАЕМ СТАТИСТИКУ
            Database.update_user_stats(user_id, "search")
            Database.update_user_stats(user_id, "found", len(found_nfts))
            Database.update_user_stats(user_id, "active_day")
            Database.update_user_stats(user_id, "search", len(found_nfts), "model_search")
            
            # Сохраняем найденных пользователей для пагинации (как в рандом поиске)
            context.user_data["found_users"] = found_nfts
            context.user_data["current_page"] = 0
            context.user_data["search_limit"] = search_limit
            
            # Показываем результат с пагинацией (такое же меню как в рандом поиске)
            await ModelSearchHandler.show_search_results_page(update, context, page=0)
            
        except Exception as e:
            logger.error(f"Ошибка поиска по модели: {e}", exc_info=True)
            keyboard = [
                [InlineKeyboardButton("🔄 Искать снова", callback_data="model_search")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_message.edit_text(
                f"❌ Ошибка при поиске NFT\n\nДетали: {str(e)[:100]}...\n\nПопробуйте еще раз!",
                reply_markup=reply_markup
            )

    @staticmethod
    async def show_search_results_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
        """Показывает страницу с результатами поиска по модели (унифицированный вид)"""
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
        
        # Получаем информацию о выбранных моделях
        selected_nft = context.user_data.get("selected_nft", [])
        nft_names = ", ".join([nft["name"] for nft in selected_nft[:3]])
        if len(selected_nft) > 3:
            nft_names += f" и еще {len(selected_nft) - 3}"
        
        # Настройки пагинации
        items_per_page = 10  # 10 результатов на страницу (как в рандом поиске)
        total_pages = math.ceil(len(found_users) / items_per_page)
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_users = found_users[start_idx:end_idx]
        
        # Формируем текст результата (единый формат с рандом поиском)
        response_text = f"🎯 *Поиск по модели*\n"
        response_text += f"📋 Модели: {nft_names}\n"
        response_text += f"📝 Шаблон: {user_templates.get(user_id, {}).get('name', 'Стандартный')}\n\n"
        
        # Отображаем пользователей на текущей странице
        for i, (url, username) in enumerate(current_users, start_idx + 1):
            message_link = Utils.create_message_link(username, template_text)
            response_text += f'{i:2d}. {username} | <a href="{message_link}">Написать</a>\n'
        
        response_text += f"\n📊 Страница {page + 1}/{total_pages}"
        response_text += f"\n🔍 Найдено: {len(found_users)} пользователей"
        
        # Создаем клавиатуру с пагинацией (единый формат с рандом поиском)
        keyboard = []
        
        # Кнопки пагинации
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"model_results_page_{page-1}"))
        
        pagination_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
        
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"model_results_page_{page+1}"))
        
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
        """Обработчик переключения страниц результатов (для поиска по модели)"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("model_results_page_"):
            try:
                page = int(data.replace("model_results_page_", ""))
                await ModelSearchHandler.show_search_results_page(update, context, page)
            except ValueError:
                await query.answer("❌ Ошибка переключения страницы", show_alert=True)
        elif data == "current_page":
            await query.answer(f"Текущая страница", show_alert=False)