CC=gcc
CFLAGS=`pkg-config --cflags --libs gstreamer-rtsp-server-1.0`

robocam_rec: robocam_rec.c
	$(CC) $(CFLAGS) -o robocam_rec robocam_rec.c

# Prevent make from doing stuff with files name clean
.PHONY: clean

clean:
	rm -f robocam_rec