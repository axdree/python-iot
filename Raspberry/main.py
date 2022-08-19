import RPi.GPIO as GPIO
import I2C_LCD_driver
import time, requests, json, schedule, threading
from ast import literal_eval
from datetime import datetime
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(17,GPIO.IN ,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.OUT)
servo = GPIO.PWM(26,50)
servo.start(5)

USERNAME="pythoniot"
PASSWORD="P@$$w0rd"
timeSchedule = {}
keyPressed = False
medTaken = False

def motion(channel):
    global medTaken
    if GPIO.input(17):
        medTaken = True
    else:
        pass
GPIO.add_event_detect(17, GPIO.RISING, callback=motion)

def LCDdisplay(msg):
    lcd = I2C_LCD_driver.lcd()
    lcd.backlight(1)
    lcd.lcd_display_string(msg, 1)

def buzz(duration):
    PWM = GPIO.PWM(18,100) #set 100Hz PWM output at GPIO 18
    PWM.start(20)
    time.sleep(duration)
    PWM.stop()

def dispense(qty):
    for i in range(qty):
        time.sleep(1)
        GPIO.output(23,1)
        time.sleep(0.5)
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

servo_range=[3,7,10,16]
def rotate(cyl):
    servo.start(servo_range[cyl-1])
    time.sleep(3)

def startSchedule():
    print("Waiting for schedule to hit")
    while True:
        schedule.run_pending()
        time.sleep(60) # wait one minute

def cycle(data):
    print("cycle1")
    global keyPressed
    keyPressed = False
    timeElapsed = 0
    while timeElapsed < 300:
        if keyPressed:
            for medication in data:
                rotate(int(medication['cylinder']))
                dispense(int(medication['dose']))
                requests.post(f'http://development.andreyap.com:7631/lowerStock?cyl={medication["cylinder"]}&qty={medication["dose"]}', auth=(USERNAME,PASSWORD))
                time.sleep(1)
            keyPressed = False
            return True
        else:
            time.sleep(1)
            timeElapsed += 1
    return False

def cycleWrapper(data, time):
    global medTaken
    print("cycleStarted")
    LCDdisplay("Press 0 to Disp")
    buzz(1)
    dispensed = cycle(data)
    cycleCount = 1
    while not dispensed and cycleCount < 12:
        buzz(1)
        dispensed = cycle(data)
        cycleCount += 1
    if not dispensed:
        print("Thinkspeak - not dispensed not taken")
        requests.get(f'https://api.thingspeak.com/update?api_key=9BXAQHAYAJLR8FW9&field1={datetime.now().strftime("%d/%m/%Y")}&field2={time}&field3=0')
        LCDdisplay("")
        requests.post(f"http://development.andreyap.com:7631/sendmessage?message=ALERT%3A%20Medication%20has%20not%20been%20dispensed%201%20hour%20after%20scheduled%20time%21", auth=(USERNAME,PASSWORD))
  
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
            requests.post(f"http://development.andreyap.com:7631/sendmessage?message=ALERT%3A%20Medication%20has%20not%20been%20taken%201%20hour%20after%20dispensed%20time%21", auth=(USERNAME,PASSWORD))
            LCDdisplay("")
            requests.get(f'https://api.thingspeak.com/update?api_key=9BXAQHAYAJLR8FW9&field1={datetime.now().strftime("%d/%m/%Y")}&field2={time}&field3=0')
        else:
            medTaken = False
            LCDdisplay("")
            print("Thinkspeak - dispensed and taken")

def main():
    LCDdisplay("")
    try:
        configResp = requests.get("http://development.andreyap.com:7631/retrconfig", auth=(USERNAME,PASSWORD))
    except Exception as e:
        print(f"Error: {e}")
        LCDdisplay("No Connection")
        buzz(5)
        time.sleep(60)
        quit()

    if literal_eval(configResp.json()['data']):
        global configuration
        configuration = literal_eval(configResp.json()['data'])
        for config in configuration:
            for time1 in config['timings']:
                if time1 in timeSchedule:
                    timeSchedule[time1].append({"cylinder":config['cylinderNum'],"dose":config['dosage']})
                else:
                    timeSchedule[time1] = [{"cylinder":config['cylinderNum'],"dose":config['dosage']}]
    else:
        LCDdisplay("No Config")
        buzz(3)
        time.sleep(60)
        quit()

    keypadThread = threading.Thread(target=read_key_pad)
    keypadThread.start()
    

    for i in timeSchedule:
        print(i)

        schedule.every().day.at(i).do(cycleWrapper,timeSchedule[i] , i)

    startSchedule()

if __name__ == "__main__":
    main()