#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h> // Unix uses <arpa/inet.h, Windows uses <Winsock2.h>. Server will be Unix.
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

int rec_all(int s){ // rec_all(socket, buffer)
    /*  first packet should be 1024 with size of message */
    char header[SIZE];
    int totalread = 0;
    int e;

    while (totalread < SIZE){
        e = read(s, ((char *)header)+totalread, SIZE-totalread);
        if (e == -1){
            break;
        }

        totalread += e;
    }

    if (e < 0){
        perror("Header error");
        exit(1);
    }

    /* split the header up */
    message_header headerstruct;
    headerstruct = split_header(header);

    /* then receive all of the messages */
    char *data = malloc(headerstruct.length);
    int total = 0;
    int n;

    memset(data, '\0', headerstruct.length);

    /* fwrite as we read new bits */
    FILE *fp;
    char *filename = headerstruct.savename;
    
    fp = fopen(filename, "wb");     // truncate and write binary

    while (total < headerstruct.length) {
        n = read(s, data+total, headerstruct.length-total);
        if (n == -1 || n == 0) {
            break;
        }
        
        fwrite(data+total, n, 1, fp);
        fflush(fp);
        total += n;
    }

    if (n < 0){
        perror("File read error");
        exit(1);
    }

    free(data);
    fclose(fp);

    printf("Received & Wrote: %d\n", total);
    return n==-1?-1:0;
}

int main(){
    //char *ip = "127.0.0.1"; // on this machine, using the following port UNUSED
    int port = 3333;

    int server_sock, client_sock;
    struct sockaddr_in server_addr, client_addr; // basic structure for handling internet addresses: https://www.gta.ufrj.br/ensino/eel878/sockets/sockaddr_inman.html
    socklen_t addr_size; // size of address
    char buffer[1024];
    int n;

    server_sock = socket(AF_INET, SOCK_STREAM, 0); 
    /*      socket(domain, type, protocol)
        domain = address family, AF_INET = IPv4
        type = socket type (SOCK_STREAM = TCP, SOCK_DGRAM = UDP, SOCK_SEQPACKET = TCP for records(?))
        protocol = the protocol being used, 0 is default for address family
    */

    // setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &sockoptval, sizeof(int));

    if (server_sock < 0){
        perror("There is an error with your socket");
        exit(1);
    }
    printf("TCP Server Socket created. \n");

    memset(&server_addr, '\0', sizeof(server_addr)); 
    /*      memset(void *str, int c, size_t n). Fill memory with value
        str pointer to memory block (& is reference)
        c is parameter to pass into memory block
        n is number of bytes to be set

        = fill memory block server_addr with NUL characters meant to be replaced, for only as many bytes as the server_addr is
    */
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port); // htons for big/little endian-ness stuff: https://www.gta.ufrj.br/ensino/eel878/sockets/htonsman.html
    //server_addr.sin_addr.s_addr = inet_addr(ip); // if we specify an IP address, it'll refuse any IP that doesn't match

    n = bind(server_sock, (struct sockaddr*)&server_addr, sizeof(server_addr));
    /*      bind(int socket, const struct sockaddr *address, socklen_t address_len)
        socket is the socket to be bound
        address is a sockaddr struct containing the address to be bound
        address_len specifies length of sockaddr struct given in address argument

        = bind the server_addr struct address of the sizeof(server_addr struct)
    */
    if (n < 0){
        perror("There is an error with the socket binding");
        exit(1);
    }
    printf("Bound to port %d. \n", port);

    listen(server_sock, 5); // listen on given socket, backlog is used to limit outstanding connections in socket's listening queue
    printf("Listening... \n");

    while(1){
        addr_size = sizeof(client_addr);
        client_sock = accept(server_sock, (struct sockaddr*)&client_addr, &addr_size); // accepting the client connections
        printf("We have a client connected! \n");

        // bzero(buffer, 1024); // bzero(void *s, size_t n) = place n zero-valued bytes in the area pointed to by s. BZERO IS OBSOLETE, USE MEMSET
        //memset(buffer, '\0', 1024);
        // recv(client_sock, buffer, sizeof(buffer), 0); // receiving
        // printf("Client: %s \n", buffer);

        printf("Waiting for the file...\n");
        rec_all(client_sock);

        memset(buffer, '\0', 1024); // replace 1024bytes in buffer with NUL
        strcpy(buffer, "We have the file. Thank you.\n");
        printf("Server: %s \n", buffer);
        send(client_sock, buffer, strlen(buffer), 0); // sending

        close(client_sock); // closing
        printf("Client has disconnected. \n\n");
    }

    return 0;
}