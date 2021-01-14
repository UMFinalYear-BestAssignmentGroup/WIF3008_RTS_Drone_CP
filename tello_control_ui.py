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
        self.quit = False
        self.autoFlightToken = False
        self.current_round = 1
        self.current_checkpoint = 0
        self.isPause = False
        self.isStop = False
        
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

        consoleContent = LabelFrame(consoleFrame, text="Console", )
        consoleContent.pack(fill="both", expand="yes", side="left")


        scrollbar = Scrollbar(consoleContent)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.mylist = Listbox(consoleContent, yscrollcommand=scrollbar.set, width=100, selectmode=BROWSE )
        self.mylist.selection_set(first=0, last=None)
        self.mylist.selection_clear(2)
        self.mylist.see("end")

        self.mylist.pack(side=LEFT, fill=BOTH)
        scrollbar.config(command=self.mylist.yview)

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
        planFrame = LabelFrame(controlFrame1, text="Automatic Flight")
        planFrame.pack(fill="both", expand="yes", side="right")
        planFrame2 = Frame(planFrame)
        planFrame2.pack(fill="both", side="right")

        self.btn_autoFlight = tki.Button(planFrame, text="Start",
                                          command=self.autoControlFlight)
        self.btn_autoFlight.pack(side="top", fill="both",
                               expand="yes", padx=10, pady=5)

        self.btn_autoFlight_pause = tki.Button(planFrame2, text="Pause",
                                              command=self.auto_flight_pause)
        self.btn_autoFlight_pause.pack(side="top", fill="both",
                                      expand="yes", padx=10, pady=5)

        self.btn_autoFlight_stop = tki.Button(planFrame2, text="Stop",
                                              command=self.auto_flight_stop)
        self.btn_autoFlight_stop.pack(side="top", fill="both",
                                      expand="yes", padx=10, pady=5)
        self.btn_autoFlight_stop["state"] = DISABLED
        self.btn_autoFlight_pause["state"] = DISABLED

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

        self.btn_reset_battery = tki.Button(self.root, text="Reset to Full Battery", relief="raised",
                                            command=self.resetBattery)
        self.btn_reset_battery.pack(side="right", fill="both",
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
        self.loop = True
        while self.loop:
            self.root.update()
        
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

        # while True:
        #     self.tello.send_command('command',0)
        #     time.sleep(5)

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
            self.append_console("False")
        else:
            self.btn_pause.config(relief="sunken")
            self.tello.video_freeze(True)
            self.append_console("True")

    # ============> Drone functions <============

    def telloTakeOff(self):
        if not self.autoFlightToken:
            self.append_console("Take off")
            return self.tello.takeoff() 
        else:  
            self.auto_flight_pause() 

    def telloLanding(self):
        if not self.autoFlightToken:
            self.append_console("Landing")
            return self.tello.land()
        else:  
            self.auto_flight_pause()

    def telloFlip_l(self):
        if not self.autoFlightToken:
            self.append_console("Flip left")
            return self.tello.flip('l', 0)
        else:  
            self.auto_flight_pause()

    def telloFlip_r(self):
        if not self.autoFlightToken:
            self.append_console("Flip right")
            return self.tello.flip('r', 0)
        else:  
            self.auto_flight_pause()

    def telloFlip_f(self):
        if not self.autoFlightToken:
            self.append_console("Flip forward")
            return self.tello.flip('f', 0)
        else:  
            self.auto_flight_pause()

    def telloFlip_b(self):
        if not self.autoFlightToken:
            self.append_console("Flip backward")
            return self.tello.flip('b', 0)
        else:  
            self.auto_flight_pause()

    def telloCW(self, degree):
        if not self.autoFlightToken:
            self.append_console("Rotate clockwise")
            return self.tello.rotate_cw(degree, 0)
        else:  
            self.auto_flight_pause()

    def telloCCW(self, degree):
        if not self.autoFlightToken:
            self.append_console("Rotate Counter-clockwise")
            return self.tello.rotate_ccw(degree, 0)
        else:  
            self.auto_flight_pause()

    def telloMoveForward(self, distance):
        if not self.autoFlightToken:
            self.append_console("Moving Forward")
            return self.tello.move_forward(distance, 0)
        else:  
            self.auto_flight_pause()

    def telloMoveBackward(self, distance):
        if not self.autoFlightToken:
            self.append_console("Moving Backward")
            return self.tello.move_backward(distance, 0)
        else:  
            self.auto_flight_pause()

    def telloMoveLeft(self, distance):
        if not self.autoFlightToken:
            self.append_console("Moving Left")
            return self.tello.move_left(distance, 0)
        else:  
            self.auto_flight_pause()

    def telloMoveRight(self, distance):
        if not self.autoFlightToken:
            self.append_console("Moving Right")
            return self.tello.move_right(distance, 0)
        else:  
            self.auto_flight_pause()

    def telloUp(self, dist):
        if not self.autoFlightToken:
            self.append_console("Moving Upward")
            return self.tello.move_up(dist, 0)
        else:  
            self.auto_flight_pause()

    def telloDown(self, dist):
        if not self.autoFlightToken:
            self.append_console("Moving Downward")
            return self.tello.move_down(dist, 0)
        else:  
            self.auto_flight_pause()

    # ============> On key press functions <============

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
        self.telloCCW(self.degree)

    def on_keypress_d(self, event):
        print "cw %d m" % self.degree
        self.telloCW(self.degree)

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
    
    # ====================================

    # Send command to drone
    def runPlannedFlight(self, movement, value, delay):
        if movement == "forward":
            description = "Drone is moving forward for "+ str(value) +" cm. Took around "+ str(delay) +" seconds"
            self.append_console(description)
            self.tello.move_forward(value, delay)
            # self.tello.send_command(movement + " " + str(value), delay)
        elif movement == "cw":
            description = "Drone is going to turn clockwise "+ str(value) +" degree."
            self.append_console(description)
            self.tello.rotate_cw(value, delay)
            # self.tello.send_command(movement + " " + str(value), delay)
        elif movement == "ccw":
            description = "Drone is going to turn counter-clockwise " + str(value) + " degree."
            self.append_console(description)
            self.tello.rotate_ccw(value, delay)
            # self.tello.send_command(movement + " " + str(value), delay)
        elif movement == "landing":
            description = "Drone is landing "
            self.append_console(description)
            self.tello.land()
            # self.tello.send_command(movement + " " + str(value), delay)

    # Thread for Automatic Flight
    def flightThread(self):
        # Pre-planned flight for drone
        checkpoint = [[1, "ccw", 90, 1, "forward", 100, 5], [2, "ccw", 90, 1, "forward", 80, 4],
                      [3, "ccw", 90, 1, "forward", 40, 2], [4, "cw", 90, 1, "forward", 60, 3],
                      [5, "ccw", 90, 1, "forward", 40, 2], [0, "ccw", 90, 1, "forward", 40, 2]]
        i = self.current_checkpoint
        max_round = 5
        self.isStop = False

        self.append_console(
                    "==================================================================================")
        if i == 0:
            self.append_console("Switching to Automatic Mode. Starting flight")
            self.append_console("Takeoff")
            self.tello.takeoff()
        else:
            self.append_console("Continuing automatic flight")

        # Let drone run the pre-planned route 5 times
        while self.current_round <= max_round and self.autoFlightToken:
            print
            'Round ', self.current_round
            self.append_console('Round ' + str(self.current_round))
            if self.current_round == max_round:
                self.append_console("Low battery. This is the last round!")
            while i < len(checkpoint) and self.autoFlightToken:
                if (checkpoint[i][0] - 1) < 0:
                    print
                    'At checkpoint ', str(checkpoint[len(checkpoint) - 2][0])
                    self.append_console('At checkpoint ' + str(checkpoint[len(checkpoint) - 2][0]))
                else:
                    print
                    'At checkpoint ', str(checkpoint[i][0] - 1)
                    self.append_console('At checkpoint ' + str(checkpoint[i][0] - 1))
                self.runPlannedFlight(checkpoint[i][1], checkpoint[i][2], checkpoint[i][3])
                self.runPlannedFlight(checkpoint[i][4], checkpoint[i][5], checkpoint[i][6])
                # print 'Reached checkpoint ',  str(checkpoint[i][0])
                # self.append_console('Reached checkpoint '+  str(checkpoint[i][0]))
                self.append_console(
                    "==================================================================================")
                i += 1
                self.current_checkpoint += 1
            if not self.isPause:
                self.current_round += 1
            i = 0
        if self.current_round == max_round and not self.isPause and not self.isStop:
            self.append_console("Returning to charging port")
            print("Returning to charging port")
        if self.isPause:
            self.append_console("Flight paused. Please move to checkpoint "+ str(self.current_checkpoint) + " to continue Automatic Flight")
            print("Flight paused.")
        elif self.autoFlightToken:
            print("Landing")
            self.append_console("Landing")
            self.tello.land()
            self.append_console("Charging drone")
            print("Charging drone")
        else:
            self.append_console("Flight interrupted. Switching to Manual mode")
        # self.btn_autoFlight.config(relief="raised")
        if self.current_round == max_round:
            self.current_round = 1

    # Start/Stop thread when button is pressed
    def autoControlFlight(self):
        self.btn_autoFlight["state"] = DISABLED
        self.btn_autoFlight_pause["state"] = NORMAL
        self.btn_autoFlight_stop["state"] = NORMAL
        self.autoFlightToken = TRUE
        self.isPause = FALSE
        self.flightThread()

    # Print to Tkinter console
    def append_console(self, command):
        self.mylist.insert(END, command)
        self.mylist.see("end")
        self.root.update()

    def resetBattery(self):
        self.append_console("Battery reset to 100%")
        print("Battery reset to 100%")
        self.current_round = 1
        self.current_checkpoint = 0

    def auto_flight_pause(self):
        print("Paused")
        self.autoFlightToken = FALSE
        self.isPause = True
        self.btn_autoFlight["state"] = NORMAL
        self.btn_autoFlight_pause["state"] = DISABLED
        self.btn_autoFlight_stop["state"] = NORMAL

    def auto_flight_stop(self):
        print("Stoped")
        self.append_console(
                    "==================================================================================")
        self.append_console("Landing")
        self.append_console("Flight is stopped. Automatic Flight will be reseted.")
        self.tello.land()
        self.autoFlightToken = FALSE
        self.isStop = True
        self.btn_autoFlight_stop["state"] = DISABLED
        self.btn_autoFlight["state"] = NORMAL
        self.btn_autoFlight_pause["state"] = DISABLED
        self.current_checkpoint = 0

    # Close system
    def onClose(self):
        """
        set the stop event, cleanup the camera, and allow the rest of
        
        the quit process to continue
        """
        self.loop = False
        print("[INFO] closing...")
        self.stopEvent.set()
        del self.tello
        self.root.quit()
        self.root.destroy()
        print("Quited")

