import socket

def initializeDeviceStore():
    global devices
    devices= dict()

def addNewDevice(sessionId, deviceIP):
    listToAppend=devices[sessionId]
    listToAppend.append(deviceIP)
    devices[sessionId]=listToAppend

def removeDevice(sessionId, deviceIP):
    listToRemove=devices[sessionId]
    listToRemove.remove(deviceIP)
    devices[sessionId]=listToRemove

def initializeSocket(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",int(port)))
    s.listen(1)
    conn, addr = s.accept()
    return conn, addr

def connectToSocket(host,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))


