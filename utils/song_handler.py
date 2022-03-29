def set_song(_self, **kwargs):
    for k,v in kwargs.items():
        setattr(_self, k, v)

# Write Audio Files tag
def write_tags(song):
    if song.format == 'flac':
        from mutagen.flac import Picture, FLAC
        audio = FLAC(song.file)
        audio['TITLE'] = song.title
        audio['ARTIST'] = song.artist.split('&')
        audio['ALBUM'] = song.album
        audio.save()
        if song.thumb:
            image = Picture()
            image.type = 3
            image.desc = 'cover'
            if song.thumb.endswith('png'):
                image.mime = 'image/png'
            elif song.thumb.endswith('jpg'):
                image.mime = 'image/jpeg'
            with open(song.thumb, 'rb') as img:
                image.data = img.read()
            audio.add_picture(image)
            audio.save()
    if song.format == 'mp3':
        from mutagen.easyid3 import EasyID3
        audio = EasyID3(song.file)
        audio['title'] = song.title
        audio['artist'] = song.artist.split('&')
        audio['album'] = song.album
        audio.save()
        if song.thumb:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, APIC
            audio = MP3(song.file, ID3=ID3)   
            if song.thumb.endswith('png'):
                mime = 'image/png'
            elif song.thumb.endswith('jpg'):
                mime = 'image/jpeg' 
            audio.tags.add(
                APIC(
                    encoding=3, 
                    mime=mime, 
                    type=3, 
                    desc=u'Cover',
                    data=open(song.thumb, 'rb').read()
                )
            )
            audio.save()