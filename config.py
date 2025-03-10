import os
from dotenv import load_dotenv
from discord import ButtonStyle

import discord

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# الحصول على التوكن من المتغيرات البيئية
TOKEN = os.getenv('DISCORD_TOKEN')

# التحقق من وجود التوكن
if not TOKEN:
    raise ValueError("لم يتم العثور على توكن Discord. تأكد من وجود DISCORD_TOKEN في ملف .env")

# إعدادات عامة للبوت
BOT_CONFIG = {
    'command_prefix': '!',
    'status_message': '!fivem للفحص',
    'intents': discord.Intents(
        message_content=True,
        guilds=True,
        messages=True
    )
}

# إعدادات التسجيل
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'bot.log'
}

# إعدادات نظام التذاكر
TICKET_CONFIG = {
    'prefix': '『🎫』ticket-',
    'category_id': int(os.getenv('TICKET_CATEGORY_ID')),
    'staff_roles': [int(role_id) for role_id in os.getenv('STAFF_ROLE_IDS', '').split(',')],
    'log_channel_id': int(os.getenv('LOG_CHANNEL_ID')),
    'embed_color': 0x2f3136,
    'buttons': {
        'create': {
            'label': 'فتح تذكرة',
            'emoji': '🎫',
            'style': ButtonStyle.primary
        }
    }
}

# إعدادات فحص FiveM
FIVEM_CONFIG = {
    'api_url': 'https://servers-frontend.fivem.net/api/servers/single/{}',
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    'timeout_seconds': 10,
    'embed_color': 0x2f3136
}

# رسائل الخطأ
ERROR_MESSAGES = {
    'invalid_cfx': '❌ الرجاء إدخال رابط صحيح يبدأ بـ cfx.re/join/',
    'server_not_found': '❌ لم يتم العثور على السيرفر',
    'general_error': '❌ حدث خطأ أثناء جلب معلومات السيرفر. الرجاء المحاولة مرة أخرى.'
}