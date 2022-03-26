import logging
import sys
import yaml
import netease
import telebot

logger = logging.getLogger(__name__)

# Load config.yml
try:
    config = yaml.safe_load(open("config.yml"))
    log_level = config['general']['loglevel']
    token = config['general']['token']
except Exception as e:
    logger.critical("config.yml is not valid!")
    logger.debug(e)
    sys.exit()
    
logging.basicConfig(level=getattr(logging, log_level.upper(), 10),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Sign into Telegram
if 'tgapi' in config['general']:
    from telebot import apihelper
    apihelper.API_URL = config['general']['tgapi']
bot = telebot.TeleBot(token)

# Handle '/start' and '/help' command
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(message, 
    """欢迎使用669点歌台!\n\n发送\n<b>点歌</b> 歌曲名称\n进行网易云搜索！\n\nPowered by <b><a href='https://dragon-fly.club/'>DragonFly Club</a></b>\n<a href='https://github.com/HolgerHuo/telegram-netease-bot/'>Source Code</a>
    """,
    parse_mode='HTML')

# Handle 点歌
@bot.message_handler(regexp="(点歌).*")
def handle_netease(message):
    keyword = message.text[2:]
    reply = bot.reply_to(message, text='正在搜索<b>'+ keyword+"</b>...", parse_mode='HTML')
    song = netease.get_song_info(keyword.replace(" ", "+"))
    # Return copyright content error
    if not song: 
        bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text='<b>'+keyword+'</b>\n无法被找到或没有版权', parse_mode='HTML')
        logger.warning(keyword+" is not found!")
    else:  # Send Music
        bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="正在缓存\n「<b>"+song.name+"</b>」\nby "+song.artist, parse_mode='HTML')
        location = netease.cache_song(song.id, song.url, song.format)
        with open(location, 'rb') as music:
            bot.send_chat_action(message.chat.id, "upload_audio")
            bot.send_voice(chat_id=message.chat.id, reply_to_message_id=message.message_id, voice=music, caption="「<b>"+song.name+"</b>」\nby "+song.artist, parse_mode='HTML')
            bot.delete_message(chat_id=message.chat.id, message_id=reply.id)

bot.infinity_polling()