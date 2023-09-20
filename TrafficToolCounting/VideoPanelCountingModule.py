# # VideoPanel v1.1.0

# library imports
import tkinter as tk # ui library
from tkinter import Tk, ttk, filedialog, messagebox # ui library

from PIL import Image, ImageTk, ImageOps # video processing library
import cv2 # image processing library

import os # directory libraries and such

from datetime import date, datetime, time, timedelta # standard time library for time calcs

# helper python code
import timeParse # extract time data from frames
import ViewLanesDict as vld # files with preset number of lanes for each views

# timers for efficiency testing
from functools import wraps
import time as ttime

# timer function
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

class VideoPanel():
    '''Video Panel creates, displays, and manipulates the video processing portion of the tool.
    Takes in all video inputs and view information.
    Passes file path, lane information, and time information to Input Panel.
    Does NOT write to any file or take in output user data.
    '''
    def __init__(self, 
                 init_index=0, 
                 time_chunk=1, 
                 output_dir=None,
                 file_path=None, 
                 view_name=None,
                 vids_file_path=".\\vids\\", 
                 parent=None,
                 master=None,
                 debug=False):
        '''Initializes VideoPanel class.
        Creates up all the tkinter objects.
        
        Args:
            init_index: starting frame [note: the first frame of the next second is the practical start]
            time_chunk: time gap between each frame (default: 5 sec)
            output_dir: optional specified .xlsx result filepath, generates automatically later if None (default: None)
            file_path: optional specified video name to load on startup, none loaded if None (default: None)
            view_name: optional specified view name to load on startup, none specified if None (default: None)
            parent: parent tkinter object (default: None)
            master: root tkinter object (default: None)
            debug: debug mode with additional detailed print messages
        '''    
        super().__init__()
        
        # process input params
        self.init_index = init_index
        self.time_chunk = timedelta(seconds=time_chunk)
        self.file_path = file_path # potentially none, deal with it later in _load()
        self.view_name = view_name # potentially None deal with it later in _load_overlay()
        self.vids_file_path = vids_file_path # currently unused
        self.parent = parent
        self.master = master
        self.debug = debug
        
        # external functions to call from other files
        self.loadLanesFunc = None # loads the lanes settings
        self.timeIndexFunc = None # returns timestamp of frame
        self.resultPathFunc = None # returns result filepath 
        
        # deal with result directory
        self.output_dir = "results" if output_dir == None else output_dir
        
        # create path if not exist
        if os.path.exists(self.output_dir) == False:
            os.makedirs(self.output_dir)
        
        # vid and view states
        self.vid_loaded = False
        self.view_selected = False
        self.has_set = False
        
        # neighbor/relative frame [-1 for 1 frame back, 0 for current frame, 1 for 1 frame forward]
        self.relative_frame = 0
        
        # timestamp of frame
        self.time = None
        
        self.parent.rowconfigure(0,weight=1)
        self.parent.columnconfigure(0,weight=1)
        
        # time frame setup
        self.time_frame = ttk.Frame(master=self.parent,
                                    relief="groove",
                                    borderwidth=1)
        self.time_frame.grid(row=0, column=0, sticky="nsew")
        self.time_label = tk.Label(master=self.time_frame, text="Camera Time:")
        self.time_label.pack()
        self.parent.rowconfigure(0, weight=0)
    
        # video frame setup
        self.vid_frame = ttk.Frame(master=self.parent,
                                    relief="groove",
                                    borderwidth=1)
        self.vid_frame.grid(row=1, column=0, rowspan=3, sticky="nsew", pady=5)
        self.vid_frame.bind("<Configure>", self._resize_image) # make vid frame dynamic
        self.parent.rowconfigure(1, weight=5)
        
        self.curr_image = None # dumbest thing ever, avoids python tkinter garbage collection bug by saving reference
        self.curr_overlay = None # dumbest thing ever, avoids python tkinter garbage collection bug by saving reference
        
        # controls frame setup
        self.controls_frame = ttk.Frame(master=self.parent,
                                    relief="groove",
                                    borderwidth=1)
        self.controls_frame.grid(row=5, column=0, rowspan=3, sticky="nsew", padx=3, pady=3)
        self.parent.rowconfigure(5, weight=0)
        
        # buttons
        fill, expand = tk.BOTH, True
        
        # make each "column" of button dynamic to widget width
        for i in range(6):
            self.controls_frame.columnconfigure(i, weight=1)#, uniform="row")
            
        # make each "row" of button dynamic to widget height
        for i in range(2):
                self.controls_frame.rowconfigure(i, weight=1, uniform="column")
                
        # start time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=0, sticky="nsew", pady=5, padx=5)

        self.start_button = tk.Button(master=frame, 
                                 text=f"Start",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpStart)
        self.start_button.pack(fill=fill, expand=expand)
        
        # Long (*-10) back time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)

        self.double_back_button = tk.Button(master=frame, 
                                 text=f"-{10 * self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpLongBackChunk)
        self.double_back_button.pack(fill=fill, expand=expand)
        
        # back (*-5) time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=1, sticky="nsew", pady=5, padx=5)

        self.back_button = tk.Button(master=frame, 
                                 text=f"-{5 * self.time_chunk.total_seconds()}s\n[←]",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpBackChunk)
        self.back_button.pack(fill=fill, expand=expand)

        # short (*-1) back time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=2, sticky="nsew", pady=5, padx=5)

        self.double_next_button = tk.Button(master=frame, 
                                 text=f"+{self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpShortNextChunk)
        self.double_next_button.pack(fill=fill, expand=expand)

        # Short (*1) next time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=3, sticky="nsew", pady=5, padx=5)

        self.double_next_button = tk.Button(master=frame, 
                                 text=f"+{self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpShortNextChunk)
        self.double_next_button.pack(fill=fill, expand=expand)
        
        # next (*5) time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=4, sticky="nsew", pady=5, padx=5)

        self.next_button = tk.Button(master=frame, 
                                 text=f"+{5 * self.time_chunk.total_seconds()}s\n[→]",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpNextChunk)
        self.next_button.pack(fill=fill, expand=expand)
        
        # Long (*10) next time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=5, sticky="nsew", pady=5, padx=5)

        self.double_next_button = tk.Button(master=frame, 
                                 text=f"+{10 * self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpLongNextChunk)
        self.double_next_button.pack(fill=fill, expand=expand)
        
        # end time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=5, sticky="nsew", pady=5, padx=5)

        self.end_button = tk.Button(master=frame, 
                                 text=f"End",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpEnd)
        self.end_button.pack(fill=fill, expand=expand)
        
        # jump frame button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=1, sticky="nsew", pady=5, padx=5)
        
        frame.rowconfigure(0, weight=1)

        self.jump_chunk_button = tk.Button(master=frame, 
                                 text=f"Jump Frame",
                                 font='sans 7',
                                 bg="white",
                                 command=self._jumpChunk)
        self.jump_chunk_button.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=5)#, uniform="row")
        
        def callback(P):
            '''Restrict to only integer input.'''
            if str.isdigit(P) or P == "":
                return True
            else:
                return False
        self.jump_chunk_entry = tk.Entry(master=frame, 
                                         width=5,
                                         justify="center", 
                                         validate='all', 
                                         validatecommand=(frame.register(callback), '%P')) 
        self.jump_chunk_entry.grid(row=0, column=1, sticky="nsew")
#         frame.columnconfigure(1, weight=1)#, uniform="row")

        # neighbor frames buttons
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=2, sticky="nsew", pady=5, padx=5)
        
        self.rel_offset = 0
        self.rel_offset_buttons = []
        self.rel_offset_buttons = [tk.Button(master=frame, 
                                            text=f"-1F",
                                            font='sans 8',
                                            bg="white",
                                            command=lambda: self._displayRelativeFrame(-1, btn=True)),
                                  tk.Button(master=frame, 
                                            text=f"Back",
                                            font='sans 8',
                                            bg="white",
                                            command=lambda: self._displayRelativeFrame(0, btn=True)),
                                  tk.Button(master=frame, 
                                            text=f"+1F",
                                            font='sans 8',
                                            bg="white",
                                            command=lambda: self._displayRelativeFrame(1, btn=True))]
        self.rel_offset_buttons[0].pack(fill=fill, expand=expand, side=tk.LEFT)
        self.rel_offset_buttons[1].pack(fill=fill, expand=expand, side=tk.LEFT)
        self.rel_offset_buttons[2].pack(fill=fill, expand=expand, side=tk.LEFT)
        
            
        # load video button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=3, sticky="nsew", pady=5, padx=5)

        self.load_button = tk.Button(master=frame, 
                                 text=f"Load Video",
                                 font='sans 10',
                                 bg="white",
                                 command=self._load)
        self.load_button.pack(fill=fill, expand=expand)
        
        # select view selection
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=4, sticky="nsew", pady=5, padx=5)
        
        frame.rowconfigure(0, weight=1)

        self.view_text = tk.StringVar()
        self.select_view_button = tk.Button(master=frame, 
                                 text=f"Set View",
                                 font='sans 7',
                                 bg="white",
                                 command=lambda: self._selectView(self.view_text.get()))
        self.select_view_button.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=5)
        self.select_view_entry = tk.Entry(master=frame, 
                                         width=5,
                                         justify="center",
                                         textvariable=self.view_text) 
        self.select_view_entry.grid(row=0, column=1, sticky="nsew")
        
        # autoload if initialized
        if self.file_path != None:
            self.debug_print("loading preset video")
            self._load(file_path_known=True)
        if self.view_name != None:
            self.debug_print("selecting view")
            self._selectView(view_name)
            
        self._update_display()
            
        self._setKeyBinds()
    
    def _load(self, file_path_known=False):
        '''Loads the video.
        
        Args:
            file_path_known: whether or filepath already known or open file explorer
        '''
        
        # if file path not known, open file explorer to select file
        if file_path_known == False:
            self.file_path = filedialog.askopenfilename() # opens file explorer to select file
            
        # get file base-name (excludes parent directories)
        file_name_raw = os.path.basename(self.file_path).split(".")
        
        # check if not a directory
        if (len(file_name_raw) == 1): return
    
        # alert if not mp4 file
        if (file_name_raw[1] != "mp4"):
            self.debug_print("file must be a mp4")
            messagebox.showinfo("Wrong File Format", "video file must be a .mp4")
            return # early return 
        
        # filename (excludes parent directories and file type)
        self.file_name = file_name_raw[0]
        
        self.debug_print("file loaded: " + str(self.file_path))
        
        # determines video properties
        self._video_properties()
        
        self.vid_frame.update() # unsure if needed
        self._displayRelativeFrame(0) # default to target relative frame
        
        # video setup if not already loaded
        if not self.vid_loaded:
            # video canvas setup
            self.vid_canvas = tk.Canvas(self.vid_frame)
            self.vid_canvas.pack(fill=tk.BOTH, expand=True)
            self.img = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
            self.img_tk = ImageTk.PhotoImage(self.img, master=self.vid_frame)
            self.curr_image = self.img_tk
            self.image = self.vid_canvas.create_image(self.vid_frame.winfo_width() // 2, 
                                                      self.vid_frame.winfo_height() // 2,
                                                      image=self.img_tk)
        # update if loaded
        else:
            self._update_display()
        
        # update frame time
        self.time = timeParse.getDateTime(self.frame)
        curr_chunk = int((self.time - self.start_time).total_seconds() // self.time_chunk.total_seconds() + 1)
        self.time_label.config(text = f"Camera Time: {self.getTimeStr()}   Frame: {str(curr_chunk)}/{str(self.num_chunks)}")
                
        self.vid_loaded = True
        
        if self.timeIndexFunc != None:
            self.timeIndexFunc(self.getTimeStr())
            # debug info
            self.debug_print("set time index to input panel")
            
        
        # if view already selected, set result path
        if self.view_selected:
            if self.resultPathFunc != None:
                self.resultPathFunc(self.getResultFilePath())
            else:
                self.debug_print("update result path func with new vid")

    def _selectView(self, view_name):
        '''Selects the view to set correct input panel and output file.
        
        Args:
            view_name: name of view file (identifies the corresponding view)
        '''
        # setting display
        if self.has_set:
            self.has_set = False
            self.select_view_entry.config(state="normal")
            self.select_view_button.config(text="set view")
            return
            
        # early return if no file set
        if view_name == "":
            return
        
        # set view value
        self.view_name = view_name
        self.view_selected = True
        
        self.debug_print("set view")
        
        # require vid loaded
        if not self.vid_loaded:
            self.debug_print("vid not loaded")
            return
        
        self.debug_print("new result path: " + self.getResultFilePath())
            
        # if the view not found in preset dictionary of views to lane nums
        if self.view_name not in vld.view_to_lanes:
            self.debug_print("number of lanes has not been set up")
            return
        
        # checks if input panel function set up
        if self.loadLanesFunc != None and self.view_selected:
            # loads input panel with the number of lanes
            self.loadLanesFunc(display_lanes=vld.view_to_lanes[self.view_name])
        else:
            self.debug_print("cannot set input panel length without input panel setup func")
            return
            
        # sets resultpathfunction if not set up
        if self.resultPathFunc != None:
            self.debug_print("set result path")
            self.resultPathFunc(self.getResultFilePath())
        
        if not self.has_set:
            self.has_set = True
            self.view_text.set(view_name)
            self.select_view_entry.config(state="disabled")
            self.select_view_button.config(text="reset view")
        
    def _displayRelativeFrame(self, rel, btn=False):
        '''Sets the correct relative frame to display and sets button background accordingly.
        Allows user to see the frames around the target frame to determine movement.
        
        Args:
            rel: the relative frame to display (when default to None, set button attributes only)
            btn: whether triggered by relative frame buttons, need update display if from button
        '''
        # debug info
        self.debug_print(f"Displaying {rel} frame")
        self.rel_offset = rel
        
        for btn in range(len(self.rel_offset_buttons)):
            if btn == rel + 1:
                self.rel_offset_buttons[btn].config(relief="sunken",
                                                   highlightbackground="yellow")
            else:
                try:
                    self.rel_offset_buttons[btn].config(relief="raised",
                                                       highlightbackground="systemWindowBackgroundColor")
                except:

                    self.rel_offset_buttons[btn].config(relief="raised",
                                                       highlightbackground="systemWindow")
        if btn: self._update_display()
            
            
    def getResultFilePath(self):
        '''Retrieves result path.'''
        # early termination if vid or view not loaded/selected
        if (self.vid_loaded == False or self.view_selected == False):
            return None
        
        # generate result filepath
        return os.path.join(self.output_dir, self.view_name + "_" + self.file_name + "_c") + ".xlsx"
    
    def _video_properties(self):
        '''Calculates video properties like start time, fps, etc.'''
        
        # define capture
        self.cap = self._getCapture(self.file_path)
        
        # extract properties pt1
        self.dims = self.cap.read()[1].shape # dimensions
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) # number of frames
        
        
        # extract properties pt2
        self.fps = self._getFPS(self.cap) # frames per second (video framerate)
        
        # starting camera time + 1 to ensure starting frame included
        self.debug_print("getting starting time")
        self.start_time = timeParse.getDateTime(self._getFrame(0)) + timedelta(seconds=1) 
        self.start_index = self._getAccurateIndex(0, self.start_time) # not objective starting frame
        
        # no issue with starting frame but need to make sure last second timechunkable
        self.debug_print("getting ending time")
        # primitive end time with last frame
        end_time_basic = timeParse.getDateTime(self._getFrame(self.frame_count - 1))
        # better end time with first frame of the last full "chunk" from starting time  
        self.end_time = (end_time_basic - timedelta(seconds=(end_time_basic - self.start_time).total_seconds() % self.time_chunk.total_seconds()))
        # frame of better end time
        self.end_index = self._getFrameIndexOfTime(self.end_time, ref_index=self.frame_count - 1)
        
        # total time between the better start time and better end time (should be divisible by chunk size)
        self.total_time = self.end_time - self.start_time
        # number of chunks
        self.num_chunks = int(self.total_time.total_seconds() // self.time_chunk.total_seconds() + 1)
        
        # frame specific data
        self.frame_index = self.start_index # reset current frame index
        self.frame = self._getFrame(self.frame_index) # reset current frame
        
    def _resize_image(self, event):
        '''Resizes video frame.
        
        Args:
            event: needed to tie event to trigger resize
        '''
        self.debug_print("resize triggered")
        self.debug_print("new frame dim: " + str((event.width, event.height - 8)))
        self._update_display(width=event.width, height=event.height)
        
#     @timeit
    def _update_display(self, width=None, height=None):
        '''Updates display.
        
        Args:
            width: width to display (default to winfo width)
            height: height to display (default to winfo height)
        '''
        # ngl no clue why update crashes when resize calls it at least on Mac
        if height == None and width == None:
            # updates the frame
            self.vid_frame.update()
            resize = False
        else:
            resize = True
                             
        # if resize, use specified, otherwise current window dims
        width = width if width != None else self.vid_frame.winfo_width()
        height = height if height != None else self.vid_frame.winfo_height()
        
        # magical offset im too lazy to find why there is overlap
        self.vid_frame_dims = width, height  - 8
        
        # check if video loaded
        if self.vid_loaded:
            # update frames
            self.frame = self._getFrame(self.frame_index + self.rel_offset) # target frame + offset
            
            # update image
            self.img = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
            
            # update time
            self.time = timeParse.getDateTime(self.frame) # update time
            curr_chunk = int((self.time - self.start_time).total_seconds() // self.time_chunk.total_seconds() + 1)
            self.time_label.config(text = f"Camera Time: {self.getTimeStr()}   Frame: {str(curr_chunk)}/{str(self.num_chunks)}")
            
            if not resize:
                # update the time string of frame
                if self.timeIndexFunc != None:
                    self.timeIndexFunc(self.getTimeStr())
                else:
                    self.debug_print("cannot set time without input result path func")
            
            # update image
            # creates new image copy for transformation
            self.resized_image = ImageOps.contain(self.img.copy(), (self.vid_frame_dims[0], self.vid_frame_dims[1]))
            # resize new image copy
            self.resized_image.resize((self.vid_frame_dims[0], self.vid_frame_dims[1]))
            # converts to tk-friendly object
            self.resized_tk = ImageTk.PhotoImage(self.resized_image)
            # set as current image
            self.curr_image = self.resized_tk
            # update vidcanvas
            self.vid_canvas.itemconfig(self.image, image=self.resized_tk)
            # update canvas coords
            self.vid_canvas.coords(self.image, self.vid_frame_dims[0] // 2, self.vid_frame_dims[1] // 2)
            self.debug_print("updated video")
    
    def _getCapture(self, filepath):
        return cv2.VideoCapture(filepath)

#     @timeit
    def _getFrame(self, frame_index, cap=None, show=False):
        '''Retrieves the frame from the video

        Retrieve the indexed frame from the video and return it as an image of an numpy array.

        Args:
            frame_num: index of the frame to show.
            cap: capture to find the frame of, defaults to cap defined above
            show: determines whether to show or to skip, defaults to noshow

        Returns:
            numpy image array of the frame

        Raises:
            Exception: frame_num({frame_num}) cannot equal or exceed number of frames({frame_count})
        '''
        cap = self.cap if cap == None else cap

        if (frame_index >= self.frame_count): 
            raise Exception(f"frame_index({frame_index}) cannot equal or exceed number of frames({self.frame_count})") 

        self.cap.set(1, frame_index)  # where frame_no is the frame you want
        ret, frame = cap.read()  # read the frame

        self._showFrame(frame, show, title="frame")

        return frame

#     @timeit
    def _getFPS(self, cap=None, n=3):
        '''Gets the current FPS.
        
        Args:
            cap: the capture object to get FPS of (default None [self cap object])
            n: the number of immediate seconds to divide and calculate FPS
        '''
        # set cap as parent cap if not specified
        cap = self.cap if cap == None else cap
        
        # get the starting time
        init_time = timeParse.getTime(self._getFrame(0))
        
        # get the first frame of the (time) second after the initial (time) second
            # Warning: potential for infinite loop if bad initial time image
        j = 0
        while j < self.frame_count and timeParse.getTime(self._getFrame(j)) == init_time: j += 1
        
        # counter of seconds
        secCounter = 0
        # start at first frame of the first post-initial time second (first full second)
        i = j
        
        # current sec (initiate as first full sec)
        new_time = timeParse.getTime(self._getFrame(j))
        # find the frame of nth second after the first full second
        while secCounter < n:
            # next full second
            while i < self.frame_count and timeParse.getTime(self._getFrame(i)) == new_time: i += 1 # start of the second second
            
            # iterate the "current" second
            new_time = timeParse.getTime(self._getFrame(i))
            # increment counter
            secCounter += 1

        return (i - j) / n
    
    def getTimeStr(self):
        '''Returns string form of time.'''
        # make sure video loaded
        if (self.vid_loaded == False):
            return None
        
        return str(self.time.replace(microsecond=0))

#     @timeit
    def _getAccurateIndex(self, index, time, fps=None, cap=None):
        '''Get first frame index of the selected time given existing close index.
        Primitively increment frames till reach time
        
        Args:
            index: current index close to specified time
            time: target time
            fps: fps (default to None)
            cap: capture object (default to None)
        '''
        # if fps and cap not specified use existing
        fps = self.fps if fps == None else fps
        cap = self.cap if cap == None else cap
        
        # track number of retrievals for debug
        i = 0
        
        # if same time or greater decrement frame till one second under target time
        while (timeParse.getDateTime(self._getFrame(index)) >= time):
            i += 1
            index -= 1

        # go up to first frame of target time
        while (timeParse.getDateTime(self._getFrame(index)) < time):
            i += 1
            index += 1
            
        # debug
        self.debug_print(f"number of error datetime retrievals: {i}")
            
        return index

#     @timeit
    def _getFrameIndexOfTime(self, time, ref_index=None, fps=None, cap=None):
        '''Get first frame index of time.
        Optimized for both given reference frame or arbitrary jump.
        
        Args:
            time: target time
            ref_index: reference index of a time that is roughly closer to target
            fps: fps (default to none)
            cap: cap (default to none)
        '''
        # if fps and cap not specified use existing
        fps = self.fps if fps == None else fps
        cap = self.cap if cap == None else cap
        
        # check if time out of bounds
        if (time < self.start_time or time > self.end_time):
            self.debug_print("invalid time no jump")
            messagebox.showinfo("Time Out of Bounds", "specified time is outside of the duration of the video")
            return -1
        
        '''
        Optimizations Explanations and ideas
        
        base: 
            method:
                use start time as reference frame and jump with fps to projected frame then find correct frame
            pros:
                easy to code
            cons:
                error increases the farther target time is from start time, larger error means longer final frame find
             
        repeat jump optimization:
            method:
                continue to jump utnil near final frame find
                with each jump less error distance so less inefficient
            pros:
                efficient
                easy to code
                preserve efficient bestcase
            cons:
                if error is large and frame rate very inconsistent larger errors
                
        input-reference optimization:
            method:
                given reference frame jump based on reference frame instead of start frame
            pros:
                much more efficient when reference frame not far from target frame
                great for short jumps
            cons:
                requires input reference
                efficiency dependent on reference time proximity to target time
                
        multiple-reference optimization:
            method:
                use start, end, (optional parameter reference frame), and frames selected from dividing the video evenly 
                    as reference frames
                find the reference frame with least time diff to target time
                jump from the selected reference frame to reduce error
                find correct frame
            pros:
                efficient
                very efficient if given reference time not far from target time as minimize error
                works with fluxuating fps
                very scalable 
            cons:
                not as easy to code
                not as efficient as binary search
                worse bestcase as increased minimum frames needed to process
                harder to pinpoint
        
        binary search optimization:
            method:
                apply binary search
            pros:
                efficient
                scalablea
                easy too code
                objectively better than mult-reference apart from input ref
            cons:
                worst best case as increasedd minimum frames needed to process
            performance:
                worst/avg: O(logn)
                
        current implementation:
            if "close" ref provided: input-reference with repeat jump
            if no ref provided: binary search
        
        TODO:
            calculate out optimal divisions withtime complexity based on total frames
            identify error
        '''
        
        # result index, a "close" index to the target time (not first frame index)
        result_index = -1
        # tracks number of datetime retrieval for debugging
        i = 0
        
        
        # repeat jump method if given reference index
        if (ref_index != None):
            self.debug_print("repeat jump")
            
            # get the time at reference index
            ref_time = timeParse.getDateTime(self._getFrame(ref_index))
            time_delt = time - ref_time # positive if target time greater than reference
            
            # repeat jumps until time diff between 1 sec
                # not > 0 in case fps slightly larger than actual frame and perpetual jump over
            while (abs(time_delt.total_seconds()) >= 2): 
                i += 1
                self.debug_print(f"jump  {str(time_delt.total_seconds() * fps)} frames ")
                ref_index += time_delt.total_seconds() * fps # jump frame
                ref_time = timeParse.getDateTime(self._getFrame(ref_index)) # get time of jumped frame
                time_delt = time - ref_time # find difference
            
            # set result index
            result_index = ref_index
            
        # binary search if no reference frame/time given
        else:
            self.debug_print("binary search")
            min_index = 0 # min frame
            max_index = self.frame_count # max frame
            ref_index = (max_index + min_index) // 2 # middle frame
            
            # time delta
            time_delt = time - timeParse.getDateTime(self._getFrame(ref_index))
            
            # binary search till within 2 sec gap
            while (abs(time_delt.total_seconds()) >= 2):
                i += 1
                # positive diff when target time greater than reference
                if time_delt.total_seconds() > 0:
                    min_index = ref_index
                    ref_index = (max_index + min_index) // 2
                    time_delt = time - timeParse.getDateTime(self._getFrame(ref_index))
                
                # negative diff when target time less than reference
                if time_delt.total_seconds() < 0:
                    max_index = ref_index
                    ref_index = (max_index + min_index) // 2
                    time_delt = time - timeParse.getDateTime(self._getFrame(ref_index))
            
            # set result index
            result_index = ref_index
        
        # debug info
        self.debug_print(f"number of jump datetime retrievals: {i}")
        
        return self._getAccurateIndex(result_index, time) # get the actual frame from close-enough result
    
    # jumps to frame index
    def _jumpToFrame(self, frame_index):
        '''Jump to arbitrary index.
        
        Args:
            frame_index: index to jump to
        '''
        # check if out of bounds
        if frame_index < self.start_index or frame_index > self.end_index:
            self.debug_print("invalid frame no jump")
            messagebox.showinfo("Time Out of Bounds", "specified time is outside of the duration of the video")
            return
            
        # known issue when jumping to non-timechunked frame
        
        # set new index
        self.frame_index = frame_index
        # always revert back to basic relative frame
        self._displayRelativeFrame(0)
        # update display
        self._update_display()
        
    def _jumpToTime(self, time):
        '''Jump to specific time.
        
        Args:
            time: time to jump to
        '''
        # check if out of bounds
        if time < self.start_time or time > self.end_time:
            self.debug_print("invalid time no jump")
            messagebox.showinfo("Time Out of Bounds", "specified time is outside of the duration of the video")
            return
        
        # set frame to first frame of specified time
        self._jumpToFrame(self._getFrameIndexOfTime(time))
    
    def _jumpForwardFrames(self, frames_forward):
        '''Jump forwards specified frames.
        
        Args:
            frames_forwards: frames to jump ahead by
        '''
        
        # set frame to specified frames forward but capped at end_index
        self._jumpToFrame(min(self.frame_index + frames_forward, self.end_index))
    
    def _jumpBackFrames(self, frames_back):
        '''Jump back specified frames.
        
        Args:
            frames_forwards: frames to jump back by
        '''
        # set frame to specified frames forward but floored at end_index
        self._jumpToFrame(max(self.frame_index - frames_back, self.start_index))
    
#     @timeit
    def _jumpForwardTime(self, delt):
        '''Jump forward specified time.
        
        Args:
            delt: time ahead to jump by (negative time jump back)
        '''
        # only jump if video loaded [ngl not needed]
        if not self.vid_loaded: return None
        # set new index as first frame of certain time forward (or back)
        new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) + delt, ref_index=self.frame_index)
        # check if frame is found, no change otherwise
        self._jumpToFrame(new_index if new_index != -1 else self.frame_index)

        #     @timeit
    def _jumpShortNextChunk(self):
        '''Jump forward one pre-defined "chunk" of time.'''
        
        # check if last chunk, cant go beyond last chunk
        if (self.time == self.end_time):
            messagebox.showinfo("Video Complete", "video is fully processed!")
            return
        
        # jump forward by pre-defined chunk of time
        self._jumpForwardTime(self.time_chunk)
        # update display
        self._update_display()
    
#     @timeit
    def _jumpShortBackChunk(self):
        '''Jump back one pre-defined "chunk" of time.'''
        # deprecate if no diff
#         new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) - self.time_chunk, ref_index=self.frame_index)
#         self.frame_index = new_index if new_index != -1 else self.frame_index

        # jump back by pre-defined chunk of time
        self._jumpForwardTime(-1 * self.time_chunk)
        # update display
        self._update_display()
    

#     @timeit
    def _jumpNextChunk(self):
        '''Jump forward one pre-defined "chunk" of time.'''
        
        # check if last 5 chunk, cant go beyond last chunk
        if (self.time == self.end_time or self.time - self.time_chunk == self.end_time):
            messagebox.showinfo("Video Complete", "video is fully processed!")
            return
        
        # jump forward by 5 pre-defined chunks of time
        self._jumpForwardTime(self.time_chunk * 5)
        # update display
        self._update_display()
    
#     @timeit
    def _jumpBackChunk(self):
        '''Jump back one pre-defined "chunk" of time.'''
        # deprecate if no diff
#         new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) - self.time_chunk, ref_index=self.frame_index)
#         self.frame_index = new_index if new_index != -1 else self.frame_index

        # jump back by 5 pre-defined chunks of time
        self._jumpForwardTime(-1 * self.time_chunk * 5)
        # update display
        self._update_display()
    
    def _jumpLongNextChunk(self):
        '''Jump forward two pre-defined "chunk" of time.'''
        
        # check if last 10 chunk, cant go beyond last chunk
        if (self.time == self.end_time or self.time - self.time_chunk == self.end_time):
            messagebox.showinfo("Video Complete", "video is fully processed!")
            return
        
        # jump forward by 10 pre-defined chunks of time
        self._jumpForwardTime(10 * self.time_chunk)
        # update display
        self._update_display()
        
    def _jumpLongBackChunk(self):
        '''Jump back two pre-defined "chunk" of time.'''
#         new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) - 2 * self.time_chunk, ref_index=self.frame_index)
#         self.frame_index = new_index if new_index != -1 else self.frame_index

        # jump back by 10 pre-defined chunks of time
        self._jumpForwardTime(-1 * self.time_chunk * 10)
        # update display
        self._update_display()
        
    def _jumpStart(self):
        '''Jump to starting index. [note not the first overall frame but first frame of first full second]'''
        # set index
        self._jumpToFrame(self.start_index)
        
    def _jumpEnd(self):
        '''Jump to ending index. [note not the last overall frame but last frame of last time chunk second]'''
#         self.frame_index = (self.frame_count - 1) - self.frame_count % self.fps
        self._jumpToFrame(self.end_index)
        
    def _jumpChunk(self):
        '''Jump to certain chunk specified by tkinter entry.'''
        # check entrybox value
        if self.jump_chunk_entry.get() == "": return None
        # convert value to integer
        chunk_to = int(self.jump_chunk_entry.get())
        
        # check if desired frame out of bounds
        if chunk_to <= 0 or chunk_to > self.num_chunks:
            self.debug_print("invalid chunk no jump")
            messagebox.showinfo("Frame Out of Bounds", "specified frame is outside of the range of frames")
            return
        
        # debug
        self.debug_print("attempting chunk jump")
        # jump to chunk
        self._jumpToTime(self.start_time + ((chunk_to - 1) * self.time_chunk))
        
    def _setKeyBinds(self):
        '''Set keybinds for keyboard shortcuts.'''
        # start button
        self.master.bind("a", lambda x: self._jumpStart())
        
        # back button
        self.master.bind("s", lambda x: self._jumpBackChunk())
        self.master.bind("<Left>", lambda x: self._jumpBackChunk())
        
        # next button
        self.master.bind("d", lambda x: self._jumpNextChunk())
        self.master.bind("<Right>", lambda x: self._jumpNextChunk())
        
        # end button
        self.master.bind("f", lambda x: self._jumpEnd())
        self.debug_print("set keybinds")
            
        
    # Input Panel Funcs
    def setLoadLanesFunc(self, func):
        '''Sets function to pass number of lanes to input panels.
        Linked up on root Traffic Tool object.
        
        Args:
            func: function from input panels to set number of lanes
        '''
        # debug
        self.debug_print("setting load lanes func from input panel")
        # binds to InputPanel.loadLanes()
        self.loadLanesFunc = func
        # check if function exists and view/number of lane selected
        if self.loadLanesFunc != None and self.view_selected:
            # runs InputPanel function to load lanes
            self.loadLanesFunc(display_lanes=vld.view_to_lanes[self.view_name])
        else:
            self.debug_print("cannot set input panel length without input panel setup func")
            
    def setTimeIndexFunc(self, func):
        '''Sets function to pass current time to input panel.
        Linked up on root Traffic Tool object.
        
        Args:
            func: function from input panels to pass current time
        '''
        # debug info
        self.debug_print("setting time index func from input panel")
        # binds to InputPanel.updateTimeIndex()
        self.timeIndexFunc = func 
        
        # check if view selected [required for file output from input panel]
        if self.view_selected:
            self.timeIndexFunc(self.getTimeStr())
    
    def setResultPathFunc(self, func):
        '''Sets function to pass result path to input panel.
        Linked up on root Traffic Tool object.
        
        Args:
            func: function from input panels to pass result path
        '''
        # debug info
        self.debug_print("setting result path func from input panel")
        # binds to InputPanel.updateResultPath()
        self.resultPathFunc = func
        
        # check view selected to generate result path
            # technically redundant bc another check in getResultPAth() but safer to have 2 checks
        if self.view_selected:
            self.resultPathFunc(self.getResultFilePath())
        
    @staticmethod
    def _showFrame(frame, show, title="Unnamed Frame"):
        '''Show the frame in question if show is true for debugging.

        If show is false, does nothing.
        If show is true, shows frame as an external window until a keypress is recorded.

        Args:
            frame: frame to show.
            title: title of the frame to show. Defaults to "Unnamed Frame"
            show: determines whether to show or to skip

        Returns:
            Nothing

        Raises:
        '''

        if (show):
            cv2.imshow(title, frame)  # show frame on window
            cv2.waitKey(0)

            # closing all open windowsgr
            cv2.destroyAllWindows()
    
    def debug_print(self, string):
        '''Print only if debug mode is on.
        
        Args:
            string: string to print
        '''
        if self.debug: print(string)

if __name__ == "__main__":
    root = Tk()
    video_panel = VideoPanel(file_path="..//vids//TLC00024.mp4", parent=root, view_name="Q2", master=root, debug=True)
#     video_panel = VideoPanel(file_path="vids\\TLC00005.mp4", overlay_path="overlays\\Q11.png", parent=root, master=root, debug=True)
#     video_panel = VideoPanel(parent=root, master=root, debug=True)
    root.mainloop()