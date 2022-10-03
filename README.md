# Telegram Netease Bot - Telegram 网易云音乐 Bot

Note: As the initial version of this bot is of low quality and is hard to extent horizontally, future development on this version may be dropped. A rewrite of this program is expected to be born some time around Jan. 2023.
---

![GitHub last commit](https://img.shields.io/github/last-commit/holgerhuo/telegram-netease-bot)![GitHub release (latest by date)](https://img.shields.io/github/v/release/holgerhuo/telegram-netease-bot)![GitHub](https://img.shields.io/github/license/holgerhuo/telegram-netease-bot)![GitHub all releases](https://img.shields.io/github/downloads/holgerhuo/telegram-netease-bot/total)![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/holgerhuo/telegram-netease-bot)

A python telegram bot enabling you to send **Netease Cloud Music** and **YouTube music (extracted from videos)** in chats

## ✨ Features

- Ease-of-use: No need to type "/" for command
- Extensible: Built on Python3 with [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- Elastic Netease Backend: Powered by [NodeJS NeteaseCloudMusicApi](https://github.com/Binaryify/NeteaseCloudMusicApi)
- Embed music tags automatically
- Enhanced caching system

## 👷‍♂️ QuickStart

Add example Radio 669 by going to [@radio_669_bot](https://t.me/radio669_bot).

Press `Start`

Choose your music by sending 
"**点歌** <song_name>"

Add r669 bot to your favorite groups, ...

Enjoy it!

## 💻 Deployment 

### Prerequisites

**telegram-netease-bot requires `Python3.7+`, which means you'll have to compile Python3.7 yourself if you are on CentOS 7**

- A working NodeJS [NeteaseCloudMusicAPI](https://github.com/Binaryify/NeteaseCloudMusicApi) (Can be deployed on Vercel)
- Python 3.7+ and pip3
- Bot token obtained from [BotFather](https://t.me/botfather)
- Obtain your NCM UserID

#### How-to: Obtain NCM UserID
1. Login to your NodeJS NCMApi using the methods in the [documentation](https://binaryify.github.io/NeteaseCloudMusicApi/#/?id=%e7%99%bb%e5%bd%95) (It is recommended to login using SMS code)
2. Use your browser to inspect cookies and find the value of `MUSIC_U`
3. That's it!

### Install

```bash
git clone https://github.com/HolgerHuo/telegram-netease-bot.git r669
cd r669
pip3 install -r requirements.txt
python3 run.py
```

A sample systemd service is shipped at r669.service. Add it to your system if you like.

Don't forget to change your bot's name, avatar, and about info and enjoy it!

## 💖 Credits
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)
- [NeteaseCloudMusicAPI](https://github.com/Binaryify/NeteaseCloudMusicApi)

## 📜 License

GNU General Public License v3.0

©️ Holger Huo

[@holgerhuo@dragon-fly.club](https://mast.dragon-fly.club/@holgerhuo)