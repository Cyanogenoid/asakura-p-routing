from PIL import Image

img = Image.open('data/st_itemicon.png')

COLS = 8
ROWS = 4
SIZE = 32

names = [
    'small_mp',
    'big_mp',
    'infinite_mp',
    'hourglass2',
    'bubble_key',
    'key',
    'coin',
    'mp',
    'blaze',
    'gravity',
    'magic',
    'dash',
    'feather',
    'break',
    'blast',
    'guard',
    'impact',
    'chain',
    'create',
    'eye',
    'candle',
    'hourglass',
    'stability',
    'ruby',
    'sapphire',
    'emerald',
    'diamond',
]

k = 0
for i in range(ROWS):
    for j in range(COLS):
        if k >= len(names):
            break
        name = names[k]
        tile = img.crop((
            j * SIZE,
            i * SIZE,
            (j + 1) * SIZE,
            (i + 1) * SIZE,
        ))
        tile.save(f'data/{name}.png')
        k += 1
