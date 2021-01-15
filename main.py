import tello
import routes
from tello_control_ui import TelloUI


def main():
    port = 9000
    port = 8889 
    
    drone = tello.Tello('', port)
    route = routes.Route.checkpoint
    vplayer = TelloUI(drone,route,"./img/")
    
	# start the Tkinter mainloop
    vplayer.root.mainloop() 

if __name__ == "__main__":
    main()
