'''
Name: Python Client Handler
Author: SPC Montgomery, Amir
Date: 20240829

Objective: Handles the calls to the C acft_client.py
'''

from ctypes import *
client = windll.LoadLibrary('./libacft_client.dll') # import the ctypes module and load the custom .dll, wowee

def connect_to_server(): # create and return the socket
    client.init_connect.restype = c_int
    return client.init_connect()

def send_to_server(filename: str, socket: int, savename: str):
    #f = open(filename, "r")
    #client.send_file(filename, socket)
    client.send_file.argtypes = c_char_p, c_int, c_char_p
    client.send_file(filename, socket, savename)
    #f.close()

def disconnect_server(socket):
    client.close_connection.argtypes = c_int,
    client.close_connection(socket)
'''
    connect to server 
    send file to server =

    open file with open(file, mode)
    use file.fileno() to get file descriptor
    FILE *fdopen(file.fileno(), mode)

    FILE *fp;
    fp = fdopen(file.fileno(), mode)
    client.send_file(fp, sock)


    Issue will be separate buffering for two objects opened on the same file descriptor.

    Flush often, os.sync to ensure all buffers are synchronized with storage devices
'''