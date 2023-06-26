import socket
import psutil

def clear_port(port):
    """Clear the specified port by terminating the process using it."""
    for proc in psutil.process_iter():
        for con in proc.connections():
            if con.laddr.port == port:
                print(f"Terminating process {proc.pid} using port {port}")
                proc.terminate()

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def debugPort(port):
    if is_port_in_use(port):
        print(f"Port {port} is already in use.")
        clear_port(port)
    else:
        print(f"Port {port} is free.")