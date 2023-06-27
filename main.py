from m5stack import *
from m5ui import *
from uiflow import *
from easyIO import *
import network
import socket
import struct
import imu
import math
import time
import wifiCfg
import _thread
import urequests

serverCfg = {
    # "host": "192.168.1.103",
    "host": "192.168.43.113",
    "port": 50
}

SCREEN_MAIN = 0
SCREEN_STEPS = 1
SCREEN_UV = 2
SCREEN_WEATHER = 3

# Current screen variable
current_screen = SCREEN_MAIN
axp.setLcdBrightness(100)

# Thresholds for the detection
thStepP = 0.2  # save only peaks above this threshold
thLiftP = 0.35
thLiftN = -0.2  # save only peaks below this threshold
thLiftP2 = 0.3
thFallP = 1.8  # check for robustness

# Different variables for signal processing
neutral = False  # next step can only be found if signal was below 0 inbetween
liftP = False  # check whether positive part of lift occured first
liftN = False  # check whether negative part occured
inlift = False  # to check for negative part when in lift
fallen = False
screenset = False  # to just set screen once
steps = 0  # counter
lastTime = -6  # important for sliding so no double steps occur
cur = 0  # store current value
prev = 0  # store previous magnitude
prevLpf = 0  # store previous magnitude after LPF
curLpf = 0  # store current mag after LPF
curFil = 0  # store current filtered value
prevFil = 0  # store previous filtered value
curTime = 0
prevTime = 0
window1 = []  # Values for 1st window
time1 = []  # Timestamps for values
c1 = 0  # Counter for first window
window2 = []
time2 = []
c2 = 0  # Counter second window
totalC = 0  # global counter
lastSaved = -6  # saves last saved value (needed for neutrals)
samplenr = 100  # samples per second: Windowsize is 1 second, offset = half a window
wait = int(1000 / samplenr)

# Weather Data
uv = ""
uvInd = 0
temperature = 0
tempFeels = 0
weather = ""

# Communication
sessionId = "HOBBIT_HIKE"
deviceName = "Sonja"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def send_msg(socket, msg):
    msg = struct.pack('>I', len(msg)) + msg  # pack message & length into byte structure
    socket.sendall(msg)


# Signal Processing utilities
def magnitude(acc):
    return math.sqrt(math.pow(acc[0], 2) + math.pow(acc[1], 2) + math.pow(acc[2], 2))


def lpf(val, prevVal, prevLpf):  # Low Pass Filter, Cutoff = 10
    result = (0.12019831) * prevLpf + (0.43990085) * val + (0.43990085) * prevVal
    return result


def hpf(val, prevVal, prevHpf):  # High Pass Filter, Cutoff = 0.1
    result = (0.99373649) * prevHpf + (0.99686825) * val + (-0.99686825) * prevVal
    return result


def process_Window(window, time):
    neutral = False
    liftP = False
    liftN = False

    global inlift
    global lastTime
    global steps
    global fallen
    global screenset

    for ind in range(0, len(window)):
        if (time[ind] > lastTime):  # only check index if it wasn't processed yet
            value = window[ind]
            if (value == 0):  # neutral check
                neutral = True
            elif (value > 0):  # check positive Peaks
                if neutral:  # only count positive Peaks if neutral before
                    if value > thFallP:  # Peak is possible Fall, checked for Fall before though
                        neutral = False
                        fallen = True
                        if liftP:
                            steps = steps + 1  # count previous peak as step
                            liftP = False
                        elif inlift:  # take away lift flag
                            liftN = False
                        lastTime = time[ind]
                    elif value > thLiftP2:  # Peak is possible Lift
                        if inlift and liftN:  # end lift
                            screenset = False
                            inlift = False
                            liftN = False
                            lastTime = time[ind]  # only save if positive
                        elif value > thLiftP:  # start lift start
                            liftP = True
                    else:  # just a step
                        if liftP:
                            steps = steps + 1  # count previous peak as step
                            liftP = False
                        elif inlift:  # take away lift flag
                            liftN = False
                        steps = steps + 1
                        lastTime = time[ind]
                neutral = False
            else:  # check negative Peaks
                if liftP:  # start lift
                    inlift = True
                    liftP = False
                    screenset = False
                    lastTime = time[ind]
                elif inlift:  # end lift start
                    liftN = True


