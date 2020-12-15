import tello
from tello_control_ui import TelloUI


def main():
    port = 9000
    port = 8889 
    
    drone = tello.Tello('', port)
    vplayer = TelloUI(drone,"./img/")
    
	# start the Tkinter mainloop
    vplayer.root.mainloop() 

if __name__ == "__main__":
    main()
