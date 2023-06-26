import socket
import threading
import array
from weather import *

devices = dict()


def addNewDevice(sessionId, deviceIP):
    listToAppend = devices[sessionId]
    listToAppend.append(deviceIP)
    devices[sessionId] = listToAppend


def removeDevice(sessionId, deviceIP):
    listToRemove = devices[sessionId]
    listToRemove.remove(deviceIP)
    devices[sessionId] = listToRemove


def handle_client(client_socket, address):
    # Process the request here...
    try:
        while True:
            msg = str(client_socket.recv(1024).decode())

            # index 0 = command, index 1 = value
            command = msg.split('#', 2)

            # value = sessionId
            if command[0] == "Register":
                addNewDevice(command[1], address)

            if command[0] == "Deregister":
                removeDevice(command[1], address)

            if command[0] == "Weather":
                uv = getUVIndexBasedOnIP(address)
                client_socket.send(str(uv).encode())

            # value = sessionId
            if command[0] == "Emergency":
                addresses = devices[command[1]]
                for addr in addresses:
                    if addr != address:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((addr, 421))
                        s.send("EMERGENCY!".encode())
                        s.close()

            if command[0] == "Stop":
                break
    except socket.error as ex:
        print(ex)
    finally:
        # Close the client socket
        client_socket.close()  # close the connection


def start_server():
    # Configure server host and port
    host = 'localhost'
    port = 420

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