# Button inputs
def buttonB_wasPressed():
    global current_screen, last_activity_time

    last_activity_time = time.time()
    # Increment the current screen
    current_screen += 1

    # Wrap around if the current screen exceeds the maximum screen ID
    if current_screen > SCREEN_WEATHER:
        current_screen = SCREEN_MAIN

    # Clear the screen
    lcd.clear()

    # Display the appropriate screen based on the current screen ID
    if current_screen == SCREEN_MAIN:
        main_screen()
    elif current_screen == SCREEN_STEPS:
        steps_screen()
    elif current_screen == SCREEN_UV:
        uv_screen()
    elif current_screen == SCREEN_WEATHER:
        weather_screen()


btnB.wasPressed(buttonB_wasPressed)


def buttonA_wasPressed():
    # global params
    global fallen
    global inlift
    global screenset

    if fallen:
        fallen = False
    elif inlift:
        inlift = False
    else:
        inlift = True

    screenset = False
    pass


btnA.wasPressed(buttonA_wasPressed)


# Screen Functions

def main_screen():
    global uv
    global temperature
    global steps

    lcd.clear()
    axp.setLcdBrightness(100)
    Date = M5TextBox(7, 12, date_string, lcd.FONT_DefaultSmall, 0x94b5b1, rotate=0)
    Time = M5TextBox(7, 90, time_string, lcd.FONT_DejaVu40, 0xedef6e, rotate=0)
    Battery = M5TextBox(100, 12, battery, lcd.FONT_DefaultSmall, 0x94b5b1, rotate=0)
    Steps = M5Rect(7, 140, 120, 25, 0x707070, 0x707070)
    Weather = M5Rect(7, 175, 120, 25, 0x707070, 0x707070)
    rectangle0 = M5Rect(7, 210, 120, 25, 0x707070, 0x707070)
    StepImage = M5Img(30, 143, "res/footprint.png", True)
    TempImage = M5Img(30, 178, "res/weather.png", True)
    UVImage = M5Img(30, 213, "res/beach.png", True)
    StepCounter = M5TextBox(54, 144, str(steps), lcd.FONT_DejaVu18, 0x000000, rotate=0)
    Temperature = M5TextBox(54, 180, '{}°C'.format(temperature), lcd.FONT_DejaVu18, 0x000000, rotate=0)
    label1 = M5TextBox(55, 215, uv, lcd.FONT_DejaVu18, 0x000000, rotate=0)


