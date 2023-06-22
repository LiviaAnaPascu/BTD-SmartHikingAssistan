from m5stack import *
from m5ui import *
from uiflow import *
import network
import socket
import struct
import imu
import math

serverCfg = {
    # "host": "192.168.1.103",
    "host": "192.168.43.113",
    "port": 50
}

# Thresholds for the detection
thStepP = 0.2  # save only peaks above this threshold
thLiftP = 0.35
thLiftN = -0.2  # save only peaks below this threshold
thFallP = 1.8  # check for robustness

neutral = False  # next step can only be found if signal was below 0 inbetween
liftP = False  # check whether positive part of lift occured first
liftN = False  # check whether negative part occured

inlift = False  # to check for negative part when in lift
fallen = False
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


def magnitude(acc):
    return math.sqrt(math.pow(acc[0], 2) + math.pow(acc[1], 2) + math.pow(acc[2], 2))


def lpf(val, prevVal, prevLpf):  # Low Pass Filter, Cutoff = 10
    result = (0.12019831) * prevLpf + (0.43990085) * val + (0.43990085) * prevVal
    return result


def hpf(val, prevVal, prevHpf):  # High Pass Filter, Cutoff = 0.1
    result = (0.99373649) * prevHpf + (0.99686825) * val + (-0.99686825) * prevVal
    return result


def send_msg(socket, msg):
    msg = struct.pack('>I', len(msg)) + msg  # pack message & length into byte structure
    socket.sendall(msg)


def buttonA_wasPressed():
    # global params
    global fallen

    fallen = False
    pass


btnA.wasPressed(buttonA_wasPressed)


def process_Window(window, time):
    neutral = False
    liftP = False
    liftN = False

    global inlift
    global lastTime
    global steps
    global fallen

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
                    elif value > thLiftP:  # Peak is possible Lift
                        if inlift and liftN:  # end lift
                            inlift = False
                            liftN = False
                            lastTime = time[ind]  # only save if positive
                        else:  # start lift start
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
                    lastTime = time[ind]
                elif inlift:  # end lift start
                    liftN = True


setScreenColor(0x111111)
label0 = M5TextBox(10, 30, "StepCounter", lcd.FONT_Default, 0xFFFFFF, rotate=0)
label1 = M5TextBox(10, 60, "Window", lcd.FONT_Default, 0xFFFFFF, rotate=0)
label2 = M5TextBox(10, 120, "Window2", lcd.FONT_Default, 0xFFFFFF, rotate=0)
imu0 = imu.IMU()

wait_ms(1000)
label0.setText("")

# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect('HH72VM_43BD_2.4G','dtF9dK6G')
# wlan.connect('HannibalsHorrificHotspot','honeybunny')

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

    if (c1 == samplenr):
        M5Led.on()
        process_Window(window1, time1)
        c1 = 0
        window1 = []
        time1 = []
        M5Led.off()

    if (c2 == samplenr):
        M5Led.on()
        process_Window(window2, time2)
        c2 = 0
        window2 = []
        time2 = []
        M5Led.off()

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

            # if (lastSaved != 0): #save over last peak if higher peak
            # if(c1>0):
            # window1.remove(len(window1))
            # time1.remove(len(time1))
            # if(c2>0):
            # window2.remove(len(window2))
            # time2.remove(len(time2))

            window1.append(prevFil)  # save the maximum
            time1.append(prevTime)

            window2.append(prevFil)
            time2.append(prevTime)

            lastSaved = prevFil

            ##Possibility: check for "fall heights" here so that detection is faster.



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

    prevLpf = curLpf
    prevFil = curFil
    prev = cur
    prevTime = curTime

    if (fallen):
        label0.setText("Error!")
        label1.setText("Error!!")
        label2.setText("Error!!!")
    elif (inlift):
        label0.setText(str(steps))
        label1.setText(str(c1))
        label2.setText(str(c2))
    else:
        label0.setText("")
        label1.setText("")
        label2.setText("")

    wait_ms(wait)