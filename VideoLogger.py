import numpy as np
import pygame
from pygame.locals import *
import cv2  # conda install --channel https://conda.anaconda.org/menpo opencv3
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import getTerminalCharset
import tkFileDialog
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
import os


# Get metadata for video file
def metadata_for(fn):

    fn, realname = unicodeFilename(fn), fn
    parser = createParser(fn, realname)
    if not parser:
        print "Unable to parse file"
        exit(1)
    try:
        metadata = extractMetadata(parser)
    except HachoirError, err:
        print "Metadata extraction error: %s" % unicode(err)
        metadata = None
    if not metadata:
        print "Unable to extract metadata"
        exit(1)

    text = metadata.exportPlaintext()
    charset = getTerminalCharset()
    for line in text:
        print makePrintable(line, charset)

    return metadata

root = tk.Tk()
root.withdraw()
path = tkFileDialog.askopenfilename()
# directory = r'C:\Users\Kevin\Documents\GitHub\iKidsNewbornCognitiveVisualizer'
# filename = r'E-0582-11-v1-4_2017-02-07_14-51-17.mp4'
# filepath = directory + '\\' + filename
filepath = str(path)
filename = os.path.basename(filepath)

meta = metadata_for(filepath)

# noinspection PyArgumentList
cap = cv2.VideoCapture(filepath)


pygame.init()
split0 = str(meta).split(':')
width = 640
height = 480
for idx, e in enumerate(split0):
    if 'width' in e.lower():
        width = int(split0[idx + 1].split(' ')[1])
    if 'height' in e.lower():
        height = int(split0[idx + 1].split(' ')[1])
screen_width, screen_height = width, height
print(screen_width)
print(screen_height)
screen = pygame.display.set_mode((screen_width, screen_height))

font = pygame.font.Font(None, 17)


def display(disp_str):
    text = font.render(disp_str, True, (255, 255, 255), (0, 0, 0))
    text_rect = text.get_rect()
    text_rect.centerx = screen.get_rect().centerx
    text_rect.centery = screen.get_rect().height - 10

    screen.blit(text, text_rect)
    pygame.display.update()

num = 0
error = 0
done = False
pause = False
prev_pause_key = False
clock = pygame.time.Clock()
fp = open(filename+'.log', 'wb')
t = 0
while cap.isOpened():
    pygame.event.pump()
    keys = pygame.key.get_pressed()

    if keys[K_ESCAPE]:
        break
    current_pause_key = keys[K_SPACE]
    if current_pause_key and not prev_pause_key:
        prev_pause = True
        pause = not pause
    prev_pause_key = current_pause_key

    state_str = ''
    if pause:
        state_str += 'paused '
    if done:
        state_str += 'done '
    key_list = [pygame.key.name(idx) for idx, key in enumerate(keys) if key == 1]
    key_list_str = ','.join(key_list)
    display_str = state_str + ' : ' + str(num) + ' : [' + key_list_str + ']'

    if not done:
        if not pause:
            ret, frame = cap.read()
            if frame is None:
                done = True

            blue = frame[:, :, 0].copy()
            red = frame[:, :, 2].copy()

            frame[:, :, 0] = red
            frame[:, :, 2] = blue

            screen.blit(pygame.image.frombuffer(frame.tostring(), (screen_width, screen_height), "RGB"), (0, 0))

            num += 1
            fps = cap.get(cv2.CAP_PROP_FPS)
            clock.tick(fps)
            frame_interval = (1000.0 / fps)
            t += frame_interval/1000.0
            int_frame_interval = int(np.round(frame_interval))
            iter_error = int_frame_interval - frame_interval
            error += np.abs(iter_error)

            fp.write(str(t) + ' : Keyboard Commands: ' + key_list_str + '\r\n')
            fp.write(str(t) + ' : XBox Controller Commands: ' + key_list_str + '\r\n')
            fp.write(str(t) + ' : TCP Commands: ' + key_list_str + '\r\n')
            if num % 30 == 0:
                print('iteration={0}, wait interval={1}, accumulated error={2}'.format(num, int_frame_interval, error))

    display(display_str)

    pygame.display.update()

fp.close()
cap.release()
cv2.destroyAllWindows()
pygame.quit()
