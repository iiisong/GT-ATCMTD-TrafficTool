# InputPanel v1.1.0

import tkinter as tk # ui library
from tkinter import Tk, ttk, filedialog, messagebox # ui library

from PIL import Image, ImageTk # video processing library
import cv2 # video processing library

import pandas as pd # output data entry library

import re # text parser library
import os # directory libraries and such

from datetime import date, datetime, time, timedelta # system time library


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
    '''Input Panel creates, displays, and manipulates the input panel portion of the tool and writes to output file.
    Takes in user input for data values.
    Takes in file path, lane information, and time information from Output Panel.
    Does NOT deal with any of the video displays.
    '''
    def __init__(self, 
                 file_path=None, 
                 num_lanes=6, 
                 display_lanes=6, 
                 max_length=10, 
                 parent=None, 
                 master=None, 
                 debug=False):
        '''Inits InputPanel class.
        Creates all the Tkinter objects.
        
        Args:
            file_path: optional specified video name to load on startup, none loaded if None (default: None)
            num_lanes: max number of lanes to display (default to 6)
            max_length: maximum input value to display (default to 10)
            parent: parent tkinter object
            master: root tkinter object
            debug: debug mode for addit information
        '''
        
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
        
        # default entry on excel when no option selected
        self.default_val = 0
        
        # configure rows
        parent.rowconfigure(0,weight=1)
        parent.columnconfigure(0,weight=1)
        
        # create header row
        self.header = ["Time"] + ["L" + str(i + 1) for i in range(self.num_lanes)]
        
        # store video time
        self.time_index = None 
        
        # functions passed in from VideoPanel
        self.result_path = None
        self.getTimeIndex = None
        self.getResultPath = None
        
        # next frame
        self.nextFrame = None
        # camera view name for file prefix
        self.view_name = None 
        
        self.curr_status = [self.default_val] * self.display_lanes
        
        self.input_pad = self.createTkPanel()
        
        self.loadLanes(self.display_lanes)
        
        self.setKeyBinds()

        
    def loadLanes(self, display_lanes, show=False):
        '''Loads input panels with set number of lanes to display.
        
        Args:
            display_lanes: number of lanes to display
            show: show number of lanes
        '''
        # set display lanes to input
        self.display_lanes = display_lanes
        
        # update header row
        self.header = ["Time"] + ["L" + str(i + 1) for i in range(self.num_lanes)]
        # create new current status length
        self.curr_status = [self.default_val] * self.display_lanes
        
        # iterate through panel and disable all those in deactivated lanes
        for i in range(self.max_length + 1):
            for j in range(self.num_lanes):
                # only display lanes 
                if j < self.display_lanes:
#                     self.button_list[i][j]["state"] = "normal"
                    self.button_frame_list[i][j].grid()
                    if i == 0: 
                        self.header_frame_list[j].grid() # add header
                        self.incre_frame_list[j].grid() # add incre
                        self.decre_frame_list[j].grid() # add decre
                else:
                    self.button_list[i][j]["state"] = "disabled"
                    self.button_frame_list[i][j].grid_remove()
                    if i == 0: 
                        self.header_frame_list[j].grid_remove() # remove header
                        self.incre_frame_list[j].grid_remove() # remove incre
                        self.decre_frame_list[j].grid_remove() # remove decre
