from PIL import Image
from PIL import ImageTk
import Tkinter as tki
from Tkinter import *
import threading
import datetime
import cv2
import os
import time
import platform

class TelloUI:
    """Wrapper class to enable the GUI."""

    def __init__(self,tello,outputpath):
        """
        Initial all the element of the GUI,support by Tkinter

        :param tello: class interacts with the Tello drone.

        Raises:
            RuntimeError: If the Tello rejects the attempt to enter command mode.
        """        

        self.tello = tello # videostream device
        self.outputPath = outputpath # the path that save pictures created by clicking the takeSnapshot button 
        self.frame = None  # frame read from h264decoder and used for pose recognition 
        self.thread = None # thread of the Tkinter mainloop
        self.stopEvent = None  
        
        # control variables
        self.distance = 0.1  # default distance for 'move' cmd
        self.degree = 30  # default degree for 'cw' or 'ccw' cmd

        # if the flag is TRUE,the auto-takeoff thread will stop waiting for the response from tello
        self.quit_waiting_flag = False
        
        # initialize the root window and image panel
        self.root = tki.Tk()
        self.panel = None
        # ---------->Console Flight Demo<-----------------------
        consoleFrame = Frame(self.root)
        consoleFrame.pack(fill="both", expand="yes", side="bottom")

        consoleContent = LabelFrame(consoleFrame, text="Console")
        consoleContent.pack(fill="both", expand="yes", side="left")

        # self.btn_preplanned1 = tki.Button(consoleFrame, text="Start planned route 1",
        #                                command=self.takeSnapshot)
        self.btn_preplanned1 = tki.Button(consoleContent, text="Start planned route 1",
                                          command=self.plannedRoute1)
        self.btn_preplanned1.pack(side="bottom", fill="both",
                                  expand="yes", padx=10, pady=5)

        # self.btn_preplanned2 = tki.Button(consoleFrame, text="Start planned route 2", relief="raised", command=self.pauseVideo)
        self.btn_preplanned2 = tki.Button(consoleContent, text="Start planned route 2", relief="raised",
                                          command=self.plannedRoute2)
        self.btn_preplanned2.pack(side="bottom", fill="both",
                                  expand="yes", padx=10, pady=5)
        # ---------->Console Flight Demo Ends<-----------------------

        # create buttons
        controlFrame1 = Frame(self.root)
        controlFrame1.pack(fill="both", expand="yes", side="bottom")

        videoFrame = LabelFrame(controlFrame1, text="Video")
        videoFrame.pack(fill="both", expand="yes", side="left")

        self.btn_snapshot = tki.Button(videoFrame, text="Snapshot!",
                                       command=self.takeSnapshot)
        self.btn_snapshot.pack(side="bottom", fill="both",
                               expand="yes", padx=10, pady=5)

        self.btn_pause = tki.Button(videoFrame, text="Pause", relief="raised", command=self.pauseVideo)
        self.btn_pause.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        #---------->Pre-planned flight<-----------------------
        planFrame = LabelFrame(controlFrame1, text="Pre-Planned")
        planFrame.pack(fill="both", expand="yes", side="right")

        # self.btn_preplanned1 = tki.Button(planFrame, text="Start planned route 1",
        #                                command=self.takeSnapshot)
        self.btn_preplanned1 = tki.Button(planFrame, text="Start planned route 1",
                                          command=self.plannedRoute1)
        self.btn_preplanned1.pack(side="bottom", fill="both",
                               expand="yes", padx=10, pady=5)

        # self.btn_preplanned2 = tki.Button(planFrame, text="Start planned route 2", relief="raised", command=self.pauseVideo)
        self.btn_preplanned2 = tki.Button(planFrame, text="Start planned route 2", relief="raised",
                                          command=self.plannedRoute2)
        self.btn_preplanned2.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        # self.btn_landing = tki.Button(
        #     self.root, text="Open Command Panel", relief="raised", command=self.openCmdWindow)
        # self.btn_landing.pack(side="bottom", fill="both",
        #                       expand="yes", padx=10, pady=5)

        #--------------------->Command Panel<-----------------------------
        # text0 = tki.Label(self.root,
        #                   text='This Controller map keyboard inputs to Tello control commands\n'
        #                        'Adjust the trackbar to reset distance and degree parameter',
        #                   font='Helvetica 10 bold'
        #                   )
        # text0.pack(side='top')


        # ---------->Instruction Frame Starts<-----------------------
        controlFrame2 = Frame(self.root)
        controlFrame2.pack(fill="both", expand="yes", side="bottom")
        
        instructionFrame = LabelFrame(controlFrame2, text="Instructions")
        instructionFrame.pack(fill="both", expand="yes", side="right")

        text1 = tki.Label(instructionFrame, text=
                          'W - Move Tello Up\n'
                          'S - Move Tello Down\n'
                          'A - Rotate Tello Counter-Clockwise\n'
                          'D - Rotate Tello Clockwise\n'
                          'Arrow Up - Move Tello Forward\n'
                          'Arrow Down - Move Tello Backward\n'
                          'Arrow Left - Move Tello Left\n'
                          'Arrow Right - Move Tello Right\n',
                          justify="left")
        text1.pack(side="right")

        #-------------------------->Flip Frame<-----------------------------------------


        flipFrame = LabelFrame(controlFrame2, text="Flip")
        flipFrame.pack(fill="both", expand="yes", side="left")

        self.btn_flipl = tki.Button(
            flipFrame, text="Flip Left", relief="raised", command=self.telloFlip_l)
        self.btn_flipl.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_flipr = tki.Button(
            flipFrame, text="Flip Right", relief="raised", command=self.telloFlip_r)
        self.btn_flipr.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_flipf = tki.Button(
            flipFrame, text="Flip Forward", relief="raised", command=self.telloFlip_f)
        self.btn_flipf.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        self.btn_flipb = tki.Button(
            flipFrame, text="Flip Backward", relief="raised", command=self.telloFlip_b)
        self.btn_flipb.pack(side="bottom", fill="both",
                            expand="yes", padx=10, pady=5)

        #------------------------> End of Flip Frame <------------------------

        #------------------------> Land/Takeoff <-----------------------------

        landFrame = LabelFrame(controlFrame2, text="Land / TakeOff")
        landFrame.pack(fill="both", expand="yes", side="right")

        self.btn_landing = tki.Button(
            landFrame, text="Land", relief="raised", command=self.telloLanding)
        self.btn_landing.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        self.btn_takeoff = tki.Button(
            landFrame, text="Takeoff", relief="raised", command=self.telloTakeOff)
        self.btn_takeoff.pack(side="bottom", fill="both",
                              expand="yes", padx=10, pady=5)

        #------------------------> End of Land/Takeoff <-----------------------

        # binding arrow keys to drone control
        self.tmp_f = tki.Frame(self.root, width=100, height=2)
        self.tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
        self.tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
        self.tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
        self.tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
        self.tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
        self.tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
        self.tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
        self.tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
        self.tmp_f.pack(side="bottom")
        self.tmp_f.focus_set()

        # self.btn_landing = tki.Button(
        #     panel, text="Flip", relief="raised", command=self.openFlipWindow)
        # self.btn_landing.pack(side="bottom", fill="both",
        #                       expand="yes", padx=10, pady=5)

        self.distance_bar = Scale(self.root, from_=0.02, to=5, tickinterval=0.01, digits=3, label='Distance(m)',
                                  resolution=0.01)
        self.distance_bar.set(0.2)
        self.distance_bar.pack(side="left")

        self.btn_distance = tki.Button(self.root, text="Reset Distance", relief="raised",
                                       command=self.updateDistancebar,
                                       )
        self.btn_distance.pack(side="left", fill="both",
                               expand="yes", padx=10, pady=5)

        self.degree_bar = Scale(self.root, from_=1, to=360, tickinterval=10, label='Degree')
        self.degree_bar.set(30)
        self.degree_bar.pack(side="right")

        self.btn_distance = tki.Button(self.root, text="Reset Degree", relief="raised", command=self.updateDegreebar)
        self.btn_distance.pack(side="right", fill="both",
                               expand="yes", padx=10, pady=5)

        #---------------------->End of Command Panel<-----------------------------
        
        # start a thread that constantly pools the video sensor for
        # the most recently read frame
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()

        # set a callback to handle when the window is closed
        self.root.wm_title("TELLO Controller")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        # the sending_command will send command to tello every 5 seconds
        self.sending_command_thread = threading.Thread(target = self._sendingCommand)
        
    def videoLoop(self):
        """
        The mainloop thread of Tkinter 
        Raises:
            RuntimeError: To get around a RunTime error that Tkinter throws due to threading.
        """
        try:
            # start the thread that get GUI image and drwa skeleton 
            time.sleep(0.5)
            self.sending_command_thread.start()
            while not self.stopEvent.is_set():                
                system = platform.system()

            # read the frame for GUI show
                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue 
            
            # transfer the format from frame to image         
                image = Image.fromarray(self.frame)

            # we found compatibility problem between Tkinter,PIL and Macos,and it will 
            # sometimes result the very long preriod of the "ImageTk.PhotoImage" function,
            # so for Macos,we start a new thread to execute the _updateGUIImage function.
                if system =="Windows" or system =="Linux":                
                    self._updateGUIImage(image)

                else:
                    thread_tmp = threading.Thread(target=self._updateGUIImage,args=(image,))
                    thread_tmp.start()
                    time.sleep(0.03)                                                            
        except RuntimeError, e:
            print("[INFO] caught a RuntimeError")

           
    def _updateGUIImage(self,image):
        """
        Main operation to initial the object of image,and update the GUI panel 
        """  
        image = ImageTk.PhotoImage(image)
        # if the panel none ,we need to initial it
        if self.panel is None:
            self.panel = tki.Label(image=image)
            self.panel.image = image
            self.panel.pack(side="left", padx=10, pady=10)
        # otherwise, simply update the panel
        else:
            self.panel.configure(image=image)
            self.panel.image = image

            
    def _sendingCommand(self):
        """
        start a while loop that sends 'command' to tello every 5 second
        """    

        while True:
            self.tello.send_command('command',0)
            time.sleep(5)

    def _sendCommand(self, command):
        """
        start a while loop that sends 'command' to tello every 5 second
        """


        self.tello.send_command(command)

    def _setQuitWaitingFlag(self):  
        """
        set the variable as TRUE,it will stop computer waiting for response from tello  
        """       
        self.quit_waiting_flag = True        
   
    # def openCmdWindow(self):
    #     """
    #     open the cmd window and initial all the button and text
    #     """        
    #     panel = Toplevel(self.root)
    #     panel.wm_title("Command Panel")

    #     # create text input entry
    #     text0 = tki.Label(panel,
    #                       text='This Controller map keyboard inputs to Tello control commands\n'
    #                            'Adjust the trackbar to reset distance and degree parameter',
    #                       font='Helvetica 10 bold'
    #                       )
    #     text0.pack(side='top')

    #     text1 = tki.Label(panel, text=
    #                       'W - Move Tello Up\t\t\tArrow Up - Move Tello Forward\n'
    #                       'S - Move Tello Down\t\t\tArrow Down - Move Tello Backward\n'
    #                       'A - Rotate Tello Counter-Clockwise\tArrow Left - Move Tello Left\n'
    #                       'D - Rotate Tello Clockwise\t\tArrow Right - Move Tello Right',
    #                       justify="left")
    #     text1.pack(side="top")

    #     #-------------------------->Start of Test<-----------------------------------------

    #     labelframe = LabelFrame(panel, text="Flip")
    #     labelframe.pack(fill="both", expand="yes", side="bottom")

    #     self.btn_flipl = tki.Button(
    #         labelframe, text="Flip Left", relief="raised", command=self.telloFlip_l)
    #     self.btn_flipl.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     self.btn_flipr = tki.Button(
    #         labelframe, text="Flip Right", relief="raised", command=self.telloFlip_r)
    #     self.btn_flipr.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     self.btn_flipf = tki.Button(
    #         labelframe, text="Flip Forward", relief="raised", command=self.telloFlip_f)
    #     self.btn_flipf.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     self.btn_flipb = tki.Button(
    #         labelframe, text="Flip Backward", relief="raised", command=self.telloFlip_b)
    #     self.btn_flipb.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     #------------------------------->End of Test<-----------------------------------------

    #     self.btn_landing = tki.Button(
    #         panel, text="Land", relief="raised", command=self.telloLanding)
    #     self.btn_landing.pack(side="bottom", fill="both",
    #                           expand="yes", padx=10, pady=5)

    #     self.btn_takeoff = tki.Button(
    #         panel, text="Takeoff", relief="raised", command=self.telloTakeOff)
    #     self.btn_takeoff.pack(side="bottom", fill="both",
    #                           expand="yes", padx=10, pady=5)

    #     # binding arrow keys to drone control
    #     self.tmp_f = tki.Frame(panel, width=100, height=2)
    #     self.tmp_f.bind('<KeyPress-w>', self.on_keypress_w)
    #     self.tmp_f.bind('<KeyPress-s>', self.on_keypress_s)
    #     self.tmp_f.bind('<KeyPress-a>', self.on_keypress_a)
    #     self.tmp_f.bind('<KeyPress-d>', self.on_keypress_d)
    #     self.tmp_f.bind('<KeyPress-Up>', self.on_keypress_up)
    #     self.tmp_f.bind('<KeyPress-Down>', self.on_keypress_down)
    #     self.tmp_f.bind('<KeyPress-Left>', self.on_keypress_left)
    #     self.tmp_f.bind('<KeyPress-Right>', self.on_keypress_right)
    #     self.tmp_f.pack(side="bottom")
    #     self.tmp_f.focus_set()

    #     # self.btn_landing = tki.Button(
    #     #     panel, text="Flip", relief="raised", command=self.openFlipWindow)
    #     # self.btn_landing.pack(side="bottom", fill="both",
    #     #                       expand="yes", padx=10, pady=5)

    #     self.distance_bar = Scale(panel, from_=0.02, to=5, tickinterval=0.01, digits=3, label='Distance(m)',
    #                               resolution=0.01)
    #     self.distance_bar.set(0.2)
    #     self.distance_bar.pack(side="left")

    #     self.btn_distance = tki.Button(panel, text="Reset Distance", relief="raised",
    #                                    command=self.updateDistancebar,
    #                                    )
    #     self.btn_distance.pack(side="left", fill="both",
    #                            expand="yes", padx=10, pady=5)

    #     self.degree_bar = Scale(panel, from_=1, to=360, tickinterval=10, label='Degree')
    #     self.degree_bar.set(30)
    #     self.degree_bar.pack(side="right")

    #     self.btn_distance = tki.Button(panel, text="Reset Degree", relief="raised", command=self.updateDegreebar)
    #     self.btn_distance.pack(side="right", fill="both",
    #                            expand="yes", padx=10, pady=5)

    # def openFlipWindow(self):
    #     """
    #     open the flip window and initial all the button and text
    #     """
        
    #     panel = Toplevel(self.root)
    #     panel.wm_title("Gesture Recognition")

    #     self.btn_flipl = tki.Button(
    #         panel, text="Flip Left", relief="raised", command=self.telloFlip_l)
    #     self.btn_flipl.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     self.btn_flipr = tki.Button(
    #         panel, text="Flip Right", relief="raised", command=self.telloFlip_r)
    #     self.btn_flipr.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     self.btn_flipf = tki.Button(
    #         panel, text="Flip Forward", relief="raised", command=self.telloFlip_f)
    #     self.btn_flipf.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)

    #     self.btn_flipb = tki.Button(
    #         panel, text="Flip Backward", relief="raised", command=self.telloFlip_b)
    #     self.btn_flipb.pack(side="bottom", fill="both",
    #                         expand="yes", padx=10, pady=5)
       
    def takeSnapshot(self):
        """
        save the current frame of the video as a jpg file and put it into outputpath
        """

        # grab the current timestamp and use it to construct the filename
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))

        p = os.path.sep.join((self.outputPath, filename))

        # save the file
        cv2.imwrite(p, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))
        print("[INFO] saved {}".format(filename))


    def pauseVideo(self):
        """
        Toggle the freeze/unfreze of video
        """
        if self.btn_pause.config('relief')[-1] == 'sunken':
            self.btn_pause.config(relief="raised")
            self.tello.video_freeze(False)
        else:
            self.btn_pause.config(relief="sunken")
            self.tello.video_freeze(True)

    def telloTakeOff(self):
        return self.tello.takeoff()                

    def telloLanding(self):
        return self.tello.land()

    def telloFlip_l(self):
        return self.tello.flip('l', 0)

    def telloFlip_r(self):
        return self.tello.flip('r', 0)

    def telloFlip_f(self):
        return self.tello.flip('f', 0)

    def telloFlip_b(self):
        return self.tello.flip('b', 0)

    def telloCW(self, degree):
        return self.tello.rotate_cw(degree, 0)

    def telloCCW(self, degree):
        return self.tello.rotate_ccw(degree, 0)

    def telloMoveForward(self, distance):
        return self.tello.move_forward(distance, 0)

    def telloMoveBackward(self, distance):
        return self.tello.move_backward(distance, 0)

    def telloMoveLeft(self, distance):
        return self.tello.move_left(distance, 0)

    def telloMoveRight(self, distance):
        return self.tello.move_right(distance, 0)

    def telloUp(self, dist):
        return self.tello.move_up(dist, 0)

    def telloDown(self, dist):
        return self.tello.move_down(dist, 0)

    def updateTrackBar(self):
        self.my_tello_hand.setThr(self.hand_thr_bar.get())

    def updateDistancebar(self):
        self.distance = self.distance_bar.get()
        print 'reset distance to %.1f' % self.distance

    def updateDegreebar(self):
        self.degree = self.degree_bar.get()
        print 'reset distance to %d' % self.degree

    def on_keypress_w(self, event):
        print "up %d m" % self.distance
        self.telloUp(self.distance)

    def on_keypress_s(self, event):
        print "down %d m" % self.distance
        self.telloDown(self.distance)

    def on_keypress_a(self, event):
        print "ccw %d degree" % self.degree
        self.tello.rotate_ccw(self.degree)

    def on_keypress_d(self, event):
        print "cw %d m" % self.degree
        self.tello.rotate_cw(self.degree)

    def on_keypress_up(self, event):
        print "forward %d m" % self.distance
        self.telloMoveForward(self.distance)

    def on_keypress_down(self, event):
        print "backward %d m" % self.distance
        self.telloMoveBackward(self.distance)

    def on_keypress_left(self, event):
        print "left %d m" % self.distance
        self.telloMoveLeft(self.distance)

    def on_keypress_right(self, event):
        print "right %d m" % self.distance
        self.telloMoveRight(self.distance)

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()

    def plannedRoute1(self):
        max_round = 5
        for x in range(max_round):
            current_round = x+1
            print('Round', current_round)
            if current_round == max_round:
                print("Low battery. This is the last round!")
            print(">>At Checkpoint 0")
            self.tello.takeoff()
            print("Drone is moving forward for 100 cm. Took around 5 seconds")
            self.tello.move_forward(100, 5)
            print(">>At Checkpoint 1")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 80 cm. Took around 4 seconds")
            self.tello.move_forward(80, 4)
            print(">>At Checkpoint 2")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 40 cm. Took around 2 seconds")
            self.tello.move_forward(40, 2)
            print(">>At Checkpoint 3")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 40 cm. Took around 2 seconds")
            self.tello.move_forward(40, 2)
            print(">>At Checkpoint 4")
            print("Drone is going to turn clockwise 90 degree")
            self.tello.rotate_cw(90, 1)
            print("Drone is moving forward for 60 cm. Took around 3 seconds")
            self.tello.move_forward(60, 3)
            print(">>At Checkpoint 5")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 40 cm. Took around 2 seconds")
            self.tello.move_forward(40, 2)
            print(">>At Checkpoint 0")
            print("==========================================================")
            if current_round == max_round:
                print("Returning to charging port")

        print("Landing")
        self.tello.land()
        print("Charging drone")

    def plannedRoute2(self):
        max_round = 5
        for x in range(max_round):
            current_round = x + 1
            print('Round', current_round)
            if current_round == max_round:
                print("Low battery. This is the last round!")
            print(">>At Checkpoint 0")
            self.tello.takeoff()
            print("Drone is moving forward for 100 cm. Took around 5 seconds")
            self.tello.move_forward(100, 5)
            print(">>At Checkpoint 1")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 80 cm. Took around 4 seconds")
            self.tello.move_forward(80, 4)
            print(">>At Checkpoint 2")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 40 cm. Took around 2 seconds")
            self.tello.move_forward(40, 2)
            print(">>At Checkpoint 3")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 40 cm. Took around 2 seconds")
            self.tello.move_forward(40, 2)
            print(">>At Checkpoint 4")
            print("Drone is going to turn clockwise 90 degree")
            self.tello.rotate_cw(90, 1)
            print("Drone is moving forward for 60 cm. Took around 3 seconds")
            self.tello.move_forward(60, 3)
            print(">>At Checkpoint 5")
            print("Drone is going to turn counter-clockwise 90 degree")
            self.tello.rotate_ccw(90, 1)
            print("Drone is moving forward for 40 cm. Took around 2 seconds")
            self.tello.move_forward(40, 2)
            print(">>At Checkpoint 0")
            print("==========================================================")
            if current_round == max_round:
                print("Returning to charging port")

        print("Landing")
        self.tello.land()
        print("Charging drone")

    def onClose(self):
        """
        set the stop event, cleanup the camera, and allow the rest of
        
        the quit process to continue
        """
        print("[INFO] closing...")
        self.stopEvent.set()
        del self.tello
        self.root.quit()

