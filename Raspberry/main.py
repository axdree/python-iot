import RPi.GPIO as GPIO
import time
from RPLCD import CharLCD

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
servo = GPIO.PWM(17,50)
servo.start(5)
try:
    while True:
        servo.ChangeDutyCycle(5)
        time.sleep(2)
        servo.ChangeDutyCycle(10)
        time.sleep(2)
except:
    servo.stop()
    GPIO.cleanup()

    import time

from RPLCD import CharLCD
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(33, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)
GPIO.setup(29, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
lcd = CharLCD(numbering_mode=GPIO.BOARD, cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[33, 31, 29, 23])
try:
    while True:
        lcd.write_string(u"Hello world!")
except:
    pass
finally:
    GPIO.cleanup()