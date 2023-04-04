import tkinter as tk
import sys
import cv2
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../../../..', ))
import controller
from PIL import Image, ImageTk


app = tk.Tk()
#ustawianie wymiarów
app_height=600
app_width=1200

screen_height=app.winfo_screenheight()
screen_width=app.winfo_screenwidth()
x_cordinate=int((screen_width/2)-(app_width/2))
y_cordinate=int((screen_height/2)-(app_height/2))
app.geometry("{}x{}+{}+{}".format(app_width,app_height,x_cordinate,y_cordinate))




def handle_start_button():
    controller.show_video()


label = tk.Label(app)
label.pack() 

start_button=tk.Button(app, text="Start", command=handle_start_button)
stop_button=tk.Button(app,text="Stop")
start_button.pack()
stop_button.pack()


app.mainloop()

