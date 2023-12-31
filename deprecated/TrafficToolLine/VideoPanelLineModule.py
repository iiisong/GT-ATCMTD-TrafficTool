import tkinter as tk
from tkinter import Tk, ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps

import cv2
import os

from datetime import date, datetime, time, timedelta

# helper python code
import timeParse # extract time data from frames
import ViewLanesDict as vld

# timers for efficiency testing
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

class VideoPanel():
    def __init__(self, init_index=0, 
                 time_chunk=5, 
                 output_dir=None,
                 file_path=None, 
                 overlay_path=None,
                 vids_file_path=".\\vids\\", 
                 overlays_file_path=".\\overlays\\", 
                 parent=None,
                 master=None,
                 debug=False):
        
        super().__init__()
        
        # process input params
        self.init_index = init_index
        self.time_chunk = timedelta(seconds=time_chunk)
        self.file_path = file_path # potentially none, deal with it later in _load()
        self.overlay_path = overlay_path # potentially None deal with it later in _load_overlay()
        self.vids_file_path = vids_file_path # currently unused
        self.overlays_file_path = overlays_file_path # currently unused
        self.parent = parent
        self.master = master
        self.debug = debug
        
        self.loadLanesFunc = None
        self.timeIndexFunc = None
        self.resultPathFunc = None
        
        # deal with result directory
        self.output_dir = "results" if output_dir == None else output_dir
        
        # create path if not exist
        if os.path.exists(self.output_dir) == False:
            os.makedirs(self.output_dir)
        
        # vid and overlay states
        self.vid_loaded = False
        self.overlay_loaded = False
        
        # toggles
        self.overlay_toggle = False
        self.overlay_down = False
        
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
        self.parent.rowconfigure(1, weight=10)
        
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
        frame.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)

        self.start_button = tk.Button(master=frame, 
                                 text=f"Start",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpStart)
        self.start_button.pack(fill=fill, expand=expand)
        
        # double back time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=1, sticky="nsew", pady=5, padx=5)

        self.double_back_button = tk.Button(master=frame, 
                                 text=f"-{2 * self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpDoubleBackChunk)
        self.double_back_button.pack(fill=fill, expand=expand)
        
        # back time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=2, sticky="nsew", pady=5, padx=5)

        self.back_button = tk.Button(master=frame, 
                                 text=f"-{self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpBackChunk)
        self.back_button.pack(fill=fill, expand=expand)
        
        # next time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=3, sticky="nsew", pady=5, padx=5)

        self.next_button = tk.Button(master=frame, 
                                 text=f"+{self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpNextChunk)
        self.next_button.pack(fill=fill, expand=expand)
        
        # double next time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=4, sticky="nsew", pady=5, padx=5)

        self.double_next_button = tk.Button(master=frame, 
                                 text=f"+{2 * self.time_chunk.total_seconds()}s",
                                 font='sans 10',
                                 bg="white",
                                 command=self._jumpDoubleNextChunk)
        self.double_next_button.pack(fill=fill, expand=expand)
        
        # end time button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=0, column=5, sticky="nsew", pady=5, padx=5)

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
        frame.grid(row=1, column=0, sticky="nsew", pady=5, padx=5)
        
        frame.rowconfigure(0, weight=1)

        self.jump_chunk_button = tk.Button(master=frame, 
                                 text=f"Jump Frame",
                                 font='sans 7',
                                 bg="white",
                                 command=self._jumpChunk)
        self.jump_chunk_button.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=5)#, uniform="row")
        
        def callback(P):
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
            
        # load video button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=2, sticky="nsew", pady=5, padx=5)

        self.load_button = tk.Button(master=frame, 
                                 text=f"Load Video",
                                 font='sans 10',
                                 bg="white",
                                 command=self._load)
        self.load_button.pack(fill=fill, expand=expand)
        
        # load overlay button
        frame = ttk.Frame(
            master=self.controls_frame,
            relief="raised",
            borderwidth=1,
        )
        frame.grid(row=1, column=3, sticky="nsew", pady=5, padx=5)
        
        self.load_overlay_button = tk.Button(master=frame, 
                                 text=f"Load Overlay",
                                 font='sans 10',
                                 bg="white",
                                 command=self._load_overlay)
        self.load_overlay_button.pack(fill=fill, expand=expand)
        
        # autoload if initialized
        if self.file_path != None:
            self.debug_print("loading preset video")
            self._load(file_path_known=True)
        if self.overlay_path != None:
            self.debug_print("loading preset overlay")
            self._load_overlay(overlay_path_known=True)
            
        self._update_display()
            
        self._setKeyBinds()
    
    def _load(self, file_path_known=False):
        """ loads the video """
        if file_path_known == False:
            self.file_path = filedialog.askopenfilename()
            
        file_name_raw = os.path.basename(self.file_path).split(".")
        
        if (len(file_name_raw) == 1): return
    
        if (file_name_raw[1] != "mp4"):
            self.debug_print("file must be a mp4")
            messagebox.showinfo("Wrong File Format", "video file must be a .mp4")
            return # early return 
        self.file_name = file_name_raw[0]
        
        self.debug_print("file loaded: " + str(self.file_path))
        
        self._video_properties()
        
        self.vid_frame.update() # unsure if needed
        
        # video setup
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
        else:
            self._update_display()
        
        self.time = timeParse.getDateTime(self.frame) # update time
        curr_chunk = int((self.time - self.start_time).total_seconds() // self.time_chunk.total_seconds() + 1)
        self.time_label.config(text = f"Camera Time: {self.getTimeStr()}   Frame: {str(curr_chunk)}/{str(self.num_chunks)}")
                
        self.vid_loaded = True
        
        if self.overlay_loaded:
            if self.resultPathFunc != None:
                self.resultPathFunc(self.getResultFilePath())
            else:
                self.debug_print("update result path func with new vid")
#         self._update_display()
        
    def _load_overlay(self, overlay_path_known=False):
        if not self.vid_loaded:
            self.debug_print("video must be loaded first")
            messagebox.showinfo("No Video Detected", "overlay requires video to be loaded first")
            return # early return 
        
        if overlay_path_known == False:
            self.overlay_path = filedialog.askopenfilename()
        
        overlay_file_name_raw = os.path.basename(self.overlay_path).split(".")
        
        if len(overlay_file_name_raw) == 1 or overlay_file_name_raw[1] != "png":
            self.debug_print("file must be a png")
            messagebox.showinfo("Wrong File Format", "overlay file must be a .png")
            return # early return 
        self.overlay_file_name = overlay_file_name_raw[0]
        
        self.debug_print("overlay loaded: " + str(self.overlay_path))
        self.debug_print("overlay lanes: " + str(vld.view_to_lanes[self.overlay_file_name]))
        
        # load overlay if specified
        if not self.overlay_loaded:
            self.debug_print("overlay created: " + str(self.overlay_path))
            self.overlay_img = Image.open(self.overlay_path).convert("RGBA")
            self.overlay_tk = ImageTk.PhotoImage(self.overlay_img, master=self.vid_frame)
            self.curr_overlay = self.overlay_tk
            self.overlay = self.vid_canvas.create_image(self.vid_frame.winfo_width() // 2, 
                                                        self.vid_frame.winfo_height() // 2, 
                                                        image=self.overlay_tk,
                                                        state=tk.HIDDEN)
        else:
            self.debug_print("new overlay created: " + str(self.overlay_path))
            self.overlay_img = Image.open(self.overlay_path).convert("RGBA")
            self._update_display()
        
        if self.loadLanesFunc != None:
            self.loadLanesFunc(display_lanes=vld.view_to_lanes[self.overlay_file_name])
        else:
            self.debug_print("cannot load lanes without load lanes func")
            
        self.overlay_loaded = True
        self._update_display()
        
        if self.resultPathFunc != None:
            self.resultPathFunc(self.getResultFilePath())
        else:
            self.debug_print("cannot set result path without input result path func")
        
        self.debug_print("result file path: " + str(self.getResultFilePath()))
            
    def getResultFilePath(self):
        if (self.vid_loaded == False or self.overlay_loaded == False):
            return None
        
        return os.path.join(self.output_dir, self.overlay_file_name + "_" + self.file_name + "_line") + ".xlsx"
    
    def _video_properties(self):
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
        end_time_basic = timeParse.getDateTime(self._getFrame(self.frame_count - 1))
        self.end_time = (end_time_basic - timedelta(seconds=(end_time_basic - self.start_time).total_seconds() % self.time_chunk.total_seconds()))
#         self.end_index =  self._getAccurateIndex(self.frame_count - 1, self.end_time) # not objective ending frame
        self.end_index = self._getFrameIndexOfTime(self.end_time, ref_index=self.frame_count - 1)
        
        self.total_time = self.end_time - self.start_time
        self.num_chunks = int(self.total_time.total_seconds() // self.time_chunk.total_seconds() + 1)
        
        # frame specific data
        self.frame_index = self.start_index # reset current frame index
        self.frame = self._getFrame(self.frame_index) # reset current frame
        
    def _resize_image(self, event):
        self.debug_print("resize triggered")
        self.vid_frame.update()
        self.vid_frame_dims = event.width, event.height - 8 # magical offset im too lazy to find why there is overlap
        self.debug_print("new frame dim: " + str(self.vid_frame_dims))

        # resize image
        if self.vid_loaded:
#             ratio = (self.dims[0] / self.dims[1])
            self.resized_image = ImageOps.contain(self.img.copy(), (self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_image.resize((self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_tk = ImageTk.PhotoImage(self.resized_image)
            self.curr_image = self.resized_tk
            self.vid_canvas.itemconfig(self.image, image=self.resized_tk)
            self.vid_canvas.coords(self.image, self.vid_frame_dims[0] // 2, self.vid_frame_dims[1] // 2)
        
        # load overlay if specified
        if self.overlay_loaded:
            self.resized_overlay = ImageOps.contain(self.overlay_img.copy(), (self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_overlay.resize((self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_overlay_tk = ImageTk.PhotoImage(self.resized_overlay.convert(mode="RGBA"))
            self.curr_overlay = self.resized_overlay_tk
            self.vid_canvas.itemconfig(self.overlay, image=self.resized_overlay_tk)
            self.vid_canvas.coords(self.overlay, self.vid_frame_dims[0] // 2, self.vid_frame_dims[1] // 2)
        
#     @timeit
    def _update_display(self):
        self.vid_frame.update()
        # magical offset im too lazy to find why there is overlap
        self.vid_frame_dims = self.vid_frame.winfo_width(), self.vid_frame.winfo_height() - 8
        
        if self.vid_loaded:
            # update frames
            self.frame = self._getFrame(self.frame_index)
            
            # update image
            self.img = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
            
            # update time
            self.time = timeParse.getDateTime(self.frame) # update time
            curr_chunk = int((self.time - self.start_time).total_seconds() // self.time_chunk.total_seconds() + 1)
            self.time_label.config(text = f"Camera Time: {self.getTimeStr()}   Frame: {str(curr_chunk)}/{str(self.num_chunks)}")
            
            if self.timeIndexFunc != None:
                self.timeIndexFunc(self.getTimeStr())
            else:
                self.debug_print("cannot set time without input result path func")
            
            # update image
            self.resized_image = ImageOps.contain(self.img.copy(), (self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_image.resize((self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_tk = ImageTk.PhotoImage(self.resized_image)
            self.curr_image = self.resized_tk
            self.vid_canvas.itemconfig(self.image, image=self.resized_tk)
            self.vid_canvas.coords(self.image, self.vid_frame_dims[0] // 2, self.vid_frame_dims[1] // 2)
            self.debug_print("updated video")

        # load overlay if specified
        if self.overlay_loaded:
            self.resized_overlay = ImageOps.contain(self.overlay_img.copy(), (self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_overlay.resize((self.vid_frame_dims[0], self.vid_frame_dims[1]))
            self.resized_overlay_tk = ImageTk.PhotoImage(self.resized_overlay.convert(mode="RGBA"))
            self.curr_overlay = self.resized_overlay_tk
            self.vid_canvas.coords(self.overlay, self.vid_frame_dims[0] // 2, self.vid_frame_dims[1] // 2)
            self.vid_canvas.itemconfig(self.overlay, image=self.resized_overlay_tk)
            
            if self.overlay_toggle:
                self.vid_canvas.itemconfig(self.overlay, state=tk.HIDDEN)
            else:
                self.vid_canvas.itemconfig(self.overlay, state=tk.NORMAL)
            
            self.debug_print("updated overlay")

    
    def _getCapture(self, filepath):
        return cv2.VideoCapture(filepath)

#     @timeit
    def _getFrame(self, frame_index, cap=None, show=False):
        """Retrieves the frame from the video

        Retrieve the indexed frame from the video and return it as an image of an numpy array.

        Args:
            frame_num: index of the frame to show.
            cap: capture to find the frame of, defaults to cap defined above
            show: determines whether to show or to skip, defaults to noshow

        Returns:
            numpy image array of the frame

        Raises:
            Exception: frame_num({frame_num}) cannot equal or exceed number of frames({frame_count})
        """
        cap = self.cap if cap == None else cap

        if (frame_index >= self.frame_count): 
            raise Exception(f"frame_index({frame_index}) cannot equal or exceed number of frames({self.frame_count})") 

        self.cap.set(1, frame_index)  # where frame_no is the frame you want
        ret, frame = cap.read()  # read the frame

        self._showFrame(frame, show, title="frame")

        return frame

#     @timeit
    def _getFPS(self, cap=None, n=3):
        cap = self.cap if cap == None else cap
        
        init_time = timeParse.getTime(self._getFrame(0))
        
        j = 0
        while j < self.frame_count and timeParse.getTime(self._getFrame(j)) == init_time: j += 1

        secCounter = 0
        i = j
        
         # start of the first sec
        new_time = timeParse.getTime(self._getFrame(j))
        while secCounter < n:
            while i < self.frame_count and timeParse.getTime(self._getFrame(i)) == new_time: i += 1 # start of the second second
            
            new_time = timeParse.getTime(self._getFrame(i))
            secCounter += 1

        return (i - j) / n
    
    def getTimeStr(self):
        if (self.vid_loaded == False):
            return None
        
        return str(self.time.replace(microsecond=0))

#     @timeit
    def _getAccurateIndex(self, index, time, fps=None, cap=None):
        fps = self.fps if fps == None else fps
        cap = self.cap if cap == None else cap
        i = 0
        
        while (timeParse.getDateTime(self._getFrame(index)) >= time):
            i += 1
            index -= 1

        while (timeParse.getDateTime(self._getFrame(index)) < time):
            i += 1
            index += 1
            
        self.debug_print(f"number of error datetime retrievals: {i}")
            
        return index

#     @timeit
    def _getFrameIndexOfTime(self, time, ref_index=None, fps=None, cap=None):
        fps = self.fps if fps == None else fps
        cap = self.cap if cap == None else cap
        
        if (time < self.start_time or time > self.end_time):
            self.debug_print("invalid time no jump")
            messagebox.showinfo("Time Out of Bounds", "specified time is outside of the duration of the video")
            return -1
        
        '''
        Optimizations explanation
        
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
        result_index = -1
        i = 0
        # input-ref with repeat jump
        
        if (ref_index != None):
            self.debug_print("repeat jump")
            ref_time = timeParse.getDateTime(self._getFrame(ref_index))
            time_delt = time - ref_time # positive if target time greater than reference
            
            # repeat jumps until time diff between 1 sec
                # not > 0 in case fps slightly larger than actual frame and perpetual jump over
            while (abs(time_delt.total_seconds()) >= 1): 
                i += 1
                self.debug_print(f"jump  {str(time_delt.total_seconds() * fps)} frames ")
                ref_index += time_delt.total_seconds() * fps # jump frame
                ref_time = timeParse.getDateTime(self._getFrame(ref_index)) # get time of jumped frame
                time_delt = time - ref_time # find difference
            
            result_index = ref_index
            
        # binary search
        else:
            self.debug_print("binary search")
            min_index = 0 # min frame
            max_index = self.frame_count # max frame
            ref_index = (max_index + min_index) // 2 # middle frame
            
            time_delt = time - timeParse.getDateTime(self._getFrame(ref_index))
            while (abs(time_delt.total_seconds()) >= 1):
                i += 1
                # positive diff when target time greater than reference
                if time_delt.total_seconds() > 0:
                    min_index = ref_index
                    ref_index = (max_index + min_index) // 2
                    time_delt = time - timeParse.getDateTime(self._getFrame(ref_index))
                
                if time_delt.total_seconds() < 0:
                    max_index = ref_index
                    ref_index = (max_index + min_index) // 2
                    time_delt = time - timeParse.getDateTime(self._getFrame(ref_index))
                    
            result_index = ref_index
        
        self.debug_print(f"number of jump datetime retrievals: {i}")
        return self._getAccurateIndex(result_index, time)
    
    # jumps to nearest valid time
    def _jumpToFrame(self, frame_index):
        if frame_index < self.start_index or frame_index > self.end_index:
            self.debug_print("invalid frame no jump")
            messagebox.showinfo("Time Out of Bounds", "specified time is outside of the duration of the video")
            return
            
        # known issue when jumping to non timechunked frame
        
        self.frame_index = frame_index
        self._update_display()
        
    def _jumpToTime(self, time):
        if time < self.start_time or time > self.end_time:
            self.debug_print("invalid time no jump")
            messagebox.showinfo("Time Out of Bounds", "specified time is outside of the duration of the video")
            return
        
        self.frame_index = self._getFrameIndexOfTime(time)
        self._update_display()
    
    def _jumpForwardFrames(self, frames_forward):
        self.frame_index = min(self.frame_index + frames_forward, self.end_index)
        _update_display()
    
    def _jumpBackFrames(self, frames_back):
        self.frame_index = max(self.frame_index - frames_back, self.start_index)
        self._update_display()
    
#     @timeit
    def _jumpForwardTime(self, delt):
        if not self.vid_loaded: return None
        new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) + delt, ref_index=self.frame_index)
        self.frame_index = new_index if new_index != -1 else self.frame_index
        self._update_display()
        
#     @timeit
    def _jumpNextChunk(self):
        if (self.time == self.end_time):
            messagebox.showinfo("Video Complete", "video is fully processed!")
            return
        
        self._jumpForwardTime(self.time_chunk)
        self._update_display()
    
#     @timeit
    def _jumpBackChunk(self):
        new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) - self.time_chunk, ref_index=self.frame_index)
        self.frame_index = new_index if new_index != -1 else self.frame_index
        self._update_display()
        
    def _jumpDoubleNextChunk(self):
        if (self.time == self.end_time or self.time - self.time_chunk == self.end_time):
            messagebox.showinfo("Video Complete", "video is fully processed!")
            return
        
        self._jumpForwardTime(self.time_chunk * 2)
        self._update_display()
        
    def _jumpDoubleBackChunk(self):
        new_index = self._getFrameIndexOfTime(timeParse.getDateTime(self.frame) - 2 * self.time_chunk, ref_index=self.frame_index)
        self.frame_index = new_index if new_index != -1 else self.frame_index
        self._update_display()
        
    def _jumpStart(self):
        self.frame_index = self.start_index
        self._update_display()
        
    def _jumpEnd(self):
#         self.frame_index = (self.frame_count - 1) - self.frame_count % self.fps
        self.frame_index = self.end_index
        self._update_display()
        
    def _setKeyBinds(self):
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
        
        # toggle button 
        self.master.bind("<KeyPress>", self._toggle_press)
        self.master.bind("<KeyRelease>", self._toggle_release)
        
    def _toggle_press(self, event):
        if event.keysym == "t":
            if not self.overlay_down:
                self.debug_print("toggle pressed")
                self.overlay_down = True
                self.overlay_toggle = True
                self._update_display()
        
    def _toggle_release(self, event):
        if event.keysym == "t":
            self.debug_print("toggle released")
            self.overlay_down = False
            self.overlay_toggle = False
            self._update_display()
            
    def _jumpChunk(self):
        if self.jump_chunk_entry.get() == "": return None
        chunk_to = int(self.jump_chunk_entry.get())
        
        if chunk_to <= 0 or chunk_to > self.num_chunks:
            self.debug_print("invalid chunk no jump")
            messagebox.showinfo("Frame Out of Bounds", "specified frame is outside of the range of frames")
            return
        
        self.debug_print("attempting chunk jump")
        self._jumpToTime(self.start_time + ((chunk_to - 1) * self.time_chunk))
        
    # Input Panel Funcs
    def setLoadLanesFunc(self, func):
        self.debug_print("setting load lanes func from input panel")
        self.loadLanesFunc = func # binds to InputPanel.loadLanes()
        if self.loadLanesFunc != None and self.overlay_loaded:
            self.loadLanesFunc(display_lanes=vld.view_to_lanes[self.overlay_file_name])
        else:
            self.debug_print("cannot set input panel length without input panel setup func")
            
    def setTimeIndexFunc(self, func):
        self.debug_print("setting time index func from input panel")
        self.timeIndexFunc = func # binds to InputPanel.updateTimeIndex()
        
        if self.overlay_loaded:
            self.timeIndexFunc(self.getTimeStr())
    
    def setResultPathFunc(self, func):
        self.debug_print("setting result path func from input panel")
        self.resultPathFunc = func # binds to InputPanel.updateResultPath()
        
        if self.overlay_loaded:
            self.resultPathFunc(self.getResultFilePath())
        
    @staticmethod
    def _showFrame(frame, show, title="Unnamed Frame"):
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

            # closing all open windowsgr
            cv2.destroyAllWindows()
    
    def debug_print(self, string):
        if self.debug: print(string)

if __name__ == "__main__":
    root = Tk()
#     video_panel = VideoPanel(file_path="vids\\TLC00005.mp4", parent=root, master=root, debug=True)
    video_panel = VideoPanel(file_path="..\\vids\\TLC00005.mp4", overlay_path="..\\overlays\\Q11.png", parent=root, master=root, debug=True)
#     video_panel = VideoPanel(parent=root, master=root, debug=True)
    root.mainloop()