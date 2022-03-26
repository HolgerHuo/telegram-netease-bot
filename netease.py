import requests
import os.path
import re
import yaml
import logging

logger = logging.getLogger(__name__)

# Construct Song Object
class Song(object):
    name = ""
    artist = ""
    id = 0
    url = ""

    def __init__(self, name, artist, id, url):
        self.name = name
        self.artist = artist
        self.id = id
        self.url = url

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
            url = request_api(api+"/song/url?id="+str(song["id"])).json()["data"][0]["url"]
            if url is not None:
                artists = []
                for artist in song['artists']:
                    artists.append(artist['name'])
                return Song(song["name"], '&'.join(artists), song["id"], url)
    return False

# Download song
def cache_song(id, url):
    location = tmp_dir+str(id)+re.search('(\.[^.\\/:*?"<>|\r\n]+$)', url).group(1)
    if not os.path.isfile(location):
        data = requests.get(url)
        logger.warning("Song "+str(id)+" has been cached")
        with open(location, 'wb')as file:
            file.write(data.content)
    return location