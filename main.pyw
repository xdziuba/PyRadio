# -*- coding: utf-8 -*-

###########################
# Python Radio Player 0.3 #
# Written by Paweł Dziuba #
###########################

# Needed imports
import dearpygui.dearpygui as dpg
import miniaudio
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from os import system, getcwd
from threading import Thread
import time
from win32api import GetKeyState
import win32gui
from PIL import Image
import numpy as np
import requests
from io import BytesIO
from youtubesearchpython import VideosSearch

## Updates the stream title and loads image related (not always) to it
## Probably going to stop using youtubesearchpython for searching and receiving song thumbnails in favor of ytmusic api or spotify api
def receive_metadata(client: miniaudio.IceCastClient, title):
    if title != dpg.get_value('rds'):
        dpg.set_value('rds', title) # Update the displayed title
        dpg.reset_pos('rds') # Reset the position of the displayed title
    try:
        search = VideosSearch(title, limit=1) # Use the stream title to run a YouTube video search in order to retreive thumbnail of currently playing song
        link = search.result()['result'][0]['thumbnails'][0]['url']
        response = requests.get(link) # Make an HTTP request to get the thumbnail
        img = Image.open(BytesIO(response.content)).convert('RGBA') # Open the imageand convert to RGBA format
        resized = img.resize((214, 120))
        arr = np.array(resized)
        # Flatten the array to 1D and normalize it so the dpg texture registry can read it
        flat_arr = arr.ravel()
        data = np.divide(flat_arr , 255)
        dpg.set_value("thumbnail_texture", data) # Update the displayed thumbnail image
    except:
        pass # Ignore any exceptions if the thumbnail wasn't loaded properly

## Streams audio from an IceCast server and plays it back on an audio device (runs in separate thread)
def icecast_thread(url):
    source = miniaudio.IceCastClient(url, update_stream_title=receive_metadata, ssl_context=None)
    stream = miniaudio.stream_any(source, source.audio_format)
    device.start(stream)

## Handles closing the app
def close_app():
    global device
    device.stop()
    dpg.stop_dearpygui()

## Handles mouse draging the viewport
def move_viewport(sender, app_data):
    global current_pos
    if drag_region: # Check if mouse is in the region, which allows moving the viewport
        current_pos = [int(current_pos[0] + app_data[1]), int(current_pos[1] + app_data[2])]
        dpg.set_viewport_pos(current_pos)

## Opens the radio list file (button callback)
def open_radiolist(sender, app_data):
    global radio_stations
    global radio_stations_names
    system(f"notepad.exe {getcwd()}/radio_stations.list")
    # After closing the radio list: update the list widget
    radio_stations = []
    radio_stations_names = []
    with open('radio_stations.list', 'r') as f:
        for station in f.readlines():
            url, name = station.split("|")
            radio_stations.append([url, name])
            radio_stations_names.append(name)
    dpg.configure_item('radio_list', items=radio_stations_names)

## Volume slider callback
def change_vol(sender, app_data):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "pythonw.exe":
            volume = session._ctl.QueryInterface(ISimpleAudioVolume) # Get volume interface from session
            volume.SetMasterVolume(round(app_data/100, 2), None)

## Stop button callback
def stop_playback(sender, app_data):
    global device
    device.stop()
    dpg.set_value('rds', 'Waiting for metadata...')
    dpg.reset_pos('rds')
    resized = img.resize((214, 120))
    arr = np.array(resized)
    flat_arr = arr.ravel()
    data = np.divide(flat_arr , 255)
    dpg.set_value("thumbnail_texture", data)

## Input text box callback - handles searching
def search_box(sender, app_data):
    global filtered_stations
    filtered_stations = []
    for station in radio_stations:
        if app_data.lower() in station[1].lower():
            filtered_stations.append(station[1])
    dpg.configure_item('radio_list', items=filtered_stations) # Display filtered list

## List box callback - handles selecting station to be played
def list_box(sender, app_data):
    global now_playing
    global device
    device.stop()
    for station in radio_stations:
        if app_data in station[1]:
            dpg.set_value('rds', 'Waiting for metadata...')
            Thread(target=lambda: icecast_thread(station[0])).start() # Run the IceCast client in separate thread
            now_playing = station[0]
    dpg.reset_pos('rds')

## Variables used for viewport handling
current_pos = [400, 400]
drag_region = False
minimized = False
state_left = GetKeyState(0x01)

## Variables used for storing radio stations/stream title and also diplaying them in the gui
radio_stations = []
radio_stations_names = []
filtered_stations = []
now_playing = ''

