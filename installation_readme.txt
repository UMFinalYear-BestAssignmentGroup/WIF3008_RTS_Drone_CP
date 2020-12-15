A) Installtion
B) How to run


A) Installation
I will assume you have a 64-bit windows (you do if you have win10/computer from the last 5 years)
1) Install pyton 2.7 64-bit first https://www.python.org/ftp/python/2.7.16/python-2.7.16.amd64.msi
Reboot after installation as requested. The latest version comes with pip, so don't worry about that.

2) Download and unzip the Tello git repo dji-sdk/Tello-Python

3) Open command prompt (cmd.exe) and do the following pip installs (pip is included in latest python), just type each python commands (your computer must be connected to the internet)
python -m pip install numpy
python -m pip install matplotlib
python -m pip install -v opencv-python==3.4.2.17
python -m pip install pillow

3) Inside the git repo (zip file), there is another x64 library file: tello-python-master\tello_video_dll(ForWin64).zip file, open it and go into the tello_video_dll and copy all files except vcredist_x64 into the C:\Python27\Lib\site-packages folder.

4) Execute (double click) the vcredist_x64.exe file and install the vc distributable.

Now, fire up your tello, connect to the tello wifi when it becomes available, open up cmd (command prompt) and go into the tello-python-master\tello_video and type: python main.py

That's it! You should now see the tello camera and control window pop up!


B) Running the system:
1) without simulator
	open main.py and user port = 8889
	run main.py
	
2) with simulator (you can see the simulator receiving the instruction)
	run TelloSimulator.py in cmd using python TelloSimulator.py
	run main.py with port = 9000