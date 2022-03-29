from PIL import Image

# Generate 250x250 thumbnail for Telegram API
def gen_thumb(location):
    MAX_SIZE = (250, 250)
    with Image.open(location) as image:
        if max(image.size[0], image.size[1]) >= max(MAX_SIZE):
            image.thumbnail(MAX_SIZE)
            image = image.convert('RGB')
            image.save(location)