# Create miniaudio playback device object
device = miniaudio.PlaybackDevice()

## Scan radio stations and append them to the list
with open('radio_stations.list', 'r') as f:
    for station in f.readlines():
        url, name = station.split("|")
        radio_stations.append([url, name])
        radio_stations_names.append(name)

## Load idle thumbnail
img = Image.open('assets/idle.jpg').convert('RGBA')
resized = img.resize((214, 120))
arr = np.array(resized)
flat_arr = arr.ravel()
data = np.divide(flat_arr , 255)

## Create dearpygui context
dpg.create_context()

## Textures registry
with dpg.texture_registry(show=False):
    dpg.add_dynamic_texture(width=214, height=120, default_value=data, tag="thumbnail_texture")
    w, h, _, d = dpg.load_image("assets/stop.png")
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="stop_texture")
    w, h, _, d = dpg.load_image("assets/list.png")
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="list_texture")

## Define timers used to delay:  
thread_time = time.time() # running the receive_metadata thread
rds_slide_time = time.time() # sliding the stream title in GUI

## Add mouse listener for handling the viewport movement
with dpg.handler_registry():
    dpg.add_mouse_drag_handler(callback=move_viewport)

## Main window
with dpg.window(label='PyRadio', tag='Primary', width=230, height=345, no_move=True, no_collapse=False, no_resize=True, on_close=close_app):             
    dpg.add_input_text(hint="Aa...", width=214, callback=search_box)
    dpg.add_listbox(items=radio_stations_names, default_value=0, num_items=6, label='', width=214, tag='radio_list', callback=list_box)
    dpg.add_image("thumbnail_texture", width=214, height=120)
    dpg.add_text("Waiting for metadata...", tag='rds')
    with dpg.group(horizontal=True):
        dpg.add_slider_int(default_value=50, max_value=100, pos=[8, 315], callback=change_vol, width=155)
        dpg.add_image_button(texture_tag='stop_texture', width=13, height=13, callback=stop_playback)
        dpg.add_image_button(texture_tag='list_texture', width=13, height=13, callback=open_radiolist)

## DPG Startup
dpg.create_viewport(title='PyRadio', width=230, height=345, decorated=False, x_pos=current_pos[0], y_pos=current_pos[1])
dpg.set_exit_callback(callback=close_app)
dpg.set_viewport_large_icon('icon.ico')
dpg.set_viewport_small_icon('icon.ico')
dpg.setup_dearpygui()
dpg.show_viewport()

## Render loop
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame() # Render GUI frame
    
    ## Viewport drag check
    new_state_left = GetKeyState(0x01) # Get the current state of the left mouse button
    if new_state_left != state_left: # If the state has changed
        state_left = new_state_left # Update the state
        if new_state_left < 0: # If the left mouse button is pressed
            window_hwnd = win32gui.GetForegroundWindow() # Get the foreground window
            if win32gui.GetWindowText(window_hwnd) == 'PyRadio': # If it's a PyRadio window
                left_top_y = win32gui.GetWindowRect(window_hwnd)[1] # Get the top left y-coordinate of the window
                mouse_pos_y = win32gui.GetCursorPos()[1] # Get mouse y-coordinate
                pos_in_window_y = mouse_pos_y - left_top_y
                if 0 < pos_in_window_y < 18 and not drag_region: # If mouse is in the viewport drag region
                    drag_region = True
        else:
            if drag_region:
                drag_region = False

    ## Minimize check
    if not dpg.get_item_state('Primary')['visible'] and minimized == False: # If the collapse arrow was pressed and the viewport is not minimized
        dpg.configure_item('Primary', collapsed=False) # Uncollapse the viewport
        dpg.minimize_viewport()
        minimized = True
    if win32gui.GetWindowPlacement(win32gui.FindWindow("PyRadio", None))[1] == 1 and minimized == True: # If viewport got unminimized
        minimized = False

    ## Slider timer
    ## Handles the stream title displaying position in DPG window
    if time.time() - rds_slide_time > 0.1:
        if dpg.get_item_rect_max('rds')[0] > 214: # If the stream title is longer than width of the viewport
            dpg.set_item_pos('rds', [dpg.get_item_pos('rds')[0] - 1, dpg.get_item_pos('rds')[1]]) # Shift it to the left
        if dpg.get_item_rect_max('rds')[0] - 215 == 0: # If the whole text was shifted through the rds text box
            dpg.reset_pos('rds')
        rds_slide_time = time.time()
    
dpg.destroy_context()