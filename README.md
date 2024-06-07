# PyRadio 📻
<p align="center">
  <img src="https://i.imgur.com/GLUBvEX.png">
</p>

### (📋) Overview:
Simple radio stream player written in Python mainly using [DearPyGui](https://github.com/hoffstadt/DearPyGui) and [python-mpv](https://github.com/jaseg/python-mpv) libs. Currently only works on Windows due to heavy usage of [pywin32](https://pypi.org/project/pywin32/) for handling the custom viewport.
### (⚙️) Installation and usage:
At first run:
`pip install -r requirements.txt`\
After that you can run the script with: `python main.pyw`
### (🎉) Key features:
- ⚡️ Fast (UI is GPU accelerated thanks to DPG)
- ✒️ Receives stream titles
- 📷 Loads thumbnail related to currently playing song
- 📡 Allows easily adding new radio streams to the player
### (📌) To do:
- [ ] Switch to pyminiaudio instead of mpv (it's much lighter)
- [ ] Implement a new way of searching for a thumbnail of song (currently using [youtube-search-python](https://github.com/alexmercerind/youtube-search-python))
- [ ] Load base list of radio stations from the internet