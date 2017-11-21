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
                print("Server: Connection accepted, addr: " + str(addr) + " client no. " + str(next_client))        
                instance = threading.Thread( target=self.get_messages, args=(sock, next_client) )
#                print("instance created.")
                instance.start()
                
                next_client += 1
        finally:
            self.listen_sock.close()

    def get_messages( self, sock, id ):
        file_req_port = sock.recv( 4 ).decode()
        print("Server: Client " + str(id) + " sent back listen port " + file_req_port + ".")
        try:
            int(file_req_port)
        except ValueError:
            print("Server: The client did not send back a valid port number.")
            sock.close()
        self.client_socks[id] = [sock, '', '']
        self.client_socks[id][self.CLIENT_LISTEN_PORT_POS] = file_req_port

        print("Server: Thread opened @client " + str(id))
        name  = sock.recv( 4096 )
        ins = name.decode().split('\n', 1)
        client_name = ins[0]
        self.client_socks[id][self.CLIENT_NAME_POS] = client_name
    
        self.client_names[client_name] = id
        print( 'Server: Client@client ' + str(id) + ' entered their name as ' + client_name )
#        print( "Server: 1 client name is: " + client_name )
        if len(ins) > 1 and ins[1] != '':
            print( "Server: ins1: " + str(ins) )
            request = ins[1].encode()
        else:
            request = sock.recv( 4096 )
        while request:
#            print( "Server: 2 client name is: " + client_name )
            #the client will send a letter indicating the request type, followed by a ':' 
            #followed by the request text.
            #example: 'm:this is a text message' or 'f:file_name'
            message = request.decode()
            messages = message.split(':', 1)
            code = Server.get_request_type( messages[0] )
            if code == Server.BAD_REQUEST:
                continue
            if code == Server.MESSAGE_REQUEST:
#                print( "Server: client name is: " + self.client_socks[id][self.CLIENT_NAME_POS] )
#                print( "Server: 3 client name is: " + client_name )
#                print( "Server: 4")
#                print( "Server: messages[1] is " + messages[1], end='' )
                print( "Server: " + self.client_socks[id][self.CLIENT_NAME_POS] + ': ' + messages[1], end='' )
                self.broadcast_msg( id, messages[1] )
            if code == Server.FILE_REQUEST:
                rq = messages[1].split(':', 1)
                owner = rq[0]
                file_name = rq[1]
                print('Server: ' + self.client_socks[id][self.CLIENT_NAME_POS] + ' requests to get file ' + file_name + ' from ' + owner )
                self.handle_file_request( sock, owner )
            request = sock.recv( 4096 )
        sock.close()
        self.client_socks.pop(id)
        print('Server: ' +  client_name + ' disconnected and the socket was successfully closed.' )
        
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
            print('Server: Error sending back port number for p2p connection.')

    def broadcast_msg( self, client_id, message ):
        line_to_send = self.client_socks[client_id][self.CLIENT_NAME_POS] + ': ' + message
        print("Server: line_to_send = " + line_to_send)
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
            print('Server: Sending message to ' + to_name + ' from ' + from_name + ' failed.')


def main():
    port, host = parse_opts(argv)
    s = Server(port)
    s.get_new_client()

main()
