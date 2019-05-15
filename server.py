import sys
import socket
from _thread import *
from protocol import read_command, set_command, get_ip

def threaded_client(conn, player):
    global init_game
    global cmds
    global currentPlayer

    while True:
        ans = conn.recv(2048).decode()
        if ans == "init" or init_game == 1:
            conn.sendall(str.encode("play"))
            break
        else:
            conn.sendall(str.encode(str(currentPlayer)))



    #primeiro a propria posicao de inicio
    cmds[player][-1] = player
    conn.send(str.encode(set_command(cmds[player])))

    while True:
        try:
            command = read_command(conn.recv(2048).decode())
            if not command:
                print("Fail to get data")
                break
            else:
                cmds[player] = command

            #manda a posição de cada inimigo ativo
            activeplayers = [cmds[i] for i in range(len(cmds)) if cmds[i][4] >= 0 and i != player]
            if len(activeplayers) > 0: 
                full_cmd = ";".join(map(set_command, activeplayers))
            else:
                full_cmd = "none"

            conn.sendall(str.encode(full_cmd))

        except socket.error as e:
            # print(e)
            break

    print("Lost connection")
    conn.close()
    currentPlayer -= 1

server = get_ip()
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(4)
print("Waiting for a connection, Server Started")

cmds = [[10,10,0,0,-1],[10,50,0,0,-1],[50,10,0,0,-1],[50,50,0,0,-1]]
init_game = 0

currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)

    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer += 1