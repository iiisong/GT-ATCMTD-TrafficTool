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
                 max_length=10, 
                 parent=None, 
                 master=None, 
                 debug=False):
        
        super().__init__()
        
        # process input params
        self.file_path = file_path
        self.num_lanes = num_lanes
        self.display_lanes = display_lanes
        self.max_length = max_length
        self.parent = parent
        self.master = master
        self.debug = debug
        
        self.df = None
        
        # autoentry on excel
        self.default_val = 0
        
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
        self.display_lanes = display_lanes
        
        self.header = ["Time"] + ["L" + str(i + 1) for i in range(self.num_lanes)]
        self.curr_status = [self.default_val] * self.display_lanes
        
        for i in range(self.max_length):
            for j in range(self.num_lanes):
                if j < self.display_lanes:
#                     self.button_list[i][j]["state"] = "normal"
                    self.button_frame_list[i][j].grid()
                    if i == 0: self.header_frame_list[j].grid()
                else:
                    self.button_list[i][j]["state"] = "disabled"
                    self.button_frame_list[i][j].grid_remove()
                    if i == 0: self.header_frame_list[j].grid_remove()
        self.entry_frame.grid(columnspan=self.display_lanes)
                    
    def inputLaneStatus(self, lane, length):
        self.debug_print("input lane status")
        if length != self.default_val and self.curr_status[lane] == length:
            self.button_list[length - 1][lane].config(relief="raised", font="sans 10", bg="white")
            self.curr_status[lane] = self.default_val
            return
            
        self.curr_status[lane] = length
        
        self.debug_print((length, lane))
        self.debug_print(self.curr_status)

        for l in range(self.max_length):
            if l + 1 != length:
                self.button_list[l][lane].config(relief="raised", font='sans 10', bg="white")
        
        if length != self.default_val:
            sel_btn = self.button_list[length - 1][lane]
            sel_btn.config(relief="sunken", font='sans 10 bold', bg="yellow")
                
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
    
    def resetInput(self):
        self.debug_print("reset input")
        self.curr_status = [self.default_val] * self.display_lanes
        
        for l in range(self.max_length):
            for r in range(self.num_lanes):
                self.button_list[l][r].config(relief="raised", font='sans 10', bg="white")
    
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
        
        for i in range(self.max_length):
            for j in range(self.num_lanes):
                if j < self.display_lanes:
                    self.button_list[i][j]["state"] = "normal"
#                     self.button_frame_list[i][j].grid()
        
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
    
    # gets called in video panel
    def triggerClickEvent(self, pixel):
        print (pixe)
        

    def createTkPanel(self, num_lanes=None, display_lanes=None, max_length=None):
        self.num_lanes = self.num_lanes if num_lanes == None else num_lanes
        self.display_lanes = self.display_lanes if display_lanes == None else display_lanes
        self.max_length = self.max_length if max_length == None else max_length
        
        self.button_list = []
        self.button_frame_list = []
        self.header_frame_list = []
        
        fill=tk.BOTH
        expand=True
            
        for i in range(self.num_lanes):
            self.header_frame_list.append(ttk.Frame(
                master=self.parent,
                borderwidth=1
            ))
            self.header_frame_list[i].grid(row=0, column=i, sticky="nsew")
            
            header_label = tk.Label(master=self.header_frame_list[i], 
                     text=self.header[i + 1])
            header_label.pack(fill=fill, expand=expand)
            
        self.parent.rowconfigure(0, weight=0)
            
        for i in range(1, self.max_length + 1):
            self.parent.rowconfigure(i, weight=1) 
            
            self.button_list.append([])
            self.button_frame_list.append([])
            
            for j in range(self.num_lanes):
                self.parent.columnconfigure(j, weight=1) 
                
                self.button_frame_list[i - 1].append(ttk.Frame(
                    master=self.parent,
                    relief="raised",
                    borderwidth=1,
                ))
                self.button_frame_list[i - 1][j].grid(row=i, column=(j), sticky="nsew")
                
                self.button_list[i - 1].append(tk.Button(master=self.button_frame_list[i - 1][j], 
                                                     text=f"{i}",
                                                     font='sans 10',
                                                     bg="white",
                                                     state="disabled",
                                                     command=lambda j=j, i=i : self.inputLaneStatus(j, i)))
                self.button_list[i - 1][j].pack(fill=fill, expand=expand)
        
        self.entry_frame = ttk.Frame(
                    master=self.parent,
                    relief="raised",
                    borderwidth=1,
                )
        
        self.entry_frame.grid(row=(self.max_length + 1), column=0, rowspan=4, columnspan=self.display_lanes, sticky="nsew")
        self.parent.rowconfigure((self.max_length + 1), weight=1) 

        self.entryButton = tk.Button(master=self.entry_frame, 
                                     text=f"Enter Entry",
                                     font='sans 10',
                                     state="disabled",
                                     command=self.enterEntry)
        self.entryButton.pack(fill=fill, expand=expand)
        
    def setKeyBinds(self):
        self.master.bind("<space>", lambda x: self.enterEntry())
        
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
        
    return os.path.join("test_results", "QTest" + "_" + "TLC00420_c") + ".xlsx"

if __name__ == "__main__":
    root = Tk()
#     inpanel = InputPanel(file_path="vids\TLC00011.mp4", num_lanes=4, parent=root)
    input_panel = InputPanel(parent=root, master=root, debug=True)
    input_panel.loadLanes(4)
#     input_panel.setIndexFunc(testingIndexFunc)
    input_panel.updateTimeIndex(testingIndexFunc())
#     input_panel.setResultPathFunc(testingFilePathFunc)
    input_panel.updateResultPath(testingFilePathFunc())
    input_panel.setNextFunc(lambda: None)
    print("created object")
    root.mainloop()