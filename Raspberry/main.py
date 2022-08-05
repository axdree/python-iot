import RPi.GPIO as GPIO
import I2C_LCD_driver
import time, requests, json, schedule, threading
from ast import literal_eval

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(17,GPIO.IN ,pull_up_down=GPIO.PUD_DOWN)
servo = GPIO.PWM(26,50)
servo.start(5)

USERNAME="pythoniot"
PASSWORD="P@$$w0rd"
timeSchedule = {}
keyPressed = False
medTaken = False

def motion(channel):
    global medTaken
    medTaken = True
GPIO.add_event_detect(17, GPIO.RISING, callback=motion)

def LCDdisplay(msg):
    mylcd = I2C_LCD_driver.lcd()
    mylcd.lcd_display_string(msg , 1,1)

def buzz(duration):
    PWM = GPIO.PWM(18,100) #set 100Hz PWM output at GPIO 18
    PWM.start(20)
    time.sleep(duration)
    PWM.stop()

def dispense(qty):
    for i in range(qty):
        time.sleep(1)
        GPIO.output(23,1)
        time.sleep(0.2)
        GPIO.output(23,0)

def read_key_pad():
    global keyPressed
    MATRIX = [[1,2,3],
            [4,5,6],
            [7,8,8],
            ['*' , 0, "#"]]
    ROW=[6,20,19,13] #row pins
    COL=[12,5,16] #column pins
    for i in range(3):
        GPIO.setup(COL[i] , GPIO.OUT)
        GPIO.output(COL[i] , 1)

    for j in range(4):
        GPIO.setup(ROW[j] , GPIO.IN, pull_up_down = GPIO.PUD_UP)


    while True:
        text = ''
        for i in range(3):
            GPIO.output(COL[i] , 0)
            for j in range(4):
                if GPIO.input(ROW[j]) == 0 :
                    if  MATRIX[j][i] == "#":
                        break
                    text += str (MATRIX[j][i])
                    while GPIO.input(ROW[j]) == 0 :
                        time.sleep(0.1)
            GPIO.output(COL[i] , 1 )
        if text != '':
            keyPressed = True

servo_range=[3,8,16,24]
def rotate(cyl):
    servo.start(servo_range[cyl-1])
    time.sleep(1)

def startSchedule():
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute

def cycle(data):
    global keyPressed
    keyPressed = False
    timeElapsed = 0
    while timeElapsed < 300 and not keyPressed:
        if keyPressed:
            for medication in data:
                requests.post('')
                rotate(int(medication['cylinder']))
                dispense(int(medication['dose']))
                requests.post(f'http://127.0.0.1:1234/lowerstock?cyl={medication["cylinder"]}', auth=(USERNAME,PASSWORD))
                time.sleep(1)
            keyPressed = False
            return True
        else:
            time.sleep(1)
    return False

def cycleWrapper(data):
    dispensed = cycle(data)
    cycleCount = 1
    while not dispensed and cycleCount < 12:
        dispensed = cycle(data)
        cycleCount += 1
    if not dispensed:
        print("Thinkspeak - not dispensed not taken")
        requests.post(f"http://127.0.0.1:1234/sendmessage?message=ALERT%3A%20Medication%20has%20not%20been%20dispensed%201%20hour%20after%20scheduled%20time%21", auth=(USERNAME,PASSWORD))
    else:
        takenTimerCount = 0
        while not medTaken and takenTimerCount < 3600:
            if takenTimerCount % 300 == 0:
                buzz(1)
                takenTimerCount += 1
            else:
                time.sleep(1)
                takenTimerCount += 1
        if not medTaken:
            print("Thinkspeak - dispensed not taken")
            requests.post(f"http://127.0.0.1:1234/sendmessage?message=ALERT%3A%20Medication%20has%20not%20been%20taken%201%20hour%20after%20dispensed%20time%21", auth=(USERNAME,PASSWORD))
        else:
            print("Thinkspeak - dispensed and taken")

def main():
    try:
        configResp = requests.get("http://127.0.0.1:1234/retrconfig", auth=(USERNAME,PASSWORD))
        stock = requests.get("http://127.0.0.1:1234/getstock", auth=(USERNAME,PASSWORD)).json()
    except Exception as e:
        print(f"Error: {e}")
        LCDdisplay("No Connection")
        buzz(5)
        time.sleep(60)
        quit()

    if configResp:
        global configuration
        configuration = literal_eval(configResp.json()['data'])
        for config in configuration:
            for time in config['timings']:
                if time in config:
                    timeSchedule[time].append({"cylinder":config['cylinderNum'],"dose":config['dosage']})
                else:
                    timeSchedule[time] = [{"cylinder":config['cylinderNum'],"dose":config['dosage']}]
    else:
        LCDdisplay("No Config")
        buzz(5)
        time.sleep(60)
        quit()

    keypadThread = threading.Thread(target=read_key_pad)
    keypadThread.start()

    for i in timeSchedule:
        schedule.every().day.at(i).do(cycleWrapper,timeSchedule[i])

    startSchedule()

if "__name__" == "__main__":
    main()