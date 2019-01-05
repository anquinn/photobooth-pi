#Config settings to change behavior of the photobooth

# Hardware config
monitor_w = 800    								# width of the display monitor
monitor_h = 480    								# height of the display monitor
led_pin = 7 									# pin for the LED 
btn_pin = 18 									# pin for the start button
debounce = 0.3 									# how long to debounce the button. Add more time if the button triggers too many times
file_path = '/home/pi/Pictures/' 				# path to save images
camera_iso = 640    							# adjust for lighting issues. Normal is 100 or 200. Sort of dark is 400. Dark is 800 max.
                    							# available options: 100, 200, 320, 400, 500, 640, 800

# Photobooth config
total_pics = 4 									# number of pics to be taken
capture_delay = 1 								# delay between pics
prep_delay = 5 									# number of seconds at step 1 as users prep to have photo taken
restart_delay = 10 								# how long to display finished message before beginning a new session                    							
capture_count_pics = True 						# if true, show a photo count between taking photos. If false, do not. False is faster
clear_on_startup = False 						# True will clear previously stored photos as the program launches. False will leave all previous photos
hi_res_pics = True  							# True to save high res pics from camera
high_res_w = 1000 								# Width of high res image, if taken
high_res_h = 750 								# Height of high res image, if taken
# high_res_w = 2000 								# Width of high res image, if taken
# high_res_h = 1500 								# Height of high res image, if taken
												# full frame of v2 camera is 3280x2464. If you run into resource issues, try smaller

black_and_white = False 						# True to take photos in black and white
overlay_logo = True 							# True will overlay logo on top of the images
image_to_overlay = 'overlay.png'				# Name of the image to overlay
												# needs to be the same size as the hi_res size
# Gif config
make_gifs = True   								# True to make an animated gif. False to post 4 jpgs into one post.
gif_delay = 50	 								# How much time between frames in the animated gif

# Upload config
post_online = True 								# True to upload images. False to store locally only
folder_id = '' 									# Google Drive folder ID for uploads
test_server = 'www.google.com'					# server to check to se if connected to the internet