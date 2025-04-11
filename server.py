import sys
from socket import *

if len(sys.argv) != 2:
    print('Usage: python server.py <port>')
    sys.exit(1)

serverPort = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

print(f'The server is ready and listening on port {serverPort}')
while True:
    try:
        connectionSocket, addr = serverSocket.accept()
        print(f'Connection from {addr} has been established.')

        print('Waiting for a message from the client...')
        sentence = connectionSocket.recv(1024).decode()
        print(f'Received message: {sentence}')

        capitalizedSentence = "Nice! It works!" #sentence.upper()
        connectionSocket.send(capitalizedSentence.encode())
        connectionSocket.close()
    except Exception as e:
        print(f'An error occurred: {e}')