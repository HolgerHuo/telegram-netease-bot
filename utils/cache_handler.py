import os
import helper
from utils.song_handler import write_tags
import logging
import requests
import mimetypes

logger = logging.getLogger(__name__)

# Check for cache presence
def check(id, provider, image=False):
    dir = helper.tmp_dir+provider+'/img/' if image else helper.tmp_dir+provider+'/'
    if not os.path.exists(dir):
        return False
    for i in os.listdir(dir):
        if os.path.splitext(i)[0] == str(id) and os.path.isfile(os.path.join(dir, i)):
            return os.path.join(dir, i)
    return False

# Generic Media Caching
def cache(song, provider):
    tmp_dir = helper.tmp_dir+provider+'/'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    song.file = tmp_dir+str(song.id)+'.'+song.format
    # delete low-res audio file
    if check(song.id, provider):
        os.remove(check(song.id, provider))
    data = requests.get(song.url)
    with open(song.file, 'wb')as f:
        f.write(data.content)
    try: 
        write_tags(song)
    except Exception as e:
        logger.error("Failed to write tags to "+song.file+" of "+song.title+" - "+song.artist)
        logger.debug(e)
    logger.warning("Song "+str(song.id)+" has been cached")
    return song

# Cache thumbnails
def cache_thumb(song, provider, force=False): 
    tmp_dir = helper.tmp_dir+provider+'/img/'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    if force or not check(str(song.id), provider, image=True):
        img = requests.get(song.thumb_url)
        mime = 'image/jpeg' if img.headers['content-type'] == 'image/jpg' else img.headers['content-type']
        ext = mimetypes.guess_extension(mime)
        location = tmp_dir+str(song.id) + ext
        with open(location, 'wb')as f:
            f.write(img.content)
        song.thumb = location
        return song
    else:
        song.thumb = check(str(song.id), provider, image=True)
        return song