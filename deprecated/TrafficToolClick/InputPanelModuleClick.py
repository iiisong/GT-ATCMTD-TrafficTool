import tkinter as tk
from tkinter import Tk, ttk, filedialog, messagebox
from PIL import Image, ImageTk

import cv2
import pandas as pd
import re
import os

from datetime import date, datetime, time, timedelta


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
    
class InputPanel(tk.Frame):
    def __init__(self, 
                 file_path=None, 
                 num_lanes=6, 
                 display_lanes=6, 
                 parent=None, 
                 master=None, 
                 debug=False):
        
        super().__init__()
        
        # process input params
        self.file_path = file_path
        self.num_lanes = num_lanes
        self.display_lanes = display_lanes
        self.parent = parent
        self.master = master
        self.debug = debug
        
        self.df = None
        
        self.settingLane = None
        
        # autoentry on excel
        self.default_val = None
        
        parent.rowconfigure(0,weight=1)
        parent.columnconfigure(0,weight=1)
        
        self.header = ["Time"] + ["L" + str(i + 1) for i in range(self.num_lanes)]
        
        self.time_index = None # store video time
        
        self.result_path = None
        self.getTimeIndex = None
        self.getResultPath = None
        self.nextFrame = None
        self.view_name = None # camera view name for file prefix
        
        self.curr_status = [self.default_val] * self.display_lanes
        
        self.input_pad = self.createTkPanel()
        
        self.loadLanes(self.display_lanes)
        
        self.setKeyBinds()
        
    def loadLanes(self, display_lanes, show=False):
        self.debug_print("load lanes")
        self.display_lanes = display_lanes
        
        self.header = ["Time"] + ["L" + str(i + 1) for i in range(self.num_lanes)]
        self.curr_status = [self.default_val] * self.display_lanes
        
        for i in range(self.num_lanes):
            if i < self.display_lanes:
                if self.view_name == None:
                    self.position_list[i][2]["state"] = "disabled"
                else:
                    self.position_list[i][2]["state"] = "normal"
                self.position_frame_list[i].pack(fill=tk.BOTH, expand=True)
            else:
                self.position_list[i][2]["state"] = "disabled"
                self.position_frame_list[i].pack_forget()
                    
    def inputLaneStatus(self, lane, pixel):
        self.debug_print("input lane status")
        
        self.debug_print((pixel, lane - 1))
        self.debug_print(self.curr_status)
        
        self.curr_status[lane] = pixel
        self.position_list[lane][1].config(text=str(pixel))
        self.position_list[lane][2].config(relief="raised")
                
    def loadLanesStatus(self):
        self.debug_print("load lanes status")
#         print(self.time_index)
        # requires time index set first to 
        if self.time_index == None: return
        
        self.debug_print("time index exists")
        # cannot load lanes data if none stored so early return
        if self.time_index not in self.df.index: 
            self.debug_print(self.time_index + " not found in " + str(self.df.index))
            self.debug_print(self.df)
            self.resetInput()
            return
        
        self.debug_print("time index found in df")
        
        # bad and hacky code below
        # update retrieved lanes
        temp_curr_status = self.df.loc[self.time_index].values.tolist()
        self.curr_status = [self.default_val] * self.display_lanes
        self.debug_print(temp_curr_status)
        
        for l in range(self.display_lanes):
            self.inputLaneStatus(l, temp_curr_status[l])
            
#     @timeit
    def loadDf(self, preload=False):
        self.debug_print("loading df")
        
        if self.result_path == None:
            self.debug_print("result path cannot be none")
            return
        
        # check if result file exists
        if not os.path.exists(self.result_path):
            self.debug_print("result file does not exist")
#             self.resetInput()
            
            # do nothing if attempting to preload nonexistent file
            if not preload: return 
            
            # create excel when not preloading
            self.debug_print("header: " + str(self.header))
            self.df = pd.DataFrame(columns=self.header[:self.display_lanes + 1])
            
            self.df.set_index("Time", inplace=True)
            
        # load existing excel
        else:
            self.debug_print("result file exists")
            self.df = pd.read_excel(self.result_path) # update df
            
            self.df.set_index("Time", inplace=True)
            
            # get starting time if preload
            if preload:
                self.debug_print("preloading")
                # retrieves time at preload which should be starting time
