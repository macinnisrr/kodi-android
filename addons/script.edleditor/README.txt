This script lets you enable, disable, create and edit EDL files

This script works with:
EDL files entered in seconds
EDL files entered in minutes:seconds (will be converted into seconds internally)
EDL files entered in frames
Comskip TXT files (always entered in frames)

This addon will let you seek through keyframes to find an edit point. As editing of all frames requires transcoding, only keyframes as edit points are supported. Keyframes are in the video stream normally every 0.5 to 5 seconds.

Editing is normally done is seconds (and subseconds). If editing in seconds is not available (ffmpeg is not available and EDL is in frames), editing is done in frame numbers.

ffmpeg/ avconv:
===============

To have visual aid, ffmpeg or avconv tools are required to be installed. It is really recommended to install ffmpeg (if not yet installed) because it is used to obtain all the video information.

ffmpeg/ avconv can for example be installed on ubuntu with:
sudo apt install libav-tools 
or
sudo apt install ffmpeg

For other platforms see:
https://www.ffmpeg.org/download.html

====

Please send Comments and Bugreports to hellyrulez@home.nl

