import socket
import threading

serverCfg = {
    # add correct server address here
    "host": "192.168.43.113",
    "port": 50
}

sessionId = "HOBBIT_HIKE"
deviceName = "Mock"
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = socket.gethostbyname(socket.gethostname()).split(":")[0]

# start like this:
# thread = threading.Thread(target=handle_emergency_messages, args=())
# thread.start()

def handle_emergency_messages():
    host = socket.gethostbyname(socket.gethostname()).split(":")[0]
    port = 420

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    client_socket, addr = server_socket.accept()
    # print(f"Accepted connection from {addr[0]}:{addr[1]}")

    rsp = str(client_socket.recv(1024).decode())
    # Trigger buzzer here and show UI stuff
    #alert_screen()
    name = rsp.split('*')[1]
    print("Emergency! Device " + str(name) + " has fallen!")

    # close connection
    client_socket.close()
    server_socket.close()


def register_device():
    global s
    msg = "Register*" + sessionId + "*" + deviceName
    s.send(msg.encode())


def deregister_device():
    global s
    msg = "Deregister*" + sessionId
    s.send(msg.encode())


def get_weather(pubIp):
    global s
    msg = "Weather*" + pubIp
    s.send(msg.encode())

    rsp = str(s.recv(1024).decode())
    return rsp


def send_emergency():
    global s
    connect_to_server()
    msg = "Emergency*" + sessionId
    s.send(msg.encode())
    close_connection()


def connect_to_server():
    global s
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((serverCfg["host"], serverCfg["port"]))


def close_connection():
    global s
    s.close()


connect_to_server()
register_device()
close_connection()

thread = threading.Thread(target=handle_emergency_messages, args=())
thread.start()

print("Type emergency to send message")
command = input()
if command == "emergency":
    send_emergency()
