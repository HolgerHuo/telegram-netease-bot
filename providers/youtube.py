import yt_dlp
from requests import get
import logging, os
import helper

logger = logging.getLogger(__name__)

def get_song_info(keyword):
    def search(arg):
        def less_than_10mins(info, *, incomplete):
            duration = info.get('duration')
            if duration and duration > 600:
                return 'The video is too long'

        def generate_abspath(song):
            song['file'] = os.path.abspath(song['requested_downloads'][0]['filepath'])
            iterable_obj = iter(song['thumbnails'])
 
            while True:
                try:
                    item = next(iterable_obj)
                    if 'filepath' in item:
                        song['thumb'] = os.path.abspath(item['filepath'])
                except StopIteration:
                    break
            
            return song

        tmp_dir = helper.tmp_dir+'youtube'+'/'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        YDL_OPTIONS = {'logger': logger, 'noprogress': True, 'quiet': True, 'format': 'bestaudio', 'match_filter': less_than_10mins, 'keepvideo': True , 'writethumbnail': True, 'paths': {'home': tmp_dir},'postprocessors': [{ 'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}], 'overwrites': False, 'outtmpl': '%(id)s.%(ext)s'}
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                get(arg)
            except:
                results = ydl.sanitize_info(ydl.extract_info(f"ytsearch:{arg}", download=True))
                result = results['entries'][0] if results['entries'] and results['entries'][0] else None
                if result:
                    return generate_abspath(result)
                else:
                    return None 
            else:
                result = ydl.sanitize_info(ydl.extract_info(arg, download=True))
                if result['duration'] > 600:
                    return None
                return generate_abspath(result)
    return search(keyword)