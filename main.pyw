# -*- coding: utf-8 -*-

###########################
# Python Radio player 0.2 #
# Written by dziubahere   #
###########################

# Needed imports
import dearpygui.dearpygui as dpg
from pycaw.pycaw import AudioUtilities
from threading import Thread
from os import system, getcwd, environ, pathsep
import time
from win32api import GetKeyState
import win32gui
from PIL import Image
import numpy as np
import requests
from io import BytesIO
from youtubesearchpython import VideosSearch

environ['PATH'] += pathsep + f'{getcwd()}/mpv'
from mpv import mpv

## Updates the stream title and loads image related (not always) to it.
## Probably going to stop using youtubesearchpython for searching and receiving song thumbnails in favor of ytmusic api or spotify api.
def receive_metadata():
    time.sleep(1)
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if 'mpv' in session.DisplayName:
                title = session.DisplayName[:-6]
        if len(title) > 2:
            if title != dpg.get_value('rds'):
                dpg.set_value('rds', title)
                dpg.reset_pos('rds')
                videosSearch = VideosSearch(title, limit=1)
                link = videosSearch.result()['result'][0]['thumbnails'][0]['url']
                response = requests.get(link)
                img = Image.open(BytesIO(response.content)).convert('RGBA')
                resized = img.resize((214, 120))
                arr = np.array(resized)
                flat_arr = arr.ravel()
                data = np.divide(flat_arr , 255)
                dpg.set_value("texture_tag", data)
    except:
        pass

## Handles closing the app.
def close_app():
    dpg.stop_dearpygui()
    player.stop()

## Handles mouse dragging the viewport.
def move_viewport(sender, app_data):
    global current_pos
    if drag_region:
        current_pos = [int(current_pos[0] + app_data[1]), int(current_pos[1] + app_data[2])]
        dpg.set_viewport_pos(current_pos)

## Opens the radio list file (button callback).
def open_radiolist(sender, app_data):
    global radio_stations
    global radio_stations_names
    system(f"notepad.exe {getcwd()}/radio_stations.list")
    radio_stations = []
    radio_stations_names = []
    with open('radio_stations.list', 'r') as f:
        for station in f.readlines():
            url, name = station.split("|")
            radio_stations.append([url, name])
            radio_stations_names.append(name)
    dpg.configure_item('radio_list', items=radio_stations_names)

## Volume slider callback.
def change_vol(sender, app_data):
    player.volume = app_data

## Stop button callback.
def stop_playback(sender, app_data):
    player.stop()
    dpg.set_value('rds', 'Waiting for metadata...')
    dpg.reset_pos('rds')

## Input text box callback - handles searching.
def search_box(sender, app_data):
    global filtered_stations
    filtered_stations = []
    for station in radio_stations:
        if app_data.lower() in station[1].lower():
            filtered_stations.append(station[1])
    dpg.configure_item('radio_list', items=filtered_stations)

## List box callback - handles selecting station to be played
def list_box(sender, app_data):
    global now_playing
    player.stop()
    for station in radio_stations:
        if app_data in station[1]:
            player.play(station[0])
            now_playing = station[0]
            dpg.set_value('rds', 'Waiting for metadata...')
            x = Thread(target=receive_metadata)
            x.start()
    dpg.reset_pos('rds')

## Defining some variables
current_pos = [400, 400]
log_scale = [2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
drag_region = False
minimized = False
radio_stations = []
radio_stations_names = []
filtered_stations = []
now_playing = ''
state_left = GetKeyState(0x01)
player = mpv.MPV(ytdl=False)
player.volume = 50.0

## Scan radio stations and append them to the list.
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
    dpg.add_dynamic_texture(width=214, height=120, default_value=data, tag="texture_tag")
    w, h, _, d = dpg.load_image("assets/stop.png")
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="stop_texture")
    w, h, _, d = dpg.load_image("assets/list.png")
    dpg.add_static_texture(width=w, height=h, default_value=d, tag="list_texture")

start_time = time.time()
rds_slide_time = time.time()
visu_timer = time.time()

## Handlers
with dpg.handler_registry():
    dpg.add_mouse_drag_handler(callback=move_viewport)

## Main window
with dpg.window(label='PyRadio', tag='Primary', width=230, height=345, no_move=True, no_collapse=False, no_resize=True, on_close=close_app):             
    dpg.add_input_text(hint="Aa...", width=214, callback=search_box)
    dpg.add_listbox(items=radio_stations_names, default_value=0, num_items=6, label='', width=214, tag='radio_list', callback=list_box)
    dpg.add_image("texture_tag", width=214, height=120)
    dpg.add_text("Waiting for metadata...", tag='rds')
    with dpg.group(horizontal=True):
        dpg.add_slider_int(default_value=50, max_value=100, pos=[8, 315], callback=change_vol, width=155)
        dpg.add_image_button(texture_tag='stop_texture', width=13, height=13, callback=stop_playback)
        dpg.add_image_button(texture_tag='list_texture', width=13, height=13, callback=open_radiolist)

## Startup
dpg.create_viewport(title='PyRadio', width=230, height=345, decorated=False, x_pos=current_pos[0], y_pos=current_pos[1])
dpg.set_exit_callback(callback=close_app)
dpg.set_viewport_large_icon('icon.ico')
dpg.set_viewport_small_icon('icon.ico')
dpg.setup_dearpygui()
dpg.show_viewport()

## Render loop
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()
    
    ## Drag check
    a = GetKeyState(0x01)
    if a != state_left:
        state_left = a
        if a < 0:
            window_hwnd = win32gui.GetForegroundWindow()
            if win32gui.GetWindowText(window_hwnd) == 'PyRadio':
                left_top_y = win32gui.GetWindowRect(window_hwnd)[1]
                mouse_pos_y = win32gui.GetCursorPos()[1]
                pos_in_window_y = mouse_pos_y - left_top_y
                if 0 < pos_in_window_y < 18 and not drag_region:
                    drag_region = True
        else:
            if drag_region:
                drag_region = False

    ## Minimize check
    if not dpg.get_item_state('Primary')['visible'] and minimized == False:
        dpg.configure_item('Primary', collapsed=False)
        dpg.minimize_viewport()
        minimized = True
    if win32gui.GetWindowPlacement(win32gui.FindWindow("PyRadio", None))[1] == 1 and minimized == True:
        minimized = False
        
    ## Metadata receive timer
    if time.time() - start_time > 20:
        x = Thread(target=receive_metadata)
        x.start()
        start_time = time.time()

    ## Slider timer
    if time.time() - rds_slide_time > 0.1:
        if dpg.get_item_rect_max('rds')[0] > 214:
            dpg.set_item_pos('rds', [dpg.get_item_pos('rds')[0] - 1, dpg.get_item_pos('rds')[1]])
        if dpg.get_item_rect_max('rds')[0] - 215 == 0:
            dpg.reset_pos('rds')
        rds_slide_time = time.time()
    
dpg.destroy_context()