import helper
import utils.cache_handler as cache
import utils.song_handler as song_handler
import logging
import requests

logger = logging.getLogger(__name__)

# Load API config
api = helper.config['netease']['neteaseapi']
userid = helper.config['netease']['userid']
cached = helper.config['netease']['cached']

if cached: # Create caching session
    from datetime import timedelta
    from requests_cache import CachedSession
    session = CachedSession('NCM_Cache',use_cache_dir=True,cache_control=False,expire_after=timedelta(days=1),allowable_methods=['GET'],allowable_codes=[200],match_headers=True,stale_if_error=False,)

# Wrap RESTful API access
def _request_api(url):
    cookies = {'MUSIC_U': userid}
    if cached:
        return session.get(url, cookies=cookies)
    return requests.get(url, cookies=cookies)

# Search for songs
def get_song_info(song):
    for s in _request_api(api+'/cloudsearch?keywords='+song.keyword+'&type=1').json()['result']['songs']:
        artists = []
        for artist in s['ar']:
            artists.append(artist['name'])
        alt = s['alia'][0] if s['alia'] else None
        song_handler.set_song(song,
            id = s['id'],
            title = s['name'],
            artist = '&'.join(artists),
            album = s['al']['name'],
            alt = alt,
            file = cache.check(str(s['id']), 'netease') # Check for cache as part of availability check
        )  
        if song.file:
            format = song.file.split('.')[-1]
            if format == 'flac':
                song.format = format
                return song
            elif _request_api(api+'/song/url?id='+str(song.id)).json()['data'][0]['type'] == format:
                song.format = format
                return song
        if _request_api(api+'/check/music?id='+str(song.id)).json()['success']:
            song_meta = _request_api(api+'/song/url?id='+str(song.id)).json()['data'][0]
            if song_meta['url'] is not None and song_meta["freeTrialInfo"] is None:
                song_handler.set_song(song, url=song_meta['url'], format=song_meta['type'].lower())
                return song
    return song_handler.set_song(song, id=False)

# Get file location
def get_file(song):
    try:
        song = get_thumb(song, force=True)
    except Exception as e:
        logger.error("Failed to cache thumbnail for "+song.title+" - "+song.artist)
        logger.debug(e)
    song = cache.cache(song, 'netease')
    return song

# Cache thumb
def get_thumb(song, force=False):
    song.thumb_url = _request_api(api+'/song/detail?ids='+str(song.id)).json()['songs'][0]['al']['picUrl']
    return cache.cache_thumb(song, 'netease', force)