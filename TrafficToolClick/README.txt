TrafficToolClick v1.0.3

(Yet Unnamed) TrafficToolClick v.1.0.3

Interactive interface for traffic data collection.

How to run:
	Install all the necessary python dependencies in "requirements.txt"
		> pip install -r "requirements.txt"
	Run "TrafficToolClick.py" on command line (additional options can be shown with -h tag)
		> python TrafficToolClick.py

Instructions:
	1. Load video and select the mp4 file
	2. Enter the name of the view ("Q1", "Q2", ...) and press the set view button
	3. Use video controls to jump around in datetime
	4. Click "Set" to set the value of the lane
		When in setting mode for a lane, click the point of contact of the front wheel of the last car in the queue in the lane
	5. press enter entry button to store the lane data in an excel the results folder (can be changed with command line options)
		(note) Results are located in "[view_name]_[video_file_name]_counting.xslx"
		<<IMPORTANT>> the entered data for that frame is only stored if the enter entry is pressed, all other buttons will NOT store 
		the data regardless of the video navigation

Additional Notes:
	Loading video will take upwards of 4-6 seconds, this behavior is normal
	Jumping between frames can take upwards of 2-3 seconds, this is a ongoing task for optimization
	

Keyboard Shortcuts

<Space>	: Enter Entry Button
a		: jump to start button
s / <left>	: back 1 interval button
d / <right>	: next 1 interval button
f		: jump to end button
1-9     : set buttons 1-9
