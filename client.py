import sys
from socket import *

serverName = 'localhost'
serverPort = 14124

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.connect((serverName, serverPort))

sentence = input('Input lowercase sentence: ')
clientSocket.send(sentence.encode())
modifiedSentence = clientSocket.recv(1024)

print('From Server:', modifiedSentence[0].decode())
clientSocket.close()

