import logging
import importlib
import helper
import utils.cache_handler as cache
from utils.image_handler import gen_thumb
import telebot
from telebot import util

logger = logging.getLogger('TNB')
logging.basicConfig(level=getattr(logging, helper.log_level.upper(), 10),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Sign into Telegram
if 'tgapi' in helper.config['general']:
    from telebot import apihelper
    apihelper.API_URL = helper.config['general']['tgapi']
bot = telebot.TeleBot(helper.token, threaded=True)
bot.worker_pool = util.ThreadPool(num_threads=helper.threads) 

# Construct Song Class
class Song(object):
    def __init__(self, keyword, id=None, title=None, artist=None, album=None, alt=None, file=None, thumb=None, format=None, url=None, thumb_url=None):
        self.keyword = keyword
        self.id = id
        self.title = title
        self.artist = artist
        self.album = album
        self.alt = alt
        self.file = file
        self.thumb = thumb
        self.format = format
        self.url = url
        self.thumb_url = thumb_url

# Handle '/start' and '/help' command
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, """欢迎使用669点歌台!\n\n发送\n<b>点歌</b> 歌曲名称\n进行网易云搜索！\n\nPowered by <b><a href='https://github.com/HolgerHuo/telegram-netease-bot/'>TelegramNeteaseBot</a></b>\n<a href='https://dragon-fly.club/'>DragonFly Club</a>""",parse_mode='HTML')

# Handle 点歌
@bot.message_handler(regexp='^(?:点歌|dg|wy) .*')
def handle_netease(message):
    select_from_providers(message, Song(message.text[3:]), 'netease')

def select_from_providers(message, song, provider):
    try:
        backend = importlib.import_module('.'+provider, package='providers')
    except Exception as e:
        logger.error("Provider "+provider+" cannot be found!")
        bot.reply_to(message, "无法找到<b>"+provider+"</b>源\n请尝试联络bot管理员！",parse_mode='HTML')
    else:
        reply = bot.reply_to(message, text="正在搜索\n<b>"+song.keyword+"</b>...", parse_mode='HTML')
        try:
            backend.get_song_info(song)
        except Exception as e: # Catch search error
            bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="搜索\n<b>"+song.keyword+"</b>\n失败！请重试！", parse_mode='HTML')
            logger.error("Search "+song.keyword+" in "+provider+" failed!")
            logger.debug(e)
        else:
            if not song.id: # Return song not found error
                bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="<b>"+song.keyword+"</b>\n无法被找到或没有版权", parse_mode='HTML')
                logger.warning(song.keyword+" is not found!")
            else:  
                name = "「<b>"+song.title+"</b>」\nby "+song.artist+"\n\n<i>"+song.alt+"</i>" if song.alt else "「<b>"+song.title+"</b>」\nby "+song.artist
                if cache.check(song.id, provider):# cache hit, send directly
                    song.file = cache.check(str(song.id), provider)
                    song.thumb = cache.check(str(song.id), provider, image=True)
                    if not song.thumb:
                        try:
                            backend.get_thumb(song)
                        except Exception as e:
                            logger.error("Failed to cache thumbnail for "+song.title+" - "+song.artist)
                            logger.debug(e)
                    send_song(message, reply, song)
                else:
                    bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="正在缓存\n"+name, parse_mode='HTML')
                    try: # Caching Audio
                        backend.get_file(song)
                    except Exception as e:
                        bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text=name+"\n缓存失败！请重试", parse_mode='HTML')
                        logger.error(song.title+" - "+song.artist+" could not be cached!")
                        logger.debug(e)
                    else: # Send audio
                        send_song(message, reply, song)

def send_song(message, reply, song):
    name = "「<b>"+song.title+"</b>」\nby "+song.artist+"\n\n<i>"+song.alt+"</i>" if song.alt else "「<b>"+song.title+"</b>」\nby "+song.artist
    bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="正在发送\n"+name, parse_mode='HTML')
    bot.send_chat_action(message.chat.id, "upload_audio")
    with open(song.file, 'rb') as a:
        try:
            gen_thumb(song.thumb)
        except Exception as e:
            logger.error("Failed to generate thumbs for "+song.title+" - "+song.artist)
        thumb = open(song.thumb, 'rb') if song.thumb else None
        bot.send_audio(chat_id=message.chat.id, reply_to_message_id=message.message_id, audio=a, caption=name, parse_mode='HTML', title=song.title, performer=song.artist, thumb=thumb)
        if thumb:
            thumb.close()
    bot.delete_message(chat_id=message.chat.id, message_id=reply.id)
    logger.info(song.title+' - '+song.artist+" has been sent to "+str(message.chat.id))

# Start polling
bot.infinity_polling()