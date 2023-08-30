TrafficToolLine v1.0.3

(Yet Unnamed) TrafficToolLine v.1.0.3

Interactive interface for traffic data collection.

How to run:
	Install all the necessary python dependencies in "requirements.txt"
		> pip install -r "requirements.txt"
	Run "TrafficToolLine.py" on command line (additional options can be shown with -h tag)
		> python TrafficToolLine.py

Instructions:
	1. Load video and select the mp4 file
	2. Load overlay and select the matching overlay png file
	3. Use video controls to jump around in datetime
	4. Use the number panel to select the "length" of each lane
		"Length" of the lane is determined by where the front wheel of the car at the back of the queue touches the ground. 
		Choose the line closest to the length determined or press enter entry if no car is present, 0 will be entered by default
		Lane is ordered by the lowest lane (L1) being the closest the camera and incrementing accordingly
			L1 is the closest lane, L2 is the second-closest, ...
	5. press enter entry button to store the lane data in an excel the results folder (can be changed with command line options)
		(note) Results are located in "[view_name]_[video_file_name]_line.xslx"
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
