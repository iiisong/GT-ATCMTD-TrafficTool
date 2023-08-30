TrafficTool v1.0.0

(Yet Unnamed) TrafficTool v.1.0.0

Interactive interface for traffic data collection.


How to run:
   Install all the python dependencies:
      tkinter
      PIL   
      pandas
      cv2
      re
      datetime
      os

   Run "TrafficTool.py" on command line

How to use:
   1. Load video and select the mp4 file
   2. Load overlay and select the matching overlay file
   3. Use video controls to jump around in datetime
   4. Use the number panel to select the "length" of the lane
         a lane's status is of length 1 if it is past line 1 but not lline 2
         empty lanes should be entered as 0
      (note) if there is more lane choices than lanes in video, go from l1 upwards instead of downwards from max lanes
   5. press enter entry to store the lane data in the results folder (can be changed with command line options)
