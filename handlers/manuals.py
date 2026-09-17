# handlers/manuals.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from utils import Utils

logger = logging.getLogger(__name__)

class ManualsHandler:
    @staticmethod
    async def work_manual_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Мануал по ворку"""
        query = update.callback_query
        await query.answer()
        
        text = """<b>Мануал по В0РКУ на нфт ☝️</b>

<b>1. Подготовка аккаунта 📱</b>
•  Купите хороший аккаунт(желательно +7) 
•  Купите на аккаунт телеграм премиум, чтобы не было спам блока

<b>2. Поиск мамонта(2 лучших варианта)</b>
•  Поиск мамонта через бота парсера(бот тимы) - @NFTparsRobot
•  Поиск мамонтов через маркет телеграма(звезды)

<b>3. Нагрев мaмонта 🦣</b>
•  Тут играет ваше умение разговаривать с людьми, социальная инженерия. Вам не обязательно втираться в доверие мамонта, достаточно лишь завести его на fейк гаранта. 

Лучше всего для этого используйте сообщения ниже 🔛

<code>Ну понимаешь, я тоже первый боюсь идти, лучше всего пойдем популярного гаранта с репой. Особенно у него 0 процент комиссии за сделку. Гарант если что @ksomu а так же лучше всего ознакомься с его отзывами @revKsomu / @rewKsomu.</code>

<code>Я обычно хожу гаранта, т.к с ним удобнее проводить сделку без скама. Пошли гаранта @ksomu у него 0% комиссии и более 300 отзывов @revKSomu / @rewKsomu. Мне написать ему чтоб сделку провел?</code>

•  После того как вы убедили 🦣 на fейк гаранта, пишите гаранту (https://t.me/ksomu) с просьбой создать конфу для сделки. 
•  Проводите сделку(гарант все напишет) и вам выплатят ваш %.

<b>ДОП. ИНФОРМАЦИЯ ‼️</b>

•  Если у вас спам блок - ищите 🦣 в чатах по нфт купля/продажа.
•  Если 🦣 просит звезды, просите у него скриншот их отсутствия(не всегда работает).
•  Не думайте, что если у вас не получается в0ркать, чаще всего вам не везет, просто работайте дальше."""

        keyboard = [
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')