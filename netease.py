import os.path
import yaml
import logging
import requests

logger = logging.getLogger(__name__)

# Construct Song Class
class Song(object):
    name = ""
    artist = ""
    id = 0
    url = ""
    format = ""
    album = ""

    def __init__(self, name, artist, id, format, album, url=None):
        self.name = name
        self.artist = artist
        self.id = id
        self.url = url
        self.format = format
        self.album = album

# Construct Location Class
class Location(object):
    song = ""
    thumb = ""

    def __init__(self, song, thumb):
        self.song = song
        self.thumb = thumb

# Load API config
config = yaml.safe_load(open("config.yml"))
api = config['netease']['neteaseapi']
userid = config['netease']['userid']
tmp_dir = config['netease']['tmpdir']

if config['netease']['cached']:
    from datetime import timedelta
    from requests_cache import CachedSession
    session = CachedSession('NCM_Cache',use_cache_dir=True,cache_control=False,expire_after=timedelta(days=1),allowable_methods=['GET'],allowable_codes=[200],match_headers=True,stale_if_error=False,)
    

# Wrap RESTful API access
def request_api(url):
    cookies = {'MUSIC_U': userid}
    if config['netease']['cached']:
        return session.get(url, cookies=cookies)
    return requests.get(url, cookies=cookies)

# Search for songs
def get_song_info(keyword):
    songs = request_api(api+"/search?keywords="+keyword+"&type=1").json()["result"]["songs"]
    for song in songs:
        name = song["name"]
        artists = []
        id = song['id']
        for artist in song['artists']:
            artists.append(artist['name'])
        artist = '&'.join(artists)
        album = song['album']['name']
        if check_exist(str(id), tmp_dir):
            format = check_exist(str(id), tmp_dir).split('.')[-1].lower()
            if format == 'flac':
                return Song(name, artist, id, format, album)
            elif request_api(api+"/song/url?id="+str(id)).json()["data"][0]["type"] == format:
                return Song(name, artist, id, format, album)
        availability = request_api(api+"/check/music?id="+str(id)).json()["success"]
        if availability:
            song_meta = request_api(api+"/song/url?id="+str(id)).json()["data"][0]
            if song_meta["url"] is not None and song_meta["freeTrialInfo"] is None:
                return Song(name, artist, id, song_meta["type"].lower(), album, song_meta["url"])
    return False

# Cache media
def cache_song(id, url, format, name, artist, album):
    location = tmp_dir+str(id)+'.'+format
    # delete low-res audio file
    if format == 'flac':
        if os.path.exists(tmp_dir+str(id)+'.mp3'):
            os.remove(tmp_dir+str(id)+'.mp3')
    try:
        img_location = cache_thumb(id)
    except Exception as e:
        img_location = None
        logger.error("Unable to cache thumbnail for "+name+' - '+artist)
        logger.debug(e)
    if not os.path.isfile(location):
        data = requests.get(url)
        with open(location, 'wb')as file:
            file.write(data.content)
        try:
            write_tags(location, format, artist, album, name, id)
        except Exception as e:
            logger.error("Could not write tag of "+name+" - "+artist)
            logger.debug(e)
        else:
            logger.warning("Tag "+name+" - "+artist+" has been written to "+location)
        logger.warning("Song "+str(id)+" has been cached")
    return Location(location, img_location)

# Write Audio Files tag
def write_tags(location, format, artist, album, name, id):
    if check_exist(str(id)+'_orig', tmp_dir+'img/'):
        thumb = check_exist(str(id)+'_orig', tmp_dir+'img/')
    elif check_exist(str(id), tmp_dir+'img/'):
        thumb = check_exist(str(id), tmp_dir+'img/')
    else: 
        thumb = None
    if format == 'flac':
        from mutagen.flac import Picture, FLAC
        audio = FLAC(location)
        audio["TITLE"] = name
        audio['ARTIST'] = artist
        audio['ALBUM'] = album
        audio.save()
        if thumb:
            image = Picture()
            image.type = 3
            image.desc = 'cover'
            if thumb.endswith('png'):
                image.mime = 'image/png'
            elif thumb.endswith('jpg'):
                image.mime = 'image/jpeg'
            with open(thumb, 'rb') as img:
                image.data = img.read()
            audio.add_picture(image)
            audio.save()
    if format == 'mp3':
        from mutagen.easyid3 import EasyID3
        audio = EasyID3(location)
        audio["title"] = name
        audio['artist'] = artist
        audio['album'] = album
        audio.save()
        if thumb:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, APIC
            audio = MP3(location, ID3=ID3)   
            if thumb.endswith('png'):
                mime = 'image/png'
            elif thumb.endswith('jpg'):
                mime = 'image/jpeg' 
            audio.tags.add(
                APIC(
                    encoding=3, 
                    mime=mime, 
                    type=3, 
                    desc=u'Cover',
                    data=open(thumb, 'rb').read()
                )
            )
            audio.save()
    if check_exist(str(id)+'_orig', tmp_dir+'img/'):
        os.remove(thumb)

# Cache thumbnails
def cache_thumb(id): 
    img_dir = tmp_dir+'img/'
    if not check_exist(str(id), img_dir):
        img_url = request_api(api+"/song/detail?ids="+str(id)).json()["songs"][0]['al']['picUrl']
        img = requests.get(img_url)
        img_ext = img_url.split('.')[-1].lower()
        location = img_dir+str(id) + '.' + img_ext
        with open(location, 'wb')as file:
            file.write(img.content)
        from PIL import Image
        MAX_SIZE = 320
        image = Image.open(location)
        original_size = max(image.size[0], image.size[1])
        if original_size >= MAX_SIZE:
            image.save(img_dir + str(id) +'_orig.png', 'PNG')
            if (image.size[0] > image.size[1]):
                resized_width = MAX_SIZE
                resized_height = int(round((MAX_SIZE/float(image.size[0]))*image.size[1])) 
            else:
                resized_height = MAX_SIZE
                resized_width = int(round((MAX_SIZE/float(image.size[1]))*image.size[0]))
            image = image.resize((resized_width, resized_height), Image.ANTIALIAS)
            image.save(img_dir + str(id) +'.png', 'PNG')
            return img_dir+str(id) + '.png'
        return location
    else:
        return check_exist(str(id), img_dir)
        
# Check if directory has item(s)
def check_exist(item, dir):
    for i in os.listdir(dir):
        if os.path.splitext(i)[0] == item and os.path.isfile(os.path.join(dir, i)):
            return os.path.join(dir, i)
    return False