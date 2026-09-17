# main.py
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN, ADMINS, HOST, PORT, HEALTH_PATH
from handlers.start import StartHandler
from handlers.search import SearchHandler
from handlers.nft_management import NFTManagementHandler
from handlers.templates import TemplatesHandler
from handlers.admin import AdminHandler
from handlers.manuals import ManualsHandler
from handlers.model_search import ModelSearchHandler
from handlers.settings import SettingsHandler
from handlers.profile import ProfileHandler

# Импортируем глобальные переменные
import globals

# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """Минимальный HTTP endpoint для health check Render."""

    def do_GET(self):
        if self.path == HEALTH_PATH or self.path == "/":
            body = b"OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server():
    server = ThreadingHTTPServer((HOST, PORT), HealthHandler)
    logger.warning("Health server listening on %s:%s", HOST, PORT)
    server.serve_forever()


class NFTBot:
    def __init__(self):
        self.application = ApplicationBuilder().token(BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Команды
        self.application.add_handler(CommandHandler("start", StartHandler.start_command))
        self.application.add_handler(CommandHandler("profile", ProfileHandler.profile_command))
        self.application.add_handler(CommandHandler("mode", SearchHandler.show_mode_selection))
        self.application.add_handler(CommandHandler("random", SearchHandler.random_search_handler))
        self.application.add_handler(CommandHandler("nft", NFTManagementHandler.nft_command))
        self.application.add_handler(CommandHandler("block", NFTManagementHandler.block_command))
        self.application.add_handler(CommandHandler("unblock", NFTManagementHandler.unblock_command))
        self.application.add_handler(CommandHandler("myblock", NFTManagementHandler.myblock_command))
        self.application.add_handler(CommandHandler("addtemplate", TemplatesHandler.add_template_command))
        self.application.add_handler(CommandHandler("settings", SettingsHandler.settings_menu))
        
        # Команды рассылки для админов
        self.application.add_handler(CommandHandler("broadcast", AdminHandler.broadcast_command))
        self.application.add_handler(CommandHandler("bc", AdminHandler.quick_broadcast_command))
        
        # Обработчик медиа-рассылки (фото, видео, документы с подписью /broadcast)
        self.application.add_handler(MessageHandler(
            filters.CAPTION & (filters.PHOTO | filters.VIDEO | filters.Document.ALL) & filters.User(ADMINS), 
            AdminHandler.handle_media_broadcast
        ))
        
        # Сообщения для шаблонов
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            TemplatesHandler.handle_template_message
        ))
        
        # Callback'и
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        
        try:
            # Обработка проверки подписки
            if data == "check_subscription":
                from utils import Utils
                user_id = query.from_user.id
                if await Utils.check_subscription(user_id, context):
                    await query.answer("✅ Проверка пройдена! Добро пожаловать!", show_alert=True)
                    await StartHandler.start_command(update, context)
                else:
                    await query.answer("❌ Вы не подписаны на канал!", show_alert=True)
                    await Utils.require_subscription(update, context)
                return
            
            # Обработка профиля
            elif data == "profile_menu":
                await ProfileHandler.profile_callback(update, context)
            elif data == "detailed_stats":
                await ProfileHandler.detailed_stats_callback(update, context)
            elif data == "weekly_stats":
                await ProfileHandler.weekly_stats_callback(update, context)
            elif data == "quick_settings":
                await ProfileHandler.quick_settings_callback(update, context)
            
            # Обработка callback'ов шаблонов
            elif data == "templates_menu":
                await TemplatesHandler.templates_menu_callback(update, context)
            elif data == "delete_template_menu":
                await TemplatesHandler.delete_template_menu_callback(update, context)
            elif data.startswith("template_delete_"):
                await TemplatesHandler.delete_template_callback(update, context)
            elif data.startswith("select_template_"):
                await TemplatesHandler.select_template_callback(update, context)
            elif data == "add_template_dialog":
                await TemplatesHandler.add_template_dialog_callback(update, context)
            elif data == "view_templates":
                await TemplatesHandler.view_templates_callback(update, context)
            elif data == "select_template_for_search":
                # Сбрасываем флаг from_results для обычных настроек
                context.user_data["from_results"] = False
                await TemplatesHandler.select_template_for_search_callback(update, context)
            elif data == "select_template_for_search_from_results":
                # Устанавливаем флаг from_results для настроек из результатов
                context.user_data["from_results"] = True
                await TemplatesHandler.select_template_for_search_callback(update, context)
            elif data == "back_to_current_settings":
                # Возврат из выбора шаблона в обычные настройки
                await SettingsHandler.settings_menu(update, context)
            elif data == "templates_menu_back":
                await TemplatesHandler.templates_menu_back(update, context)
            elif data == "back_to_results_search":
                # Возврат к результатам поиска
                await TemplatesHandler.back_to_results_search(update, context)
            
            # Обработка callback'ов админ-панели
            elif data == "admin_panel":
                await AdminHandler.admin_panel_callback(update, context)
            elif data == "admin_stats":
                await AdminHandler.admin_stats_callback(update, context)
            elif data == "admin_clear_cache":
                await AdminHandler.admin_clear_cache_callback(update, context)
            elif data == "admin_broadcast_info":
                await AdminHandler.admin_broadcast_info_callback(update, context)
            
            # Обработка callback'ов настроек
            elif data == "settings_menu":
                await SettingsHandler.settings_menu(update, context)
            elif data == "change_search_limit":
                context.user_data["from_results"] = False
                await SettingsHandler.change_search_limit(update, context)
            elif data.startswith("set_limit_"):
                await SettingsHandler.handle_limit_selection(update, context)
            elif data == "settings_back":
                await SettingsHandler.settings_menu(update, context)
            
            # Обработка поиска и режимов
            elif data.startswith("mode_"):
                await SearchHandler.mode_callback(update, context)
            elif data == "search" or data == "search_again":
                await SearchHandler.random_nft_search(update, context)
            elif data == "change_mode":
                # Сбрасываем флаг from_results для обычных настроек
                context.user_data["from_results"] = False
                await SearchHandler.show_mode_selection(update, context)
            elif data == "change_mode_from_results":
                # Устанавливаем флаг from_results для настроек из результатов
                context.user_data["from_results"] = True
                await SearchHandler.show_mode_selection(update, context)
            elif data == "search_with_default":
                await SearchHandler.search_with_default_callback(update, context)
            
            # Обработка NFT менеджмента
            elif data == "nft_list":
                await NFTManagementHandler.nft_command(update, context)
            elif data == "block_management":
                # Сбрасываем флаг from_results для обычных настроек
                context.user_data["from_results"] = False
                await NFTManagementHandler.block_management_callback(update, context)
            elif data == "block_management_from_results":
                # Устанавливаем флаг from_results для настроек из результатов
                context.user_data["from_results"] = True
                await NFTManagementHandler.block_management_callback(update, context)
            elif data == "myblock_list":
                await NFTManagementHandler.myblock_command(update, context)
            elif data.startswith("block_"):
                await NFTManagementHandler.block_nft_callback(update, context)
            elif data == "block_nft_menu":
                # Показываем список NFT для блокировки
                await NFTManagementHandler.nft_command(update, context)
            elif data == "unblock_nft_menu":
                # Показываем заблокированные NFT для разблокировки
                await NFTManagementHandler.myblock_command(update, context)
            
            # Обработка мануалов
            elif data == "work_manual":
                await ManualsHandler.work_manual_handler(update, context)
            
            # Обработка поиска по модели
            elif data == "search_type_selection":
                await ModelSearchHandler.show_search_type_selection(update, context)
            elif data == "random_search":
                await SearchHandler.show_mode_selection(update, context)
            elif data == "model_search":
                # Сбрасываем флаг from_results для обычных настроек
                context.user_data["from_results"] = False
                await ModelSearchHandler.show_model_selection(update, context)
            elif data == "model_search_from_results":
                # Устанавливаем флаг from_results для настроек из результатов
                context.user_data["from_results"] = True
                await ModelSearchHandler.show_model_selection(update, context)

            # Обработка выбора NFT для поиска по модели
            elif data.startswith("toggle_nft_"):
                await ModelSearchHandler.handle_nft_selection(update, context)
            elif data.startswith("nft_page_"):
                await ModelSearchHandler.handle_nft_selection(update, context)
            elif data == "reset_nft_selection":
                await ModelSearchHandler.handle_nft_selection(update, context)
            elif data == "start_model_search":
                await ModelSearchHandler.start_model_search(update, context)
            
            # Обработка кнопок пагинации для поиска по модели
            elif data.startswith("model_results_page_"):
                await ModelSearchHandler.handle_results_page(update, context)
            
            # Обработка кнопок пагинации для рандом поиска
            elif data.startswith("random_results_page_"):
                await SearchHandler.handle_results_page(update, context)
            
            # Обработка возврата к результатам поиска
            elif data == "back_to_results_search":
                # Возвращаемся к результатам рандом поиска
                await SearchHandler.show_search_results_page(update, context, page=0)
            elif data == "back_to_results_model":
                # Возвращаемся к результатам поиска по модели
                await ModelSearchHandler.show_search_results_page(update, context, page=0)
            
            # Обработка информации о текущей странице
            elif data == "current_page":
                await query.answer("Текущая страница", show_alert=False)

            elif data == "back_to_results_search":
                # Возвращаемся к результатам поиска
                await TemplatesHandler.back_to_results_search(update, context)
            
            # Обработка навигации
            elif data == "back_to_menu":
                await StartHandler.start_command(update, context)
            
            else:
                await query.answer("❌ Неизвестная команда")
                
        except Exception as e:
            logger.error(f"Ошибка в обработчике callback: {e}", exc_info=True)
            await query.answer("❌ Произошла ошибка")

    def run(self):
        print("🤖 NFT Gift Bot запущен!")
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        self.application.run_polling()

if __name__ == "__main__":
    bot = NFTBot()
    bot.run()