#include <stdio.h>
#include <ctype.h>
#include <errno.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <netdb.h>
#include <string.h>

int proxy_port, server_port;
struct sockaddr_in server_host;
extern int errno;

void read_args(int argc, char* args[]) {
  struct hostent *hostp;
  struct servent *servp;
  unsigned long inaddr;
  struct {
    char proxy_port[32];
    char service_host[64];
    char service_port[32];
  } pargs;
  strcpy(pargs.proxy_port, args[1]);
  strcpy(pargs.service_host, args[2]);
  strcpy(pargs.service_port, args[3]);
  int i;
  for (i = 0; i < strlen(pargs.proxy_port); ++i) {
    if (!isdigit(pargs.proxy_port[i])) {
      break;
    }
  }
  if (strlen(pargs.proxy_port) == i) {
    proxy_port = htons(atoi(pargs.proxy_port));
  }
  else {
    printf("Invalid Args!\n");
    return;
  }
  bzero(&server_host, sizeof(server_host));
  server_host.sin_family = AF_INET;
  if ((inaddr = inet_addr(pargs.service_host)) != INADDR_NONE)
    bcopy(&inaddr,&server_host.sin_addr,sizeof(inaddr));
  else if ((hostp = gethostbyname(pargs.service_host)) != NULL)
    bcopy(hostp->h_addr,&server_host.sin_addr,hostp->h_length);
  else {
    printf("%s: Unknown Host\n",pargs.service_host);
    return;
  }
  if ((servp = getservbyname(pargs.service_port, "tcp")) != NULL)
    server_host.sin_port = servp->s_port;
  else if (atoi(pargs.service_port) > 0) 
    server_host.sin_port = htons(atoi(pargs.service_port)); 
  else { 
    printf("%s: Invalid Service Name or Port\n", pargs.service_port);
    return;
  } 
}


void onproxy (int usersockfd) {
  int isosockfd;
  fd_set rdfdset;
  int connstat;
  int iolen;
  char buf[2048];
  if ((isosockfd = socket(AF_INET,SOCK_STREAM,0)) < 0) puts("failed to create socket to host");
  connstat = connect(isosockfd,(struct sockaddr *) &server_host, sizeof(server_host));
  switch (connstat) {
    case 0:
      break;
    case ENETUNREACH:
    case ETIMEDOUT:
    case ECONNREFUSED:
      strcat(buf,"\r\n");
      write(usersockfd,buf,strlen(buf));
      close(usersockfd);
      return;
      break;
    default:
      puts("failed to connect to host");
  }
  while (1) {
    FD_ZERO(&rdfdset);
    FD_SET(usersockfd,&rdfdset);
    FD_SET(isosockfd,&rdfdset);
    if (select(FD_SETSIZE,&rdfdset,NULL,NULL,NULL) < 0) {
      puts("select failed");
    }
    if (FD_ISSET(usersockfd,&rdfdset)) {
      if ((iolen = read(usersockfd,buf,sizeof(buf))) <= 0) break;
      write(isosockfd,buf,iolen);
    }
    if (FD_ISSET(isosockfd,&rdfdset)) { 
      if ((iolen = read(isosockfd,buf,sizeof(buf))) <= 0) break;
      write(usersockfd,buf,iolen); 
    } 
  }
  close(isosockfd); 
}


int main(int argc, char* args[]) {
  struct sockaddr_in servaddr, cliaddr;
  int clilen;
  int childpid;
  int sockfd, newsockfd;
  read_args(argc, args);
  bzero((char *) &servaddr, sizeof(servaddr)); 
  servaddr.sin_family = AF_INET; 
  servaddr.sin_addr.s_addr = htonl(INADDR_ANY); 
  servaddr.sin_port = proxy_port; 
  if ((sockfd = socket(AF_INET,SOCK_STREAM,0)) < 0) { 
    fputs("Failed to create server socket\r\n",stderr); 
    return 1;
  } 
  if (bind(sockfd,(struct sockaddr_in *) &servaddr,sizeof(servaddr)) < 0) { 
    fputs("faild to bind server socket to specified port\r\n",stderr); 
    return 1;
  } 
  listen(sockfd,5); 
  while (1) {
    clilen = sizeof(cliaddr); 
    newsockfd = accept(sockfd, (struct sockaddr_in *) &cliaddr, &clilen); 
    if (newsockfd < 0 && errno == EINTR) {
      continue;
    }
    else if (newsockfd < 0) {
      puts("failed to accept connection");
    }
    if ((childpid = fork()) == 0) { 
      close(sockfd); 
      onproxy(newsockfd); 
      return 1;
    } 
  }
  return 0;
}
