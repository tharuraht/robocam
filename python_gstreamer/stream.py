#

# http://lifestyletransfer.com/how-to-launch-gstreamer-pipeline-in-python/
import gi
import sys
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

HOSTIP = "192.168.0.99"
BITRATE = "2000000"
STREAM_PARAMS = "framerate=25/1,width=1280,height=720"

# Initialise
Gst.init(sys.argv)

# Gst.Pipeline
# pipeline = Gst.parse_launch(f"\
#     rpicamsrc preview=false rotation=180 annotation-mode=time+date name=src bitrate={BITRATE} \
#     ! video/x-h264,{STREAM_PARAMS} \
#     ! h264parse \
#     ! queue \
#     ! rtph264pay config-interval=1 pt=96 \
#     ! rtph264depay \
#     ! avdec_h264 \
#     ! videoconvert \
#     ! autovideosink sync=false")
pipeline = Gst.parse_launch("videotestsrc num-buffers=50 ! autovideosink")

# Start pipeline
pipeline.set_state(Gst.State.PLAYING)

# Init GObject loop to handle Gstreamer Bus Events 
loop = GObject.MainLoop() 
try: 
    loop.run()
except: 
    loop.quit()