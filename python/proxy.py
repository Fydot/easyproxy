#!/usr/bin/env python
# coding: utf8
import socket
import select


connections = {}
client_server = {}


def accept(serversocket):
    connection, address = serversocket.accept()
    connection.setblocking(0)
    return connection


def connect(host, port):
    c_socket = socket.socket()
    c_socket.connect((host, port))
    return c_socket


def main():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    serversocket.bind(('0.0.0.0', 12580))
    serversocket.listen(5)
    serversocket.setblocking(0)

    epoll = select.epoll()
    epoll.register(serversocket.fileno(), select.EPOLLIN)

    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == serversocket.fileno():
                connection = accept(serversocket)
                epoll.register(connection.fileno(), select.EPOLLIN)
                connections[connection.fileno()] = connection
                c_socket = connect('localhost', 10010)
                client_server[connection.fileno()] = c_socket.fileno()
                client_server[c_socket.fileno()] = connection.fileno()
            elif event & select.EPOLLIN:
                request = connections[fileno].recv(4096)
                connections[client_server[fileno]].sendall(request)

if __name__ == "__main__":
    main()
