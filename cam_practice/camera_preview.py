from picamera import PiCamera

camera = PiCamera()
camera.resolution = (1024,768)
camera.start_preview()

while True:
  pass