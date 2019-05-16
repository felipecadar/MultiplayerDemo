import socket

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def read_command(str):
    mycomm = str.split(",")
    # print(mycomm)
    return list(map(float, mycomm))

def set_command(comm):
    return ",".join(map(str, comm))

class BattleProtocol:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = get_ip()
        self.port = 5555
        self.addr = (self.server, self.port)
        while not self.connect():
            pass
        # self.command = self.receive()

    # def getCommand(self):
    #     return self.command

    def connect(self):
        try:
            self.client.connect(self.addr)
            # return self.client.recv(2048).decode()
            return True
        except:
            print("Fail to Connect " + self.addr[0] + " " + str(self.addr[1]))
            return False

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            # return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)

    def receive(self):
        try:
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)
