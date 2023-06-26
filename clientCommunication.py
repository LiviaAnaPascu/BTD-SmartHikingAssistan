import socket


serverCfg = {
    # add correct server address here
    "host": "<XXX.XXX.XXX.XXX>",
    "port": 420
}

sessionId = "PAX_ROMANA"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# start like this:
# thread = threading.Thread(target=handle_emergency_messages, args=())
# thread.start()
def handle_emergency_messages():
    host = 'localhost'
    port = 421

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    client_socket, addr = server_socket.accept()
    print(f"Accepted connection from {addr[0]}:{addr[1]}")

    # Trigger buzzer here and show UI stuff

    # close connection
    client_socket.close()
    server_socket.close()


def register_device():
    msg = "Register#" + sessionId
    s.send(msg.encode())


def deregister_device():
    msg = "Deregister#" + sessionId
    s.send(msg.encode())


def get_uv_index():
    msg = "Weather"
    s.send(msg.encode())

    rsp = str(s.recv(1024).decode())
    return rsp


def send_emergency():
    msg = "Emergency"
    s.send(msg.encode())


def connect_to_server():
    s.connect((serverCfg["host"], serverCfg["port"]))


def close_connection():
    s.close()
