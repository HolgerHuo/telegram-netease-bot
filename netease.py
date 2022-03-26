import requests
import os.path
import yaml
import logging

logger = logging.getLogger(__name__)

# Construct Song Object
class Song(object):
    name = ""
    artist = ""
    id = 0
    url = ""
    format = ""

    def __init__(self, name, artist, id, url, format):
        self.name = name
        self.artist = artist
        self.id = id
        self.url = url
        self.format = format

# Load API config
config = yaml.safe_load(open("config.yml"))
api = config['netease']['neteaseapi']
userid = config['netease']['userid']
tmp_dir = config['netease']['tmpdir']

# Wrap RESTful API access
def request_api(url):
    cookies = {'MUSIC_U': userid}
    return requests.get(url, cookies=cookies)

# Search for songs
def get_song_info(keyword):
    songs = request_api(api+"/search?keywords="+keyword+"&type=1")
    for song in songs.json()["result"]["songs"]:
        availability = request_api(api+"/check/music?id="+str(song["id"]))
        if availability.json()["success"]:
            song_meta = request_api(api+"/song/url?id="+str(song["id"])).json()["data"][0]
            if song_meta["url"] is not None and song_meta["freeTrialInfo"] is None:
                artists = []
                for artist in song['artists']:
                    artists.append(artist['name'])
                return Song(song["name"], '&'.join(artists), song["id"], song_meta["url"], song_meta["type"])
    return False

# Download song
def cache_song(id, url, format):
    location = tmp_dir+str(id)+'.'+format
    if not os.path.isfile(location):
        data = requests.get(url)
        logger.warning("Song "+str(id)+" has been cached")
        with open(location, 'wb')as file:
            file.write(data.content)
    return location