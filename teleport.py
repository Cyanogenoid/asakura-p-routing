import matplotlib.pyplot as plt
from PIL import Image

import inject


plt.ion()


def on_click(event):
    if event.button == 1:
        process.write_double(0x5B3FA0, event.xdata)
        process.write_double(0x5B3FA8, event.ydata)
        print(event.key, event.xdata, event.ydata)

plt.gcf().canvas.mpl_connect('button_press_event', on_click)


old_room, new_room = None, None

with inject.Process(name='AssaCrip_en.exe') as process:
    while True:
        old_room, new_room = new_room, process.read_int32(0x5D9AFC)
        if old_room != new_room:
            img = Image.open('img/{:03d}.png'.format(new_room + 1))
            plt.cla()
            plt.imshow(img, interpolation='catrom')
            plt.axis('off')
            plt.subplots_adjust(left=0, top=1, right=1, bottom=0)
        plt.pause(0.05)