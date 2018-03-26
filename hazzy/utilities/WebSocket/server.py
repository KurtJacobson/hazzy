#!/usr/bin/env python

import json
import linuxcnc
from websocket_server import WebsocketServer

from google.protobuf.json_format import MessageToJson
from linuxcnc_pb2 import Joint

command = linuxcnc.command()


# Called for every client connecting (after handshake)
def new_client(client, server):
    client_id = client['id']
    client_address = client['address']
    print("New client connected and was given id {}".format(client_id))
    server.send_message(client, "This client's ID is {0} and has address {1}".format(client_id, client_address))
    server.send_message_to_all("Hey all, a new client has joined us")




# Called for every client disconnecting
def client_left(client, server):
    print("Client(%d) disconnected" % client['id'])


# Called when a client sends a message
def message_received(client, server, message):
    parsed_msg = json.loads(message)
    print json.dumps(parsed_msg, indent=4, sort_keys=True)

    if parsed_msg.get('type') == 'command':
        process_command(client, parsed_msg)

    elif parsed_msg.get('type') == 'joint':
        process_joint(client)


def process_command(client, data):
    command_type = data.get('command_type')
    if hasattr(command, command_type):
        try:
            cmd = getattr(command, command_type)
            text = data.get('command_text')
            command.mode(linuxcnc.MODE_MDI)
            cmd(text)
        except Exception as e:
            server.send_message(client, "ERROR: {}".format(e))


def process_joint(client):
    # wild test just here

    s = linuxcnc.stat()
    s.poll()

    for joint in s.joint:
        for key, value in joint.items():
            # print("linuxcnc - {},{}".format(key, value))
            setattr(Joint, key, value)
            print("protobuf - {},{}".format(key, getattr(Joint, key)))

    joint = Joint()
    print(type(joint))

    # server.send_message(client, joint.SerializeToString())

    # end of the wild test


PORT = 9001
server = WebsocketServer(PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server.run_forever()