#         self.noChange_frame.grid(columnspan=self.display_lanes)
        self.entry_frame.grid(columnspan=self.display_lanes)
                    
    # def exceedLaneStatus(self, lane):
    #     '''Update status of lane to indicate that the queue exceeds the camera view
        
    #     Args:
    #         lane: lane to update status of
    #     '''
        

    def inputLaneStatus(self, lane, length):
        '''Update status of the buttons on a specified lane.
        
        Args: 
            lane: lane to update status of
            length: the new value 
        '''
        # debug info
        self.debug_print("input lane status")
        
        # reset to default when click current selected non-default, de-select behavior
        if length != self.default_val and self.curr_status[lane] == length:
            # debug info
            self.debug_print("current button re-pressed, button raised")
            # reset current selected to raised
            try:
                self.button_list[length][lane].config(relief="raised", 
                                                      font="sans 10", 
                                                      bg="white", 
                                                      highlightbackground="systemWindowBackgroundColor")
            except:
                self.button_list[length][lane].config(relief="raised", 
                                                      font="sans 10", 
                                                      bg="white", 
                                                      highlightbackground="systemWindow")

            # set current value to default
            self.curr_status[lane] = self.default_val
            return
        
        # set current value to new value
        self.curr_status[lane] = length
        
        # debug info
        self.debug_print(f"lane, length input: {(lane, length)}")
        self.debug_print(f"status: {self.curr_status}")

        # iterate through lane button
        for l in range(self.max_length + 1):
            # if not new selection, deselect it
            if l != length:
                try:
                    self.button_list[l][lane].config(relief="raised", 
                                                     font='sans 10', 
                                                     bg="white", 
                                                     highlightbackground="systemWindowBackgroundColor")  
                except:
                    self.button_list[l][lane].config(relief="raised", 
                                                     font="sans 10", 
                                                     bg="white", 
                                                     highlightbackground="systemWindow")
        
        # set new value if not-default (default already set)
        #if length != self.default_val:
        # debug config
        self.debug_print("new button pressed down")
        # find button
        sel_btn = self.button_list[length][lane]
        # set button to sunken
        sel_btn.config(relief="sunken", 
                       font='sans 10 bold', 
                       bg="yellow", 
                       highlightbackground="yellow")
                
    def loadLanesStatus(self):
        '''Load the inputted value of lanes.'''
        # debug info
        self.debug_print("load lanes status")
        # requires time index set first to 
        if self.time_index == None: return
        
        # debug info
        self.debug_print("time index exists")
        # cannot load lanes data if none stored so early return
        if self.time_index not in self.df.index: 
            self.debug_print(self.time_index + " not found in " + str(self.df.index))
            self.debug_print(self.df)
            self.resetInput()
            return
        
        # debug info
        self.debug_print("time index found in df")
        
        # bad and hacky code below
        # retrieve next default or existing value
        new_status = self.df.loc[self.time_index].values.tolist()
        self.curr_status = [self.default_val] * self.display_lanes
        # debug info
        self.debug_print(f"new status: {new_status}")
        self.updateLanesStatus(new_status)
        
    def updateLanesStatus(self, new_status):
        '''Update entry pad with status values.
        
        Args:
            new_status: new status to update pad with'''
        # set next value 
        for l in range(self.display_lanes):
            self.inputLaneStatus(l, new_status[l])
            
#     @timeit
    def loadDf(self, preload=False):
        '''Loads dataframe.
        
        Args:
            preload: preload dataframe when loading new dataframe
        '''
        # debug info
        self.debug_print("loading df")
        
        # check if result path specified
        if self.result_path == None:
            self.debug_print("result path cannot be none")
            return
        
        # if result file not exists create result file
        if not os.path.exists(self.result_path):
            # debug info
            self.debug_print("result file does not exist")
#             self.resetInput()
            
            # do nothing if attempting to preload nonexistent file
            if not preload: return 
            
            # create excel when not preloading
            self.debug_print("header: " + str(self.header))
            self.df = pd.DataFrame(columns=self.header[:self.display_lanes + 1])
            
            self.df.set_index("Time", inplace=True)
            
        # load existing excel if result file already exists
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
        '''Enters lane status entry into dataframe and write to excel.'''
        
        # reset panel if no result file selected
        if self.result_path == None:
            self.debug_print("entered entry but no result file selected")
            return self.resetInput()
        
        # reset panel if video not provided (detected by time index not set) 
        if self.time_index == None:
            self.debug_print("time index not set")
            messagebox.showinfo("Require Video", "needs video to enter into exel")
            return self.resetInput()
        
        # make sure df is up-to-date
        self.loadDf() 
        
        # debug info
        self.debug_print(self.time_index)
        
        # enter entry into dataframe
        self.debug_print("entered entry")
        self.df.loc[self.time_index] = self.curr_status[:self.display_lanes]
        # write dataframe to excel
        self.debug_print("wrote into excel at " + self.result_path)
        self.df.to_excel(self.result_path)
        
        # reset input 
        self.resetInput()
        
        # loads next lane status from dataframe [default if not already defined]
        if self.nextFrame != None:
            self.nextFrame() # calls updateTimeIndex() too
            self.debug_print("next")
            self.loadLanesStatus()
            
    # ===IN-PROGRESS===
