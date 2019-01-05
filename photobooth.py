#!/usr/bin/env python
#Photobooth.py
#Author: Andrew Quinn
#Python Version: 2.7

import os
import glob
import time
import traceback
from time import sleep
import RPi.GPIO as GPIO
import picamera # http://picamera.readthedocs.org/en/release-1.4/install2.html
import atexit
import sys
import socket
import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE
from pydrive.auth import GoogleAuth
from pydrive.auth import ServiceAccountCredentials
from pydrive.drive import GoogleDrive
import config # this is the config python file config.py
from signal import alarm, signal, SIGALRM, SIGKILL
from PIL import Image

# Variables
transform_x = config.monitor_w # how wide to scale the jpg when replaying
transfrom_y = config.monitor_h # how high to scale the jpg when replaying
offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos
replay_delay = 1 # how much to wait in-between showing pics on-screen after taking
replay_cycles = 2 # how many times to show each photo on-screen after taking

real_path = os.path.dirname(os.path.realpath(__file__))

# Auth Google
CREDS_FILE = "/home/pi/photobooth-pi/service_creds.json"
gauth = GoogleAuth()
scope = ['https://www.googleapis.com/auth/drive']
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
# gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(config.led_pin,GPIO.OUT) # LED
GPIO.setup(config.btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.output(config.led_pin,False) #for some reason the pin turns on at the beginning of the program

# initialize pygame
pygame.init()
pygame.display.set_mode((config.monitor_w, config.monitor_h))
screen = pygame.display.get_surface()
pygame.display.set_caption('Photo Booth Pics')
pygame.mouse.set_visible(False) #hide the mouse cursor
pygame.display.toggle_fullscreen()

#################
### Functions ###
#################

# clean up running programs as needed when main program exits
def cleanup():
  print('Ended abruptly')
  pygame.quit()
  GPIO.cleanup()
atexit.register(cleanup)

# A function to handle keyboard/mouse/device input events    
def input(events):
	for event in events:  # Hit the ESC key to quit the slideshow.
		if (event.type == QUIT or
			(event.type == KEYDOWN and event.key == K_ESCAPE)):
			pygame.quit()
				
#delete files in folder
def clear_pics(channel):
	files = glob.glob(config.file_path + '*')
	for f in files:
		os.remove(f) 
	#light the lights in series to show completed
	print "Deleted previous pics"
	for x in range(0, 3): #blink light
		GPIO.output(config.led_pin,True); 
		sleep(0.25)
		GPIO.output(config.led_pin,False);
		sleep(0.25)

# check if connected to the internet   
def is_connected():
  try: 
	# see if we can resolve the host name
	host = socket.gethostbyname(config.test_server)
	# connect to the host -- tells us if the host is actually reachable
	s = socket.create_connection((host, 80), 2)
	return True
  except:
	 pass
  return False    

# set variables to properly display the image on screen at right ratio
def set_demensions(img_w, img_h):
	# Note this only works when in booting in desktop mode. 
	# When running in terminal, the size is not correct (it displays small). Why?

	# connect to global vars
	global transform_y, transform_x, offset_y, offset_x

	# based on output screen resolution, calculate how to display
	ratio_h = (config.monitor_w * img_h) / img_w 

	if (ratio_h < config.monitor_h):
		#Use horizontal black bars
		#print "horizontal black bars"
		transform_y = ratio_h
		transform_x = config.monitor_w
		offset_y = (config.monitor_h - ratio_h) / 2
		offset_x = 0
	elif (ratio_h > config.monitor_h):
		#Use vertical black bars
		#print "vertical black bars"
		transform_x = (config.monitor_h * img_w) / img_h
		transform_y = config.monitor_h
		offset_x = (config.monitor_w - transform_x) / 2
		offset_y = 0
	else:
		#No need for black bars as photo ratio equals screen ratio
		#print "no black bars"
		transform_x = config.monitor_w
		transform_y = config.monitor_h
		offset_y = offset_x = 0

	# uncomment these lines to troubleshoot screen ratios
#     print str(img_w) + " x " + str(img_h)
#     print "ratio_h: "+ str(ratio_h)
#     print "transform_x: "+ str(transform_x)
#     print "transform_y: "+ str(transform_y)
#     print "offset_y: "+ str(offset_y)
#     print "offset_x: "+ str(offset_x)

# display one image on screen
def show_image(image_path):

	# clear the screen
	screen.fill( (0,0,0) )

	# load the image
	img = pygame.image.load(image_path)
	img = img.convert() 

	# set pixel dimensions based on image
	set_demensions(img.get_width(), img.get_height())

	# rescale the image to fit the current display
	img = pygame.transform.scale(img, (transform_x,transfrom_y))
	screen.blit(img,(offset_x,offset_y))
	pygame.display.flip()

# display a blank screen
def clear_screen():
	screen.fill( (0,0,0) )
	pygame.display.flip()

# display a group of images
def display_pics(jpg_group):
	for i in range(0, replay_cycles): #show pics a few times
		for i in range(1, config.total_pics+1): #show each pic
			show_image(config.file_path + jpg_group + "-0" + str(i) + ".png")
			time.sleep(replay_delay) # pause 

#fake showing the gif because pygame can't show gifs
def display_gif(gif_part):
	#convert milliseconds to 1/100s to match GraphicsMagick
	gif_delay = config.gif_delay / 100
	for i in range(0, 4): #show pics a few times
		for i in range(1, config.total_pics+1): #show each pic
			show_image(config.file_path + gif_part + "-0" + str(i) + ".png")
			time.sleep(gif_delay) # pause 
				
# define the photo taking function for when the big button is pressed 
def start_photobooth(): 

	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.

	################################# Begin Step 1 #################################

	print "Get Ready"
	GPIO.output(config.led_pin,False);
	show_image(real_path + "/instructions.png")
	sleep(config.prep_delay)
	
	# clear the screen
	clear_screen()
	
	camera = picamera.PiCamera()  
	camera.vflip = False
	camera.hflip = True # flip for preview, showing users a mirror image
	
	if config.black_and_white:
		camera.saturation = -100 # comment out this line if you want color images
	
	camera.iso = config.camera_iso
	
	pixel_width = 0 # local variable declaration
	pixel_height = 0 # local variable declaration
	
	if config.hi_res_pics:
		camera.resolution = (config.high_res_w, config.high_res_h) # set camera resolution to high res
	else:
		pixel_width = 600 # makes the gif smaller
		pixel_height = config.monitor_h * pixel_width // config.monitor_w
		camera.resolution = (pixel_width, pixel_height) # set camera resolution to low res
		
	################################# Begin Step 2 #################################
	
	print "Taking pics"
	
	now = time.strftime("%Y-%m-%d_%H:%M:%S") #get the current date and time for the start of the filename
	
	if config.capture_count_pics:
		try: # take the photos
			for i in range(1,config.total_pics+1):
				show_image(real_path + "/pose" + str(i) + ".png")
				time.sleep(config.capture_delay) # show pose number before taking & pause in-between shots
				camera.hflip = True # preview a mirror image
				camera.start_preview() # start preview at low res but the right ratio
				time.sleep(2) #warm up camera
				# GPIO.output(config.led_pin,True) #turn on the LED
				filename = config.file_path + now + '-0' + str(i) + '.png'
				camera.hflip = False # flip back when taking photo
				camera.capture(filename)
				print(filename)
				# GPIO.output(config.led_pin,False) #turn off the LED
				clear_screen()
				camera.stop_preview()
				
				if i == config.total_pics+1:
					break
		finally:
			camera.close()
	else:
		camera.start_preview(resolution=(config.monitor_w, config.monitor_h)) # start preview at low res but the right ratio
		time.sleep(2) #warm up camera
		
		try: #take the photos
			for i, filename in enumerate(camera.capture_continuous(config.file_path + now + '-' + '{counter:02d}.png')):
				# GPIO.output(config.led_pin,True) #turn on the LED
				print(filename)
				time.sleep(config.capture_delay) # pause in-between shots
				# GPIO.output(config.led_pin,False) #turn off the LED
				if i == config.total_pics-1:
					break
		finally:
			camera.stop_preview()
			camera.close()
		
	########################### Begin Step 3 #################################
	
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	
	if config.post_online:
		show_image(real_path + "/uploading.png")
	else:
		show_image(real_path + "/processing.png")

	# if you want the logo overlayed on the images
	if config.overlay_logo:
		for x in range(1, config.total_pics+1):
			print "pic " + str(x)
			output = "" + config.file_path + now + "-0" + str(x) + ".png"
			overlay_path = os.path.join(os.path.dirname(__file__), config.image_to_overlay)
			overlay = Image.open(overlay_path)
			output_img = Image.open(output).convert('RGBA')
			print(output_img)
			new_output = Image.alpha_composite(output_img, overlay)
			print "new output"
			new_output.save(output)
			print(output)

	if config.make_gifs: # make the gifs
		print "Creating an animated gif" 
		graphicsmagick = "gm convert -delay " + str(config.gif_delay) + " " + config.file_path + now + "*.png " + config.file_path + now + ".gif" 
		os.system(graphicsmagick) #make the .gif

	if config.post_online: # turn off posting pics online in config.py
		connected = is_connected() #check to see if you have an internet connection

		# Upload file to folder.
		f = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": config.folder_id}]})

		if (connected==False):
			print "bad internet connection"
					
		while connected:
			if config.make_gifs: 
				try:
					file_to_upload = config.file_path + now + ".gif"
					f['title'] = now + ".gif"

					# Make sure to add the path to the file to upload below.
					f.SetContentFile(file_to_upload)
					print(f.Upload())
					f['title'] = now + ".gif"
					print("Uploaded file")
					
					break
				except ValueError:
					print "Oops. No internect connection. Upload later."
					try: #make a text file as a note to upload the .gif later
						file = open(config.file_path + now + "-FILENOTUPLOADED.txt",'w')   # Trying to create a new file or open one
						file.close()
					except:
						print('Something went wrong. Could not write file.')
						sys.exit(0) # quit Python
			else: # upload jpgs instead
				try:
					# create an array and populate with file paths to our jpgs
					photos=[0 for i in range(4)]
					for i in range(4):
						photos[i]=config.file_path + now + "-0" + str(i+1) + ".png"

					for photo in photos:
						f.SetContentFile(photo)
						f.Upload()
						print("Uploaded file")

					break
				except ValueError:
					print "Oops. No internect connection. Upload later."
					try: #make a text file as a note to upload the .gif later
						file = open(config.file_path + now + "-FILENOTUPLOADED.txt",'w')   # Trying to create a new file or open one
						file.close()
					except:
						print('Something went wrong. Could not write file.')
						sys.exit(0) # quit Python               
	
	########################### Begin Step 4 #################################
	
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python
	
	if config.make_gifs:
		try:
			display_gif(now)
		except Exception, e:
			tb = sys.exc_info()[2]
			traceback.print_exception(e.__class__, e, tb)
			pygame.quit()
	else:	
		try:
			display_pics(now)
		except Exception, e:
			tb = sys.exc_info()[2]
			traceback.print_exception(e.__class__, e, tb)
			pygame.quit()
		
	print "Done"
	
	if config.post_online:
		show_image(real_path + "/finished.png")
	else:
		show_image(real_path + "/finished2.png")
	
	time.sleep(config.restart_delay)
	show_image(real_path + "/start.png");
	GPIO.output(config.led_pin,True) #turn on the LED

####################
### Main Program ###
####################

## clear the previously stored pics based on config settings
if config.clear_on_startup:
	clear_pics(1)

print "Photo booth app running..." 
for x in range(0, 5): #blink light to show the app is running
	GPIO.output(config.led_pin,True)
	sleep(0.25)
	GPIO.output(config.led_pin,False)
	sleep(0.25)

show_image(real_path + "/start.png");

while True:
	GPIO.output(config.led_pin,True); #turn on the light showing users they can push the button
	input(pygame.event.get()) # press escape to exit pygame. Then press ctrl-c to exit python.
	GPIO.wait_for_edge(config.btn_pin, GPIO.FALLING)
	time.sleep(config.debounce) #debounce
	start_photobooth()
