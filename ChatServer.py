"""
CSC376 Assignment 3 - Chat
Server
Michael Skiles
"""

import threading
import sys
import os
import socket

def usage( script_name ):
    print( 'Usage: python3 ' + script_name + ' <port number>' )

argv = sys.argv
argc = len( sys.argv )
if argc != 2:
    usage( sys.argv[0] )
    os.exit(1)

def parse_opts( argv ):
    port = ''
    host = 'localhost'

    try:
        port = argv[1]

        # make sure the port argument is an int, throws ValueError
        int(port)
    except (IndexError, ValueError):
        print("The port number was either not specified, or not an integer")
        sys.exit()

    return (port, host)

class Server:

    #The client_socks dict is a dictionary with an client id int
    #as the key, followed by a list in form [socket, thread instance, client username]
    MESSAGE_REQUEST = 0
    FILE_REQUEST = 1
    BAD_REQUEST = -1

    SOCKET_POS = 0
    CLIENT_NAME_POS = 1
    CLIENT_LISTEN_PORT_POS = 2

    client_socks = {}
    client_names = {}
    listen_sock = None

    def __init__( self, port ):
        self.port = port
        self.open_listener( self.port )

    def open_listener( self, port ):
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind( ('localhost', int(port)) )
        self.listen_sock.listen(5)

    def get_new_client( self ):
        next_client = 0
        try:
            while True:
                sock, addr = self.listen_sock.accept()
                print("Connection accepted, addr: " + str(addr) + " client no. " + str(next_client))
                file_req_port = sock.recv( 4 ).decode()
                print("Client sent back listen port " + file_req_port + ".")
                try:
                    int(file_req_port)
                except ValueError:
                    print("The client did not send back a valid port number.")
                    sock.close()
                self.client_socks[next_client] = [sock, '', '']
                self.client_socks[next_client][self.CLIENT_LISTEN_PORT_POS] = file_req_port

                instance = threading.Thread( target=self.get_messages, args=(sock, next_client) )
#                print("instance created.")
                instance.start()
                
                next_client += 1
        finally:
            self.listen_sock.close()

    def get_messages( self, sock, id ):
        print("Thread opened @client " + str(id))
        message = sock.recv( 4096 )
        client_name = message.decode().strip()
        self.client_socks[id][self.CLIENT_NAME_POS] = client_name
        self.client_names[client_name] = id
        print( 'Client@client ' + str(id) + ' entered their name as ' + client_name )
        request = sock.recv( 4096 )
        while request:
            #the client will send a letter indicating the request type, followed by a ':' 
            #followed by the request text.
            #example: 'm:this is a text message' or 'f:file_name'
            request = request.decode()
            message = request.split(':', 1)
            code = Server.get_request_type( message[0] )
            if code == Server.BAD_REQUEST:
                continue
            if code == Server.MESSAGE_REQUEST:
                print( client_name + ': ' + message[1], end='' )
                self.broadcast_msg( id, message[1] )
            if code == Server.FILE_REQUEST:
                message = message[1].split(':', 1)
                owner = message[0]
                file_name = message[1]
                print( client_name + ' requests to get file ' + file_name + ' from ' + owner )
                self.handle_file_request( sock, owner )
            request = sock.recv( 4096 )
        sock.close()
        self.client_socks.pop(id)
        print( client_name + ' disconnected and the socket was successfully closed.' )
        
    def get_request_type( code ):
        #print(code)
        if code == 'm':
            return Server.MESSAGE_REQUEST
        if code == 'f':
            return Server.FILE_REQUEST
        else:
            return Server.BAD_REQUEST

    def handle_file_request( self, sock, owner ):
        owner_id = self.client_names[owner]
        port = self.client_socks[owner_id][self.CLIENT_LISTEN_PORT_POS]
        try:
            sock.send( port.encode() )
        except:
            print('Error sending back port number for p2p connection.')

    def broadcast_msg( self, client_id, message ):
        line_to_send = self.client_socks[client_id][self.CLIENT_NAME_POS] + ': ' + message
        for c in self.client_socks:
            if c != client_id:
                sock = self.client_socks[c][self.SOCKET_POS]
                send_instance = threading.Thread( target=self.send_msg, args=(sock, c, client_id, line_to_send) )
                send_instance.start()

    def send_msg( self, sock, id_to, id_from, message ):
        try:
            sock.send( message.encode() )
        except:
            to_name = self.client_socks[id_to][CLIENT_NAME_POS]
            from_name = self.client_socks[id_from][CLIENT_NAME_POS]
            print('Sending message to ' + to_name + ' from ' + from_name + ' failed.')


def main():
    port, host = parse_opts(argv)
    s = Server(port)
    s.get_new_client()

main()