def steps_screen():
    global steps
    lcd.clear()
    setScreenColor(0x000000)
    axp.setLcdBrightness(100)
    Frame = M5Rect(7, 60, 120, 120, 0x707070, 0x707070)
    StepImage = M5Img(60, 70, "res/footprint.png", True)
    label0 = M5TextBox(25, 100, "Today's count:", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
    StepCounter = M5TextBox(43, 120, str(steps), lcd.FONT_DejaVu18, 0x000000, rotate=0)


def uv_screen():
    lcd.clear()
    global uv
    global uvInd
    axp.setLcdBrightness(100)
    setScreenColor(0x000000)
    Frame = M5Rect(7, 60, 120, 120, 0x707070, 0x707070)
    UVImage = M5Img(60, 70, "res/beach.png", True)
    label0 = M5TextBox(47, 100, "UV index:", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
    UVIndex = M5TextBox(35, 120, str(uvInd) + " " + uv, lcd.FONT_DejaVu18, 0x000000, rotate=0)
    # TODO: Adapt this text based on uv level
    label2 = M5TextBox(12, 145, "Protection needed!", lcd.FONT_DefaultSmall, 0x000000, rotate=0)


def weather_screen():
    lcd.clear()
    global tempFeels
    global temperature
    global weather
    axp.setLcdBrightness(100)
    setScreenColor(0x000000)
    Frame = M5Rect(7, 60, 120, 120, 0x707070, 0x707070)
    # TODO: Adapt picture based on weather
    WeatherImage = M5Img(60, 70, "res/weather.png", True)
    label0 = M5TextBox(30, 100, "Temperature:", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
    Temperature = M5TextBox(45, 120, str(temperature) + " \u00B0C", lcd.FONT_DejaVu18, 0x000000, rotate=0)
    label2 = M5TextBox(20, 145, "Feels like " + str(tempFeels) + " \u00B0C", lcd.FONT_DefaultSmall, 0x000000, rotate=0)


def fall_screen():
    lcd.clear()
    axp.setLcdBrightness(100)
    setScreenColor(0x000000)
    Frame = M5Rect(5, 60, 124, 160, 0x707070, 0x707070)
    StepImage = M5Img(60, 70, "res/warning.png", True)
    label0 = M5TextBox(20, 100, "Emergency Alert!", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
    label2 = M5TextBox(23, 130, "Did you Fall?", lcd.FONT_Default, 0x000000, rotate=0)
    label3 = M5TextBox(10, 149, "Press Button A", lcd.FONT_Default, 0x000000, rotate=0)
    label4 = M5TextBox(10, 168, "to cancel Alert", lcd.FONT_Default, 0x000000, rotate=0)

    for i in range(0, 10):
        PWM0 = machine.PWM(2, freq=500, duty=50, timer=0)
        wait_ms(90)
        PWM0 = machine.PWM(2, freq=200, duty=0, timer=0)
        M5Led.on()
        wait_ms(90)
        M5Led.off()
        wait_ms(2)

    label2.setText("An Alert was")
    label3.setText("sent to all other")
    label4.setText("linked Devices!")

    send_emergency()


def alert_screen():
    lcd.clear()
    axp.setLcdBrightness(100)
    setScreenColor(0xffffff)
    Frame = M5Rect(7, 60, 120, 120, 0xffffff, 0xffffff)
    StepImage = M5Img(60, 70, "res/warning.png", True)
    label0 = M5TextBox(20, 114, "Emergency Alert!", lcd.FONT_DefaultSmall, 0x000000, rotate=0)
    label2 = M5TextBox(49, 130, "From", lcd.FONT_Default, 0x000000, rotate=0)
    label3 = M5TextBox(33, 149, "DEVICE 1", lcd.FONT_Default, 0x000000, rotate=0)
    PWM0 = machine.PWM(2, freq=500, duty=50, timer=0)
    wait_ms(90)
    PWM0 = machine.PWM(2, freq=200, duty=0, timer=0)
    M5Led.on()
    wait_ms(90)
    M5Led.off()
    wait_ms(2)


def notification(text):
    wait(1)
    axp.setLcdBrightness(100)
    Frame = M5Rect(7, 30, 120, 50, 0x707070, 0xedef6e)
    label0 = M5TextBox(20, 40, text, lcd.FONT_Default, 0x000000, rotate=0)
    wait(2)
    Frame.hide()
    label0.hide()


# Communication Functions

def handle_emergency_messages():
    host = 'localhost'
    port = 421

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    client_socket, addr = server_socket.accept()
    # print(f"Accepted connection from {addr[0]}:{addr[1]}")

    # Trigger buzzer here and show UI stuff
    alert_screen()

    # close connection
    client_socket.close()
    server_socket.close()


def register_device():
    msg = "Register*" + sessionId + "*" + deviceName
    s.send(msg.encode())


def deregister_device():
    msg = "Deregister*" + sessionId
    s.send(msg.encode())


def get_weather(pubIp):
    msg = "Weather*" + pubIp
    s.send(msg.encode())

    rsp = str(s.recv(1024).decode())
    return rsp


def send_emergency():
    connect_to_server()
    msg = "Emergency*" + sessionId
    s.send(msg.encode())
    close_connection()


def connect_to_server():
    s.connect((serverCfg["host"], serverCfg["port"]))


def close_connection():
    s.close()


# WLAN Connection and Server Communication Setups
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('HH72VM_43BD_2.4G', 'dtF9dK6G')
wlan.connect('HannibalsHorrificHotspot', 'honeybunny')
wait_ms(100)

# We need the public IP otherwise we can't get any location data
publicIP = urequests.get(url='https://api.ipify.org').text
connect_to_server()
register_device()
responseWeather = get_weather(publicIP)
response = responseWeather.split("*", 5)
uv = response[0]
uvInd = response[1]
temperature = response[2]
tempFeels = response[3]
weather = response[4]
close_connection()

# Set Up Threading
_thread.start_new_thread(handle_emergency_messages, ())

# Setup for screen
setScreenColor(0x000000)
axp.setLcdBrightness(0)
last_activity_time = time.time()
battery = (str((map_value((axp.getBatVoltage()), 3.7, 4.1, 0, 100))) + str('%'))
date = rtc.now()
# Extract the time components
hour = int(date[3])
minute = int(date[4])
# Format the time string as "HH:MM"
time_string = "{:02d}:{:02d}".format(hour, minute)
# Extract the date components
year = int(date[0])
month = int(date[1])
day = int(date[2])
# Format the date string as "Mon dd"
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
date_string = "{} {:02d}".format(month_names[month - 1], day)

# SetUp for Signal Processing
imu0 = imu.IMU()
wait_ms(1000)

# 1st sample, no filtering yet
prev = magnitude(imu0.acceleration)
wait_ms(wait)

# Filtering only LPF first
cur = magnitude(imu0.acceleration)
curLpf = lpf(cur, prev, (1.000))
prevLpf = curLpf
prevFil = curLpf
prev = cur
wait_ms(wait)

# First time both filtered
cur = magnitude(imu0.acceleration)
curTime = -1
curLpf = lpf(cur, prev, prevLpf)
curFil = hpf(curLpf, prevLpf, 0.00)
prevLpf = curLpf
prevFil = curFil
prev = cur
prevTime = curTime
wait_ms(wait)

# Setup over, Loop Start
while True:
    # Get Processing Values
    cur = magnitude(imu0.acceleration)
    curTime = totalC
    curLpf = lpf(cur, prev, prevLpf)
    curFil = hpf(curLpf, prevLpf, prevFil)

    totalC = totalC + 1  # global timestamp clock
    c1 = c1 + 1
    c2 = c2 + 1

    if (totalC == (samplenr / 2)):  # 50 samples have been taken, initialize second window
        c2 = 0
        window2 = []
        time2 = []

    if (c1 == samplenr):  # Process and reset Window 1
        # M5Led.on()
        process_Window(window1, time1)
        c1 = 0
        window1 = []
        time1 = []
        # M5Led.off()

    if (c2 == samplenr):  # Process and reset Window 2
        # M5Led.on()
        process_Window(window2, time2)
        c2 = 0
        window2 = []
        time2 = []
        # M5Led.off()

    # do all the checking for thresholds
    if (curFil < 0.07) and (curFil > -0.07):  # Neutral range, save it
        if (lastSaved != 0):
            window1.append(0)
            time1.append(curTime)
            window2.append(0)
            time2.append(curTime)
            lastSaved = 0

    elif curFil < prevFil:  # prev Peak was local max, moving down
        if (prevFil > thStepP) and (prevFil > lastSaved):
            # Save only positive Peaks above Step threshold, others don't matter
            # Save only the peaks => only the highest Values, not all the values going down

            if (lastSaved != 0):  # save over last peak if higher peak
                if (len(window1) > 0):
                    del window1[len(window1) - 1]
                    del time1[len(time1) - 1]
                if (len(window2) > 0):
                    del window2[len(window2) - 1]
                    del time2[len(time2) - 1]

            window1.append(prevFil)  # save the maximum
            time1.append(prevTime)

            window2.append(prevFil)
            time2.append(prevTime)

            lastSaved = prevFil

        elif (prevFil > 0) and (curFil < 0):  # samples too coarse to catch neutralize
            if (lastSaved != 0):
                window1.append(0)
                time1.append(curTime)
                window2.append(0)
                time2.append(curTime)
                lastSaved = 0

    else:  # prev peak was local min, moving up
        if (prevFil < thLiftN) and (prevFil < lastSaved):
            window1.append(prevFil)  # save the minimum
            time1.append(prevTime)

            window2.append(prevFil)
            time2.append(prevTime)

            lastSaved = prevFil
        elif (curFil > 0) and (prevFil < 0):  # samples too course to catch neutralize
            if (lastSaved != 0):
                window1.append(0)
                time1.append(curTime)
                window2.append(0)
                time2.append(curTime)
                lastSaved = 0

    # Set Up for next Round
    prevLpf = curLpf
    prevFil = curFil
    prev = cur
    prevTime = curTime

    # Screenactions
    if (fallen and not screenset):
        # first check for 10 secs then send alarm message
        # possibly exchange
        fall_screen()
        screenset = True
        fallen = False
    elif (inlift and not screenset):
        main_screen()
        screenset = True
    elif (not screenset):
        lcd.clear()
        setScreenColor(0x000000)
        axp.setLcdBrightness(0)

    wait_ms(wait)