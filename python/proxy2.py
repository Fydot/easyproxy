#!/usr/bin/env python
# coding: utf8
import socket
import select
import sys
import re


fileno_socket = {}
pair_socket = {}
send_fileno = {}


def parse_args(args_str):
    args_pattern = re.compile(r'\d+->[\w\'-.]+:\d+$')
    if not args_pattern.match(args_str):
        raise Exception('''I don't know what you say, give me (port->hostname:port)''')
    local_port = int(args_str.split('->')[0])
    remote_host = args_str.split('->')[1].split(':')[0]
    remote_port = int(args_str.split('->')[1].split(':')[1])
    return local_port, remote_host, remote_port


def bind(local_port, back_logs=5):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    serversocket.bind(('0.0.0.0', local_port))
    serversocket.listen(back_logs)
    serversocket.setblocking(0)
    return serversocket


def register(epoll_pool, sock, eventmask):
    epoll_pool.register(sock.fileno(), eventmask)


def connect(host, port):
    c_socket = socket.socket()
    c_socket.connect((host, port))
    return c_socket


def on_accept(server_socket, epoll_pool, remote_host, remote_port):
    connection, address = server_socket.accept()
    connection.setblocking(0)
    register(epoll_pool, connection, select.EPOLLIN | select.EPOLLOUT)
    service_socket = connect(remote_host, remote_port)
    register(epoll_pool, service_socket, select.EPOLLIN | select.EPOLLOUT)
    fileno_socket[connection.fileno()] = connection
    fileno_socket[service_socket.fileno()] = service_socket
    pair_socket[connection.fileno()] = service_socket.fileno()
    pair_socket[service_socket.fileno()] = connection.fileno()
    send_fileno[connection.fileno()] = ''
    send_fileno[service_socket.fileno()] = ''


def on_socket_closed(fileno, epoll_pool):
    fileno_socket[fileno].close()
    fileno_socket[pair_socket[fileno]].close()
    epoll_pool.unregister(fileno)
    epoll_pool.unregister(pair_socket[fileno])
    send_fileno.pop(fileno)
    send_fileno.pop(pair_socket[fileno])
    fileno_socket.pop(fileno)
    fileno_socket.pop(pair_socket[fileno])
    pair_socket.pop(pair_socket[fileno])
    pair_socket.pop(fileno)


def on_recv(fileno, epoll_pool):
    data = fileno_socket[fileno].recv(2 ** 12)
    if data is None:
        on_socket_closed(fileno, epoll_pool)
    else:
        send_fileno[pair_socket[fileno]] += data


def on_send(fileno):
    if len(send_fileno[fileno]) > 0:
        length = fileno_socket[fileno].send(send_fileno[fileno])
        send_fileno[fileno] = send_fileno[fileno][length:]


def main():
    local_port, remote_host, remote_port = parse_args(sys.argv[1])
    server_socket = bind(local_port)
    epoll_pool = select.epoll()
    register(epoll_pool, server_socket, select.EPOLLIN)

    while True:
        events = epoll_pool.poll(1)
        for fileno, event in events:
            if fileno == server_socket.fileno():
                on_accept(server_socket, epoll_pool, remote_host, remote_port)
            elif event & select.EPOLLIN:
                on_recv(fileno, epoll_pool)
            elif event & select.EPOLLOUT:
                on_send(fileno)


if __name__ == "__main__":
    main()
