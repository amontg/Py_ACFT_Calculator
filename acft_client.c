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
#include <stdint.h>

#define SIZE 1024

typedef struct{
    long length;
    char *savename;
} message_header;

message_header split_header(char *header){
    message_header headerstruct;
    const char s[2] = "/";
    
    headerstruct.length = strtol(strtok(header, s), NULL, 10);
    //printf("Length: %ld\n", headerstruct.length);
    headerstruct.savename = strtok(NULL, s); // remainder of header
    //printf("Name: %s\n", headerstruct.savename);
    //printf("Remainder: %s\n", header);

    return headerstruct;
}

int send_all(int s, char *data, char *header){ // send_all(socket, data, bytes in data)
    /* first send the length of message */
    send(s, header, SIZE, 0);

    message_header headerstruct;
    headerstruct = split_header(header);
    
    /* then send the message */
    int total = 0;          // how many bytes sent
    int n;            

    while (total < headerstruct.length){
        n = send(s, data+total, headerstruct.length-total, 0); // char byte size 1
        if (n == -1 || n == 0) {
            break;
        }

        total += n;
    }

    if (n < 0) {
        printf("Send file error: %d\n", WSAGetLastError());
    }

    printf("Sent: %d\n", total);
    return n==-1?-1:0;      // -1 fail, 0 success
}

void send_file(char* fname, int socket, char *savename){
    /* do the file opening stuff */
    FILE *fp;
    fp = fopen(fname, "rb");

    if (fp == NULL) {
        printf("Error opening file: %d\n", WSAGetLastError());
        exit(1);
    } else {
        fseek(fp, 0, SEEK_END);                         // fseek eof, ftell pos, rewind.
        long nbytes = ftell(fp);                        // number of bytes to send **
        rewind(fp);                                     // cur back to beginning
        char *data = malloc(nbytes);                    // the actual data to send **
        size_t n = sizeof(*data) / sizeof(data[0]);

        fread(data, nbytes, n, fp);
        
        char header[SIZE];
        snprintf(header, sizeof(header), "%ld/%s", nbytes, savename);   // size/savename
        //printf(header);                                               // positive check
        
        int e = send_all(socket, data, header);
        if (e < 0){
            printf("Send All Error: %d\n", WSAGetLastError());
        }

        fclose(fp);
        free(data);
        //memset(data, '\0', nbytes);
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