#     def noChangeEntry(self):
#         '''Set same values as previous entry.'''
#         # debug info
#         self.debug_print("no change triggered")
        
#         # pull immediate previous entry
#         new_status = self.df.shift(1).loc[self.time_index]
        
#         # make sure not first-line
#         if not new_status.isna().all():
#             self.debug_print(f"setting previous values: {new_status.values.tolist()}")
#             self.updateLanesStatus(new_status.tolist())
            
    def increLaneEntry(self, lane):
        '''Increment lane entry value by 1.
        
        Args:
            lane: lane to increase by 1
        '''
        # check if lane is out of bounds, do nothing
        if lane < 0 or lane >= self.display_lanes:
            # debug info
            self.debug_print("lane out of bounds")
            return
        
        # check if max length already
        if self.curr_status[lane] >= self.max_length:
            # debug info
            self.debug_print("cannot increment past max value")
            return
        
        # incre value by 1
        self.inputLaneStatus(lane, self.curr_status[lane] + 1)
        
    def decreLaneEntry(self, lane):
        '''Decrement lane entry value by 1.
        
        Args:
            lane: lane to decrease by 1
        '''
        # check if lane is out of bounds, do nothing
        if lane < 0 or lane >= self.display_lanes:
            # debug info
            self.debug_print("lane out of bounds")
            return
        
        # check if min length already
        if self.curr_status[lane] <= 0:
            # debug info
            self.debug_print("cannot decrement past min value")
            return
        
        # incre value by 1
        self.inputLaneStatus(lane, self.curr_status[lane] - 1)
    
    def resetInput(self):
        '''Resets/clears input panel and selection.'''
        # debug info
        self.debug_print("reset input")
        # clear current entry data
        self.curr_status = [self.default_val] * self.display_lanes
        
        # reset all the buttons in the panel
        for l in range(self.max_length + 1):
            for r in range(self.num_lanes):
                try:
                    self.button_list[l][r].config(relief="raised", 
                                                  font='sans 10', 
                                                  bg="white",
                                                  highlightbackground="systemWindowBackgroundColor")
                except:
                    self.button_list[l][r].config(relief="raised", 
                                                  font='sans 10', 
                                                  bg="white",
                                                  highlightbackground="systemWindow")
    
    def updateTimeIndex(self, time_index):
        '''Retrieves the frame time for the data entry, called from video panel.
        
        Args:
            time_index: time
        '''
        # debug info
        self.debug_print("set time index")
        # store time
        self.time_index = time_index
        
        # load lanes if file exists
        if self.result_path != None:
            self.loadLanesStatus()
    
    # unused
    def setIndexFunc(self, func):
        '''Sets function to retrieve time index of video from Video Panel.
        Linked up on root Traffic Tool object.
        
        Args:
            func: function from video panel to export time index
        '''
        self.debug_print("set time index func")
        self.getTimeIndex = func
        
    def updateResultPath(self, result_path):
        '''Updates file path of the excel output.
        
        Args:
            result path: file path of the excel output.
        '''
        self.debug_print("set result path as " + result_path)
        self.result_path = result_path
        
        # when result path entered, un-freeze the input panels
        for i in range(self.max_length + 1):
            for j in range(self.num_lanes):
                if j < self.display_lanes:
                    self.button_list[i][j]["state"] = "normal"
                    self.incre_list[j]["state"] = "normal"
                    self.decre_list[j]["state"] = "normal"