#                 self.time_index = self.getTimeIndex()
                self.loadLanesStatus()
            

    def enterEntry(self):
        if self.result_path == None:
            self.debug_print("entered entry but no result file selected")
            return self.resetInput()
        
        if self.time_index == None:
            self.debug_print("time index not set")
            messagebox.showinfo("Require Video", "needs video to enter into exel")
            return self.resetInput()
        
        self.loadDf() # 
        
        self.debug_print(self.time_index)
        
        self.debug_print("entered entry")
        self.df.loc[self.time_index] = self.curr_status[:self.display_lanes]
        self.debug_print("wrote into excel at " + self.result_path)
        self.df.to_excel(self.result_path)
        
        self.resetInput()
        
        if self.nextFrame != None:
            self.nextFrame() # calls updateTimeIndex() too
            self.debug_print("next")
            self.loadLanesStatus()
    
    # gets called in video panel
    def triggerClickEvent(self, event):
        if self.settingLane == None:
            self.debug_print("ignoring clicks when not setting lanes")
            return
        
        if self.imgSize == None:
            self.debug_print("img size must be processed first")
            return
            
        pixel = (float("{:.3f}".format((event.x - self.canvas.winfo_width() // 2 + self.imgSize[0] // 2) / self.imgSize[0])), 
                 float("{:.3f}".format((event.y - self.canvas.winfo_height() // 2 + self.imgSize[1] // 2) / self.imgSize[1])))
        
        if pixel[0] < 0 or pixel[1] < 0 or pixel[0] >= self.imgSize[0] or pixel[1] >= self.imgSize[1]:
            self.debug_print("click ignored as outside of image")
            return
        
        self.inputLaneStatus(self.settingLane - 1, str(pixel))
        self.settingLane = None
        
    def setCanvas(self, canvas):
        self.canvas = canvas
        self.canvas.bind("<Button-1>", self.triggerClickEvent)
    
    def setImgSize(self, size):
        self.imgSize = size
        
    def setButtonClicked(self, lane):
        if lane > self.display_lanes or self.position_list[lane - 1][2]["state"] == "disabled":
            return
        
        if isinstance(self.master.focus_get(), tk.Entry):
            return
        
        if self.settingLane == lane:
            self.debug_print("already setting")
            self.position_list[self.settingLane - 1][2].config(relief="raised")
            self.settingLane = None
            return
    
        self.settingLane = lane
        self.debug_print("setting new lane:" + str(self.settingLane - 1))
        self.position_list[self.settingLane - 1][2].config(relief="sunken")
        
        for i in range(self.display_lanes):
            if i == self.settingLane - 1:
                continue
            
            self.position_list[i][2].config(relief="raised")
        
    
    def resetInput(self):
        self.debug_print("reset input")
        self.curr_status = [self.default_val] * self.display_lanes
        
        for i in range(self.num_lanes):
            self.position_list[i][1].config(relief="ridge", 
                                            text="None", 
                                            font='sans 10')
    
    # sets the time, called from video panel
    def updateTimeIndex(self, time_index):
        self.debug_print("set time index")
        self.time_index = time_index
        
        if self.result_path != None:
            self.loadLanesStatus()
    
    # allows input panel to retrieve timeindex of video
    def setIndexFunc(self, func):
        self.debug_print("set time index func")
        self.getTimeIndex = func
        
    # sets the result path, called from video panel
    def updateResultPath(self, result_path):
        self.debug_print("set result path as " + result_path)
        self.result_path = result_path
        
        for i in range(self.num_lanes):
            if i < self.display_lanes:
                self.position_list[i][2]["state"] = "normal"
                self.position_frame_list[i].pack(fill=tk.BOTH, expand=True)
        
        self.entryButton["state"] = "normal"
        
        self.loadDf(preload=True)
        
    # allows input panel to retrieve result path of video
    def setResultPathFunc(self, func):
        self.debug_print("set result path func")
        self.getResultPath = func
        
    # allows input panel to go to next in video
    def setNextFunc(self, func):
        self.debug_print("set next func")
        self.nextFrame = func

    def createTkPanel(self, num_lanes=None, display_lanes=None):
        self.num_lanes = self.num_lanes if num_lanes == None else num_lanes
        self.display_lanes = self.display_lanes if display_lanes == None else display_lanes
        
        self.position_list = []
        self.position_frame_list = []
        
        fill=tk.BOTH
        expand=True
            
        # input panel
        inputBox = ttk.Frame(master=self.parent)
        inputBox.pack()
        
        # entry panel
        entryBox = ttk.Frame(master=self.parent)
        entryBox.pack(side="bottom")
        
        # create input lanes rows 
        for i in range(self.num_lanes):
            # create vertical header
            self.position_frame_list.append(ttk.Frame(
                master=self.parent,
                borderwidth=1
            ))
            self.position_frame_list[i].pack(fill=fill, expand=expand)
            
            self.position_list.append((tk.Label(master=self.position_frame_list[i], 
                                                text=self.header[i + 1]),
                                       tk.Label(master=self.position_frame_list[i],
                                                relief="ridge",
                                                text="None"),
                                       tk.Button(master=self.position_frame_list[i],
                                                 text="Set", 
                                                 state="disabled",
                                                 command=lambda x=i: self.setButtonClicked(x + 1))))
            self.position_list[i][0].pack(fill=fill, expand=expand, side="left")
            self.position_list[i][1].pack(fill=fill, expand=expand, side="left")
            self.position_list[i][2].pack(fill=fill, expand=expand, side="left")
            
        # create entry box
        frame = ttk.Frame(
                    master=self.parent,
                    relief="raised",
                    borderwidth=1)
        
        frame.pack(fill=fill, expand=expand, side="bottom")

        self.entryButton = tk.Button(master=frame, 
                                     text=f"Enter Entry",
                                     font='sans 10',
                                     state="disabled",
                                     command=self.enterEntry)
        self.entryButton.pack(fill=fill, expand=expand)
        
    def setKeyBinds(self):
        self.master.bind("<space>", lambda x: self.enterEntry())
        
        for i in range(10):
            self.master.bind(str(i + 1), lambda e, x=i: self.setButtonClicked(x + 1))
        
        # enter unbounded because of potential issuess with user expectations of the entry boxes
        # also too lazy to code for widget focusing logic
#         self.master.bind("<Return>", lambda x: self.enterEntry())
        
    def debug_print(self, string):
        if self.debug: print(string)

def testingIndexFunc():
    return "4200-04-20 04:20:00"

def testingFilePathFunc():
    if not os.path.exists("test_results"):
        os.mkdir("test_results")
        
    return os.path.join("test_results", "QTest" + "_" + "TLC00420_click") + ".xlsx"


if __name__ == "__main__":
    root = Tk()
    testWindow = tk.Toplevel(root)
    tf = tk.Frame(testWindow)
    tf.pack(fill=tk.BOTH, expand=True)
    tp = testPanel(tf)
#     tp.pack()
    
#     inpanel = InputPanel(file_path="vids\TLC00011.mp4", num_lanes=4, parent=root)
    input_panel = InputPanel(parent=root, master=root, debug=True)
    input_panel.loadLanes(4)
#     input_panel.setIndexFunc(testingIndexFunc)
    input_panel.updateTimeIndex(testingIndexFunc())
#     input_panel.setResultPathFunc(testingFilePathFunc)
    input_panel.updateResultPath(testingFilePathFunc())
    input_panel.setNextFunc(lambda: None)
    input_panel.setCanvas(tp.getCanvas())
    tp.setImgSizeFunc(input_panel.setImgSize)
    print("created object")
    root.mainloop()
    root.mainloop()