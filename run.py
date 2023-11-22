import logging
import importlib
import helper
import utils.cache_handler as cache
from utils.image_handler import gen_thumb
import providers.youtube as youtube
import telebot

logger = logging.getLogger('TNB')
logging.basicConfig(level=getattr(logging, helper.log_level.upper(), 10),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Sign into Telegram
if 'tgapi' in helper.config['general']:
    from telebot import apihelper
    apihelper.API_URL = helper.config['general']['tgapi']
bot = telebot.TeleBot(helper.token, threaded=True, num_threads=helper.threads)

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
    bot.reply_to(message, """欢迎使用669点歌台!\n\n发送\n<b>点歌/dg/wy</b> 歌曲名称\n进行网易云搜索！\n<b>yt/油管</b> 歌曲名称\n进行YouTube搜索！\n\nPowered by <b><a href='https://github.com/HolgerHuo/telegram-netease-bot/'>TelegramNeteaseBot</a></b>\n<a href='https://dragon-fly.club/'>DragonFly Club</a>""",parse_mode='HTML')

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
                if cache.check(song.id, provider) and cache.check(str(song.id), provider).split('.')[-1] == song.format:# cache hit, send directly
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

@bot.message_handler(regexp='^(?:yt|油管|视频) .*')
def handle_youtube(message):
    reply = bot.reply_to(message, text="正在搜索\n<b>"+message.text[3:]+"</b>...", parse_mode='HTML')
    try:
        song = youtube.get_song_info(message.text[3:])
    except Exception: # Catch search error
        bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="搜索\n<b>"+message.text[3:]+"</b>\n失败！请重试！", parse_mode='HTML')
    else:
        if not song: # Return song not found error
            bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="<b>"+message.text[3:]+"</b>\n无法被找到或超过10分钟", parse_mode='HTML')
        else:  
            if 'track' in song:
                song['title'] = song['track']
            name = "「<b>"+song['title']+"</b>」\nby "+song['artist'] if 'artist' in song else "「<b>"+song['title']+"</b>」"
            if not 'artist' in song:
                song['artist'] = None
            bot.edit_message_text(chat_id=message.chat.id, message_id=reply.id, text="正在发送\n"+name, parse_mode='HTML')
            bot.send_chat_action(message.chat.id, "upload_audio")
            with open(song['file'], 'rb') as a:
                thumb = open(song['thumb'], 'rb') if 'thumb' in song else None
                bot.send_audio(chat_id=message.chat.id, reply_to_message_id=message.message_id, audio=a, caption=name, parse_mode='HTML', title=song['title'], performer=song['artist'], thumb=thumb)
                if thumb:
                    thumb.close()
            bot.delete_message(chat_id=message.chat.id, message_id=reply.id)
            logger.info(song['title']+" has been sent to "+str(message.chat.id))

from time import time
from flask import Flask, request
import requests
import threading

app = Flask(__name__)

app.logger.disabled = True
logging.getLogger('werkzeug').disabled = True

api = helper.ncmapi
userid = helper.ncmuserid

@app.route('/check')
def check():
    ts = str(int(time()))
    status = requests.get(api+'/login/status?timestamp=' + ts, cookies={'MUSIC_U': userid})
    if not status.json()['data']['account']:
        return {"status": False, "api": api}
    else:
        return {"status": True}

@app.route('/update', methods=['POST'])
def update():
    key = request.get_json().get('key')
    ts = str(int(time()))
    key_status = requests.get(
        api+'/login/status?timestamp='+ts, cookies={'MUSIC_U': key})
    if (key_status.json()['data']['account'] is not None):
        with open('config.yml', 'r+') as f:
            global userid
            global helper
            src = f.read()
            f.seek(0)
            src = src.replace(userid, key)
            f.write(src)
            f.truncate()
            userid = key
            helper.ncmuserid = key
        return {"status": True}
    else:
        return {"status": False, "api": api}

@app.route("/")
def entry():
    return """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Scan to login to NCM</title>
</head>

<body>
    <img id="qrImg" />
    <div id="info" class="info"></div>
    <script src="https://cdn.jsdelivr.net/npm/axios@0.26.1/dist/axios.min.js
    "></script>
    <script>
        let base
        async function checkStatus(key) {
            const res = await axios({
                url: `${base}/login/qr/check?key=${key}&timestamp=${Date.now()}&noCookie=true`,
            })
            return res.data
        }
        async function login() {
            const status = await axios({
                url: `${window.location}/check`,
            })
            if (!status.data.status) {
                document.querySelector('#info').innerText = "Login expired, scan QRCode to refresh!"
                base = status.data.api
                let timer
                const res = await axios({
                    url: `${base}/login/qr/key?timestamp=${Date.now()}`,
                })
                const key = res.data.data.unikey
                const res2 = await axios({
                    url: `${base}/login/qr/create?key=${key}&qrimg=true&timestamp=${Date.now()}`,
                })
                document.querySelector('#qrImg').src = res2.data.data.qrimg

                timer = setInterval(async () => {
                    const statusRes = await checkStatus(key)
                    if (statusRes.code === 800) {
                        document.querySelector('#info').innerText = 'QRCode expired, refresh page'
                        clearInterval(timer)
                    }
                    if (statusRes.code === 803) {
                        clearInterval(timer)
                        updateStatus = await axios({
                            url: `${window.location}/update`,
                            method: 'post',
                            data: {
                                "key": statusRes.cookie.replaceAll(' HTTPOnly', '').split(";").map(cookie => cookie.startsWith('MUSIC_U') && cookie.slice(8) || undefined).join(''),
                            },
                        })
                        login()
                    }
                }, 3000)
            } else {
                document.querySelector('#info').innerText = "Login information ok!"
                document.querySelector('#qrImg').src = ''
            }
        }
        login()
    </script>
    <style>
        .info {
            white-space: pre;
        }
    </style>
</body>

</html>
"""

threading.Thread(target=lambda: app.run(host='127.0.0.1', port=5000)).start()

# Start polling
threading.Thread(target=lambda: bot.infinity_polling()).start()