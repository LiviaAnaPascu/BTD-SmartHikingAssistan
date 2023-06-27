import socket
import threading
import array
from weather import *

devices = dict()


def addNewDevice(sessionId, deviceIP, name):
    if devices.get(sessionId) is None:
        temp = dict()
        devices.update({sessionId : temp})
    listToAppend = devices[sessionId]
    listToAppend.update({deviceIP[0] : name})
    devices[sessionId] = listToAppend


def removeDevice(sessionId, deviceIP):
    listToRemove = devices[sessionId]
    listToRemove.pop(deviceIP[0])
    if len(listToRemove) == 0:
        devices.pop(sessionId)
    devices[sessionId] = listToRemove


def handle_client(client_socket, address):
    # Process the request here...
    try:
        while True:
            msg = str(client_socket.recv(1024).decode())

            # index 0 = command, index 1 = value, ind 2 = name for register
            command = msg.split('*', 3)

            # value = sessionId
            if command[0] == "Register":
                addNewDevice(command[1], address, command[2])

            elif command[0] == "Deregister":
                removeDevice(command[1], address)

            elif command[0] == "Weather":
                uv,uvInd,temp,feelTemp,wh = convertUVIndexToString(command[1])
                client_socket.send((str(uv)+"*"+str(uvInd)+"*"+str(temp)+"*"+str(feelTemp)+"*"+str(wh)).encode())

            # value = sessionId
            elif command[0] == "Emergency":
                addresses = devices[command[1]]
                name = addresses[address[0]]
                for addr in addresses:
                    if addr != address[0]:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((addr, 420))
                        s.send(("Emergency*" + str(name)).encode())
                        s.close()

            elif command[0] == "Stop":
                break
    except socket.error as ex:
        print(ex)
    finally:
        # Close the client socket
        client_socket.close()  # close the connection


def start_server(ip):
    # Configure server host and port
    host = ip
    port = 50

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        # Accept a client connection
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr[0]}:{addr[1]}")

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr,))
        client_thread.start()


def initializeDeviceStore():
    global devices
    devices = dict()


ip = socket.gethostbyname(socket.gethostname())
initializeDeviceStore()
start_server(ip)


