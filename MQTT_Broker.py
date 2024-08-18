import socket
import sys
from threading import Thread
import MQTT_control_packets.RETRANSMET
import MQTT_decoder
import MQTT_database
import MQTT_persistant_sessions.operations
from MQTT_database import read_database,session_get_topic, session_delete
from MQTT_packet_handler import packet_router
import time
from MQTT_control_packets import PUBLISH, PUBACK
from MQTT_persistant_sessions.operations import add_value_to_topic, search_client_id
import sqlite3
import hashlib
import signal
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()


#mqtt broker address
HOST = "127.0.0.1"
PORT = 1883

#store the (client_ID,client_sock).
connected_clients = []
#store the client_ID.
con_cli=[]
# Assuming packet_ids is a set that stores all active packet identifiers.
packet_ids = set()
#NONACKED packets's information (packet_id,value,topic,client_socket,time_stamp).
non_acked_ids=[]
def signal_handler(signal, frame):
    print('The Broker went to sleep...!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

KEEP_ALIVE_INTERVAL=15 #in sec
def check_non_acked_packet_ids():
    while True:
        for idx, info in enumerate(non_acked_ids):
            packet_id, value, topic, client_socket, timestamp = info
            if time.time() - timestamp >= KEEP_ALIVE_INTERVAL:  # we check if the packet still with no PUBACK for KEEP_ALIVE_INTERVAL, if so, a new packet with the same id and DUP flag raised will be prepared(encoded) for resending it.
                packet = MQTT_control_packets.RETRANSMET.encode(topic, value, packet_id)
                client_socket.send(packet)
                non_acked_ids[idx] = (packet_id, value, topic, client_socket, time.time())
        time.sleep(1)
def main():
    # Initialize database.
    MQTT_database.initialize_database()
    MQTT_persistant_sessions.operations.initialize_database()
    # Create dummy session and topic.
    #MQTT_database.session_create("test1")
    MQTT_database.topic_create('Temperature')
    MQTT_database.topic_create('Humidity')
    #for delete all information stored in ds.json and db_persistant_sessions run the script in the file named Rest DBs.py.
    Thread(target=check_non_acked_packet_ids).start()
    start_broker()


def start_broker():

    # Create server socket.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind socket to port.
    try:
        server_socket.bind((HOST, PORT))
        print(f"Binding server socket to host: {HOST} and port: {PORT}")
        print(Fore.GREEN + "Broker is running....." + Style.RESET_ALL)

    except:
        print(f"Bind failed. \nError: {str(sys.exc_info())}")
        sys.exit()

    # Enable passive listening sockets.
    server_socket.listen(5)

    # Periodically jump out of accept waiting process to receive keyboard interrupt commnad.
    server_socket.settimeout(0.5)

    while True:

        client_socket = None

        try:
            # Wait and accept incoming connection
            (client_socket, address) = server_socket.accept()
            ip, port = str(address[0]), str(address[1])
            print(f"Connection from {ip}:{port} has been established.")

            try:
                Thread(target=client_thread, args=(client_socket, ip, port)).start()
                print(f"Client thread for {ip}:{port} has been created.")
            except:
                print(f"Client thread for {ip}:{port} did not create")
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            sys.exit()


def client_thread(client_socket, ip, port):
    global connected_clients
    global con_cli
    global non_acked_ids
    client_ID = ""

    while True:

        try:
            # Listen to incoming data
            try:
                data = client_socket.recv(1024)
            except:
                print(f'Client ({client_ID}) unexpected disconnect.')
                connected_clients = [client for client in connected_clients if client_ID not in client]
                sys.exit()
            if not data:
                time.sleep(0.5)
                print(f"Client ({client_ID}) went to sleep")
                break

            # print(f"Incomming packet: {data}")

            # Decode incoming packet
            incoming_packet = MQTT_decoder.decode(data)
            # Authentication procces
            if incoming_packet.get("Packet type") == "CONNECT":
                if incoming_packet.get("Username flag")==False or incoming_packet.get("Password flag")==False:
                    message = 'Please provide the full credincitals!'
                    print(message)
                    client_socket.send(message.encode())
                    client_socket.close()
                    return
                else:
                    username=incoming_packet.get("Username")
                    raw_password=incoming_packet.get("Password").encode()
                    password=hashlib.sha256(raw_password).hexdigest()
                    con=sqlite3.connect("userdata.db")
                    cur=con.cursor()
                    cur.execute("SELECT * FROM userdata WHERE username=? AND password=?",(username,password))
                    if cur.fetchall():
                        print("Authentication done!")
                        client_ID = incoming_packet.get("Payload")
                        connected_clients.append((client_ID, client_socket))
                        con_cli.append(client_ID)
                    else:
                        message="Wrong credincitals!"
                        print(message)
                        client_socket.send(message.encode())
                        client_socket.close()
                        return

            if incoming_packet.get("Packet type") == "DISCONNECT":
                connected_clients = [client for client in connected_clients if client_ID not in client]
                con_cli=[client for client in con_cli if client!=client_ID]
                # search in the persistance session data base, while there are no entry for the client, if so the client session will be deleted upon disconnection.
                if search_client_id(client_ID)==False:
                    session_delete(client_ID)  # Destroy the session because the session clean flag is True.
                print(f"connected_clients:{con_cli}")

            # check if the packet type is PUBACK=0100=4, if so, print the puback source and the message id of the QOS 1 message that has been sent.
            if incoming_packet.get("Packet type") == 4:
                print(f"PUBACK received from the client:{client_ID} for the message with id:{incoming_packet.get('Packet identifier')}")
                non_acked_ids=[id for id in non_acked_ids if incoming_packet.get('Packet identifier') not in id ]
                print(f"nonacked packets:{non_acked_ids}")
            else:
                # prepare the outgoing packt(response) to be sent back to the client
                outgoing_packet = packet_router.route_packet(incoming_packet, client_ID)
            # print(f'Outgoing packet: {outgoing_packet}')


            # Send outgoing packet
            if incoming_packet.get("Packet type") == "PUBLISH":
                # check if the QOS is 1 to send the PUBACK packet:
                if incoming_packet.get('Flags')[2] == '1':
                    puback_packect=PUBACK.encode(incoming_packet.get("Packet identifier"))
                    client_socket.send(puback_packect)
                    print(f"PUBACK sent for QOS 1 message...!")
                    #prepare the QOS 1 packet with unquie identifier for each sent packet
                    for client in connected_clients:
                        client_ID, client_socket = client
                        if incoming_packet.get("Topic") in session_get_topic(client_ID):
                            outgoingQOS1_packet,packt_id=outgoing_packet
                            client_socket.send(outgoingQOS1_packet)
                            non_acked_ids.append((packt_id,incoming_packet.get("Payload"),incoming_packet.get("Topic"),client_socket,time.time()))
                            #encode another QOS 1 packet to be sent.
                            outgoing_packet = PUBLISH.encode_QOS1(incoming_packet.get("Topic"), incoming_packet.get("Payload"))
                    print(f"nonacked packets:{non_acked_ids}")
                else:
                    send_to_all_connected(outgoing_packet,incoming_packet.get('Topic'))
                # print(f"connected_clients:{con_cli}")
                # check if there are any disconnected clients subsecribed in the topic that the message published to, if it is then the message will be stored until the client reconnect.
                database=MQTT_database.read_database()
                client_lise = database.get("Clients")
                for client in client_lise:
                    for client, details in client.items():
                        if incoming_packet.get("Topic") in session_get_topic(client) and client not in con_cli:
                            add_value_to_topic(client, incoming_packet.get("Topic"), incoming_packet.get("Payload"))
                            print(f"Value added for client {client} to topic {incoming_packet.get('Topic')}:{MQTT_persistant_sessions.operations.read_database()} ")

            else:
                if incoming_packet.get("Packet type")!=4:
                    client_socket.send(outgoing_packet)
                # we check if the newlly connected client is already have a session stored, if so, then we iterat over the stored values and send them to the client.
                if incoming_packet.get("Packet type") == "CONNECT":
                    if search_client_id(client_ID): #check if the client has stored session
                        target_client_id=client_ID
                        persistant_sessions=MQTT_persistant_sessions.operations.read_database()
                        persistant_sessions_list=persistant_sessions["Sessions"]
                        for session in persistant_sessions_list:
                            if target_client_id in session:
                                client_info = session[target_client_id]
                                for sub_type, values in client_info["Subscriptions"].items():
                                    for value in values[:]:
                                        outgoing_packet=PUBLISH.encode(sub_type,value)
                                        values.remove(value)
                                        client_socket.send(outgoing_packet)
                        persistant_sessions.update({"Sessions": persistant_sessions_list})
                        MQTT_persistant_sessions.operations.write_database(persistant_sessions)
            #send the value of the topic to the client who just subsecribed
            if incoming_packet.get("Packet type") == "SUBSCRIBE":
                topic = incoming_packet.get('Topics')[0]
                topic = next(iter(topic))
                if topic in MQTT_database.session_get_topic(client_ID):
                    if MQTT_database.topic_exists(topic):
                        value = MQTT_database.topic_get_value(topic)
                        outgoing_packet = PUBLISH.encode(topic, value,)
                        client_socket.send(outgoing_packet)


        except KeyboardInterrupt:
            client_socket.close()
            sys.exit()

# send the published message to all client subsecribed to the topic that has been published to
def send_to_all_connected(packet: bytes,topic):
    global connected_clients
    for client in connected_clients:
        client_ID,client_socket=client
        if topic in session_get_topic(client_ID):
            client_socket.send(packet)


if __name__ == "__main__":
    main()
