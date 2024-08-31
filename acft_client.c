/*
Name: ACFT Calculator Client
Author: SPC Montgomery, Amir
Date: 20230829

Objective: Create a client to send and receive databases from a server.
*/

#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>
#include <wsipv6ok.h>

#define SIZE 1024

void send_file(char* fname, int socket){
    // do the file opening stuff
    FILE *fp;
    fp = fopen(fname, "rb");

    if (fp == NULL) {
        printf("Error opening file: %d\n", WSAGetLastError());
        exit(1);
    } else {
        fseek(fp, 0, SEEK_END); // fseek eof, ftell pos, rewind.
        long nbytes = ftell(fp);
        rewind(fp);
        char data[nbytes];
        size_t n = sizeof(data) / sizeof(data[0]);

        //memset(data, '\0', SIZE);
        fread(data, nbytes, n, fp);

        int e = send(socket, data, nbytes, 0); // reset connect when = send(socket, data, nbytes/sizeof(data), 0)
        if (e < 0){
            printf("Error sending file: %d\n", WSAGetLastError());
            exit(1);
        }

        fclose(fp);
        memset(data, '\0', SIZE);
    }
}

int init_connect(){ // initializes the connection and returns the socket to be used
    
    // Start Windows Socket Functions
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    // IP Addressing & Sockets
    char *ip = "192.168.1.153";
    int port = 3333;

    int sock;
    struct sockaddr_in addr;
    socklen_t addr_size;
    char buffer[1024];
    int n;

    // Fill in Addressing to addr struct
    memset(&addr, '\0', sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = inet_addr(ip);

    // create socket and connect
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET){
        printf("There is an error with your socket: %d\n", WSAGetLastError());
        exit(1);
    }
    
    int connection_status = connect(sock, (struct sockaddr*)&addr, sizeof(addr));
    if (connection_status == SOCKET_ERROR){
        printf("There is an error with connection: %d\n", WSAGetLastError());
        exit(1);
    }

    return sock;
}

void close_connection(int sock){
    closesocket(sock);
    WSACleanup();
}
