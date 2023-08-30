import tkinter as tk
from tkinter import Tk, ttk
from PIL import Image, ImageTk

import cv2
import numpy as np

from datetime import date, datetime, time, timedelta

# import pytesseract


# # timers for efficiency testing
from functools import wraps
import time as ttime

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = ttime.perf_counter()
        result = func(*args, **kwargs)
        end_time = ttime.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} took {total_time:.4f} seconds')
        return result
    return timeit_wrapper

'''
======================================
CONSTANTS
======================================
hard-coded image recognition for speed
'''

# nums pixel size
NUM_HEIGHT = 14
NUM_WIDTH = 14

# x,y pixel of 10s and 1s digit respectively
NUMS_Y = 704

YEARS_X = 576, 592, 608, 624
MONTHS_X = 656, 672
DAYS_X = 704, 720

HOURS_X = 752, 768 
MINS_X = 800, 816
SECS_X = 848, 864

# image map # outdated and poor
numRef = {
    '[10, 10, 13, 13, 7, 7, 7, 7, 7, 7, 13, 13, 10]': 0,
    '[0, 0, 1, 1, 3, 3, 13, 13, 13, 13, 1, 1, 1]':  1,
    '[5, 5, 9, 9, 5, 5, 7, 7, 5, 5, 11, 11, 7]': 2,
    '[4, 4, 7, 7, 3, 3, 5, 5, 5, 5, 13, 13, 8]' : 3,
    '[4, 4, 6, 6, 6, 6, 6, 6, 13, 13, 13, 13, 2]' : 4,
    '[8, 8, 9, 9, 5, 5, 5, 5, 5, 5, 11, 11, 8]': 5,
    '[8, 8, 11, 11, 7, 7, 5, 5, 5, 5, 9, 9, 4]': 6,
    '[4, 4, 4, 4, 7, 7, 9, 9, 6, 6, 6, 6, 4]': 7, 
    '[8, 8, 13, 13, 5, 5, 5, 5, 5, 5, 13, 13, 8]': 8,
    '[4, 4, 9, 9, 5, 5, 5, 5, 7, 7, 12, 12, 8]': 9,
}

# 5 pixel identification
id_pixels = [(5, 8), (7, 3), (10, 9), (2, 11), (8, 5)]

pixelRef = {
    "[1.0, 1.0, 0.0, 1.0, 1.0]": 0,
    "[1.0, 0.0, 1.0, 0.0, 0.0]": 1,
    "[0.0, 0.0, 0.0, 1.0, 1.0]": 2,
    "[0.0, 0.0, 0.0, 1.0, 0.0]": 3,
    "[1.0, 1.0, 1.0, 1.0, 1.0]": 4,
    "[1.0, 0.0, 0.0, 0.0, 0.0]": 5,
    "[0.0, 1.0, 0.0, 0.0, 0.0]": 6,
    "[1.0, 0.0, 0.0, 1.0, 1.0]": 7,
    "[0.0, 1.0, 0.0, 1.0, 0.0]": 8,
    "[0.0, 1.0, 1.0, 1.0, 0.0]": 9
}

id_pixels = [(5, 8), (7, 3), (10, 9), (2, 11), (8, 5)]

'''
DATE PARSING
'''
# @timeit # ~.038s
def getNum(frame, xcoord, ycoord=None, show=False, print_pixel=False):
    """Retrieves a number from the video

    Identify the number from a coordinate specified in the video and return it as a integer.

    Args:
        frame: numpy array image to identify.
        xcoord: x coordinate of the top-left pixel of the number
        ycoord: y coordinate of the top-left pixel, defaults to the nums_y_loc
        show: determines whether to show or to skip, defaults to noshow

    Returns:
        integer at that location, -1 if invalid
    """
    ycoord = NUMS_Y if ycoord == None else ycoord

    num_crop = np.around(cv2.cvtColor(frame[ycoord : ycoord + NUM_HEIGHT, 
                                            xcoord : xcoord + NUM_WIDTH], 
                                      cv2.COLOR_BGR2GRAY) / 255)

    showFrame(num_crop, show, title="cropped number")
    if print_pixel: print(num_crop)

    pixKey = str([num_crop[px[0]][px[1]] for px in id_pixels])
    if pixKey in pixelRef:
        return pixelRef[pixKey]
    
#     showFrame(num_crop, show=True, title="bad")
#     print("ocr goes brrr")
    
#     padded_num = np.pad(np.array(num_crop) * 255, 30)
#     numImage = Image.fromarray(padded_num).convert("RGB")
#     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
#     custom_config = r'-c tessedit_char_whitelist=0123456789 --psm 6'
#     return int(pytesseract.image_to_string(numImage, config=custom_config))

#     return numRef[hashed]

# @timeit # ~.35s
def getDate(frame, show=False):
    years = (1000 * getNum(frame, YEARS_X[0]) +
             100 * getNum(frame, YEARS_X[1]) +
             10 * getNum(frame, YEARS_X[2]) +
             getNum(frame, YEARS_X[3]))
    months = 10 * getNum(frame, MONTHS_X[0]) + getNum(frame, MONTHS_X[1])
    days = 10 * getNum(frame, DAYS_X[0]) + getNum(frame, DAYS_X[1])

    dateCrop = frame[NUMS_Y : NUMS_Y + NUM_HEIGHT, YEARS_X[0] : DAYS_X[1] + NUM_WIDTH]
    showFrame(dateCrop, show, title="cropped date")

    return datetime(years, months, days)

# @timeit #
def getTime(frame, show=False):
    hours = 10 * getNum(frame, HOURS_X[0]) + getNum(frame, HOURS_X[1])
    mins = 10 * getNum(frame, MINS_X[0]) + getNum(frame, MINS_X[1])
    secs = 10 * getNum(frame, SECS_X[0]) + getNum(frame, SECS_X[1])

    dateCrop = frame[NUMS_Y : NUMS_Y + NUM_HEIGHT, HOURS_X[0] : SECS_X[1] + NUM_WIDTH]
    showFrame(dateCrop, show, title="cropped time")

    return datetime.combine(datetime.today(), time(hours, mins, secs))

# @timeit
def getDateTime(frame, show=False):
    dateCrop = frame[NUMS_Y : NUMS_Y + NUM_HEIGHT, YEARS_X[0] : SECS_X[1] + NUM_WIDTH]
    showFrame(dateCrop, show, title="cropped datetime")

    return datetime.combine(getDate(frame), getTime(frame).time())

def getFrameFromFile(filename):
    return cv2.imread(filename)

def showFrame(frame, show, title="Unnamed Frame"):
    """Show the frame in question if show is true for debugging.

    If show is false, does nothing.
    If show is true, shows frame as an external window until a keypress is recorded.

    Args:
        frame: frame to show.
        title: title of the frame to show. Defaults to "Unnamed Frame"
        show: determines whether to show or to skip

    Returns:
        Nothing

    Raises:
    """

    if (show):
        cv2.imshow(title, frame)  # show frame on window
        cv2.waitKey(0)

        # closing all open windows
        cv2.destroyAllWindows()