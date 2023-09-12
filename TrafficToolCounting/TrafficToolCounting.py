# TrafficTool v1.1.0

import tkinter as tk # ui library
from tkinter import Tk, ttk, filedialog # ui library
 
from PIL import Image, ImageTk, ImageOps # image processing library
import cv2 # image processing library

import argparse # parse command line

from datetime import date, datetime, time, timedelta # system time library

# helper python code
import timeParse # extract time data from frames

# helper panels
import InputPanelCountingModule # input panel
import VideoPanelCountingModule # video panel

# timers for efficiency testing
from functools import wraps
import time

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} took {total_time:.4f} seconds')
        return result
    return timeit_wrapper

class TrafficTool(Tk):
    def __init__(self, 
                 file_path=None, 
                 view_name=None,
                 output_dir=None,
                 time_interval=1, 
                 num_lanes=6,
                 max_length=20,
                 width=800, 
                 height=500,
                 debug=False):
        '''TrafficTool is the main root object that combines and configures both Input Panel and Video Panel to create
        an interface to speed up manual data entry for car congestion data.
        
        Args:
            file_path: preset file path of video (default to None)
            view_name: preset view name (default to None)
            output_dir: preset excel output (default to None)
            time_interval: time duration of 1 time "chunk" (default to 5 sec)
            num_lanes: number of max lanes to display on input panel (default to 6)
            max_length: maximum data value to display on input panel (default to 5)
            width: initial width of tool, can be resized (defualt to 800px)
            height: initial height of tool, can be resized (default to 500px)
            debug: debug mode for addit info
        '''
        
        super().__init__()
        
        # process input params
        time_interval = 1 if time_interval == None else int(time_interval)
        num_lanes = 6 if num_lanes == None else int(num_lanes)
        debug = False if debug == None else debug
        
        self.debug = debug
        
        # set initial window sizes
        self.geometry(str(width) + "x" + str(height))
        
        # window size resizable
        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)
        
        # set inner padding
        self.config(padx=10, pady=10)
        
        # create top title frame
        self.title_frame = ttk.Frame(master=self,
                                    relief="groove",
                                    borderwidth=1)
        self.title_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.title_label = tk.Label(master=self.title_frame, text="Traffic Tool Counting v.1.0.3",)
        self.title_label.pack()
        self.rowconfigure(0, weight=0) # static title height
        
        # create left frame
        self.left_frame = ttk.Frame(master=self,
                                    relief="groove",
                                    borderwidth=1)
        self.left_frame.grid(row=1, column=0, sticky="nsew")
#         self.left_label = tk.Label(master=self.left_frame, text="Left Panel")
#         self.left_label.pack()
        self.rowconfigure(1, weight=1) 
        self.columnconfigure(0, weight=0)#, uniform="row")
        
        # create right frame
        self.right_frame = ttk.Frame(master=self,
                                    relief="groove",
                                    borderwidth=1)
        self.right_frame.grid(row=1, column=1, sticky="nsew")
#         self.right_label = tk.Label(master=self.right_frame, text="Right Panel")
#         self.right_label.pack()
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=5)#, uniform="row")
        
        # setup left panel
        
        input_panel = InputPanelCountingModule.InputPanel(parent=self.left_frame, 
                                                  master=self, 
                                                  file_path=file_path, 
                                                  num_lanes=num_lanes, 
                                                  max_length=max_length,
                                                  display_lanes=num_lanes,
                                                  debug=self.debug)
        video_panel = VideoPanelCountingModule.VideoPanel(parent=self.right_frame, 
                                                  master=self, 
                                                  file_path=file_path, 
                                                  view_name=view_name, 
                                                  output_dir=output_dir, 
                                                  time_chunk=time_interval, 
                                                  debug=self.debug)
        
#         # bind input_panel to video_panel
#         input_panel.setIndexFunc(video_panel.getTimeStr)
#         input_panel.setResultPathFunc(video_panel.getResultFilePath)
        input_panel.setNextFunc(video_panel._jumpNextChunk)
        self.debug_print("input_panel to video_panel done")
        
#         # bind video_panel to input_panel for output func
        video_panel.setLoadLanesFunc(input_panel.loadLanes)
        video_panel.setTimeIndexFunc(input_panel.updateTimeIndex)
        video_panel.setResultPathFunc(input_panel.updateResultPath)
        self.debug_print("video_panel to input_panel done")
        
        video_panel._update_display()
        self.bind_all("<Button-1>", lambda event: event.widget.focus_set())
    
    
    def debug_print(self, string):
        '''Print only if debug mode is on.
        
        Args:
            string: string to print
        '''
        if self.debug: print(string)
    
if __name__ == "__main__":
#     msg = '''
#         (Yet Unnamed) TrafficTool v.1.0.0
#         \n
#         \nInteractive interface for traffic data collection
#         \n
#         \n(Options)
#         \n-fp [filename] : specify the filepath going in
#         \n-d             : debug on
#         \n-nl            : number of lanes (defaults to 6)
#         '''

#     parser = argparse.ArgumentParser(description=msg)
#     parser.add_argument("-o", "--output_dir", help = "directory to store output")
#     parser.add_argument("-vn", "--view_name", help = "video view name")
#     parser.add_argument("-ofp", "--ofile_path", help = "overlay file path")
#     parser.add_argument("-ti", "--time_interval", help = "time length of each interval (default 5)")
#     parser.add_argument("-nl", "--num_lanes", help = "number of lanes (default 6)")
#     parser.add_argument("-d", "--debug", help = "toggle debug mode", action="store_true")
#     args=parser.parse_args()
    
#     trafficTool = TrafficTool(file_path=args.vfile_path, 
#                               view_name=args.view_name,
#                               output_dir=args.output_dir, 
#                               time_interval=args.time_interval, 
#                               num_lanes=args.num_lanes, 
#                               debug=args.debug)
        
#     trafficTool = TrafficTool(file_path="vids\\TLC00005.mp4", overlay_path="overlays\\Q11.png", output_dir="testest", debug=True)
    trafficTool = TrafficTool(debug=True)
    trafficTool.mainloop()