#                     self.button_frame_list[i][j].grid()
        
        self.entryButton["state"] = "normal"
        
        # preload to check for existing info
        self.loadDf(preload=True)
    
    # unused
    def setResultPathFunc(self, func):
        '''Sets function to to set result path of video from Video Panel.
        Linked up on root Traffic Tool object.
        
        Args:
            func: function from video panel to export time index
        '''
        self.debug_print("set result path func")
        self.getResultPath = func
        
    # allows input panel to go to next in video
    def setNextFunc(self, func):
        '''Sets function to to call "next" chunk in Video Panel from Input Panel.
        Linked up on root Traffic Tool object.
        
        Args:
            func: function from video panel to go to next time chunk
        '''
        self.debug_print("set next func")
        self.nextFrame = func

    def createTkPanel(self, num_lanes=None, display_lanes=None, max_length=None):
        '''Creates Tkinter objects.
        
        Args:
            num_lanes: number of lanes to display buttons (default to predefined)
            display_lanes: number of lanes to display (default to predefined)
            max_length: max input button for user entry (default to predefined)
        '''
        # process input params
        self.num_lanes = self.num_lanes if num_lanes == None else num_lanes
        self.display_lanes = self.display_lanes if display_lanes == None else display_lanes
        self.max_length = self.max_length if max_length == None else max_length
        
        # create tkinter list object for iteration
        self.button_list = [] # list of buttons
        self.incre_list = []
        self.decre_list = []
        self.button_frame_list = [] # button frames
        self.header_frame_list = [] # header
        self.incre_frame_list = [] # increment by 1 button
        self.decre_frame_list = [] # decrement by 1 button
        self.exceed_frame_list = [] # queue exceeds camera view button
        
        # tkinter configs
        fill=tk.BOTH
        expand=True
            
        # create header and incre/decre rows
        for i in range(self.num_lanes):
            # header
            self.header_frame_list.append(ttk.Frame(
                master=self.parent,
                borderwidth=1
            ))
            self.header_frame_list[i].grid(row=0, column=i, sticky="nsew")
            
            header_label = tk.Label(master=self.header_frame_list[i], 
                     text=self.header[i + 1])
            header_label.pack(fill=fill, expand=expand)
            
            # incre row
            self.incre_frame_list.append(ttk.Frame(
                master=self.parent,
                borderwidth=1
            ))
            self.incre_frame_list[i].grid(row=1, column=i, sticky="nsew")
            
            self.incre_list.append(tk.Button(master=self.incre_frame_list[i], 
                                   text="+1",
                                   font='sans 10',
                                   bg="white",
                                   state="disabled",
                                   command=lambda i=i: self.increLaneEntry(i)))
            self.incre_list[i].pack(fill=fill, expand=expand)
            
            # decre row
            self.decre_frame_list.append(ttk.Frame(
                master=self.parent,
                borderwidth=1
            ))
            self.decre_frame_list[i].grid(row=2, column=i, sticky="nsew")
            
            self.decre_list.append(tk.Button(master=self.decre_frame_list[i], 
                                    text="-1",
                                    font='sans 10',
                                    bg="white",
                                    state="disabled",
                                    command=lambda i=i: self.decreLaneEntry(i)))
            self.decre_list[i].pack(fill=fill, expand=expand)
            
        self.parent.rowconfigure(0, weight=0)
            
        # create each data entry row
        for i in range(0, self.max_length + 1):
            self.parent.rowconfigure(i + 3, weight=1) 
            
            self.button_list.append([])
            self.button_frame_list.append([])
            
            # create each data entry per lane
            for j in range(self.num_lanes):
                self.parent.columnconfigure(j, weight=1) 
                
                self.button_frame_list[i].append(ttk.Frame(
                    master=self.parent,
                    relief="raised",
                    borderwidth=1,
                ))
                self.button_frame_list[i][j].grid(row=i+3, column=j, sticky="nsew")
                try:
                    self.button_list[i].append(tk.Button(master=self.button_frame_list[i][j], 
                                                         text=f"{i}",
                                                         font='sans 10',
                                                         bg="white",
                                                         highlightbackground="systemWindowBackgroundColor",
                                                         state="disabled",
                                                         command=lambda j=j, i=i : self.inputLaneStatus(j, i)))
                except:
                    self.button_list[i].append(tk.Button(master=self.button_frame_list[i][j], 
                                                         text=f"{i}",
                                                         font='sans 10',
                                                         bg="white",
                                                         highlightbackground="systemWindow",
                                                         state="disabled",
                                                         command=lambda j=j, i=i : self.inputLaneStatus(j, i)))
                self.button_list[i][j].pack(fill=fill, expand=expand)

        # # ===IN-PROGRESS===
        # # create (+) button (when queue exceeds camera view)
        # for i in range(self.num_lanes):
        #     self.exceed_frame_list.append(ttk.Frame(
        #         master=self.parent,
        #         relief="raised"
        #         borderwidth=1
        #     ))
        #     self.button_frame_list[i].grid(row=(self.max_length + 4), column=self.display_lanes, sticky="nsew")
            
        #     self.exceed_frame_list.append(tk.Button(master=self.incre_frame_list[i], 
        #                            text="(+)",
        #                            font='sans 10',
        #                            bg="white",
        #                            state="disabled",
        #                            command=lambda i=i: self.exceedLaneStatus(i)))
        #     self.exceed_frame_list[i].pack(fill=fill, expand=expand)

        # ===IN-PROGRESS===
        # create no change entry button
#         self.noChange_frame = ttk.Frame(
#                     master=self.parent,
#                     relief="raised",
#                     borderwidth=1,
#             )
        
#         self.noChange_frame.grid(row=(self.max_length + 4), column=0, columnspan=self.display_lanes, sticky="nsew")
#         self.parent.rowconfigure((self.max_length + 4), weight=1) 

#         self.noChangeButton = tk.Button(master=self.noChange_frame, 
#                                      text=f"No Change",
#                                      font='sans 10',
#                                      state="normal",
#                                      command=self.noChangeEntry)
#         self.noChangeButton.pack(fill=fill, expand=expand)
        
        # create enter entry button
        self.entry_frame = ttk.Frame(
                    master=self.parent,
                    relief="raised",
                    borderwidth=1,
            )
        
        self.entry_frame.grid(row=(self.max_length + 4), column=0, columnspan=self.display_lanes, sticky="nsew")
        self.parent.rowconfigure((self.max_length + 4), weight=1) 

        self.entryButton = tk.Button(master=self.entry_frame, 
                                     text=f"Enter Entry\n[Space]",
                                     font='sans 10',
                                     state="disabled",
                                     command=self.enterEntry)
        self.entryButton.pack(fill=fill, expand=expand)
        
    def setKeyBinds(self):
        '''Set keybinds for keyboard shortcuts.'''
        # enter entry button
        self.master.bind("<space>", lambda x: self.enterEntry())
        
        # enter unbounded because of potential issuess with user expectations of the entry boxes
        # also too lazy to code for widget focusing logic
#         self.master.bind("<Return>", lambda x: self.enterEntry())
        
    def debug_print(self, string):
        '''Print only if debug mode is on.
        
        Args:
            string: string to print
        '''
        if self.debug: print(string)

            
# testing functions
def testingIndexFunc():
    return "4200-04-20 04:20:00"

def testingFilePathFunc():
    if not os.path.exists("test_results"):
        os.mkdir("test_results")
        
    return os.path.join("test_results", "QTest" + "_" + "TLC00420_c") + ".xlsx"

if __name__ == "__main__":
    root = Tk()
#     inpanel = InputPanel(file_path="vids\TLC00011.mp4", num_lanes=4, parent=root)
    input_panel = InputPanel(parent=root, max_length=20, master=root, debug=True)
    input_panel.loadLanes(4)
#     input_panel.setIndexFunc(testingIndexFunc)
    input_panel.updateTimeIndex(testingIndexFunc())
#     input_panel.setResultPathFunc(testingFilePathFunc)
    input_panel.updateResultPath(testingFilePathFunc())
    input_panel.setNextFunc(lambda: None)
    print("created object")
    root.mainloop()