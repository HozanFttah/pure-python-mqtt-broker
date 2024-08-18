import MQTT_persistant_sessions.operations
from MQTT_control_packets import CONNACK
import MQTT_database
from MQTT_persistant_sessions.operations import  add_persistant_session, search_client_id, delete_persistant_session
def handle(incoming_packet: dict, client_ID: str):

    # Get protocol name
    protocol_name = incoming_packet.get('Protocol name')
    if protocol_name != 'MQTT4':
        outgoing_packet = CONNACK.encode(session_present=False, return_code=1)
        return outgoing_packet

    # Get client ID
    client_id = incoming_packet.get('Payload').split(' ',1)[0]

    # Get clean session
    clean_session = incoming_packet.get('Clean Session flag')

    # Clean session == True
    if clean_session:
        # If we have old session
        if MQTT_database.session_exists(client_id) and search_client_id(client_id):
            MQTT_database.session_delete(client_id) # Delete any old session
            delete_persistant_session(client_id)
        MQTT_database.session_create(client_id) # Create new session
        outgoing_packet = CONNACK.encode(session_present=False, return_code=0)
    # Clean session == False
    if not clean_session:
        if MQTT_database.session_exists(client_id) and search_client_id(client_id): #if there is a stored session for the client from the last time he connect then just send him CONACK
            outgoing_packet = CONNACK.encode(session_present=True, return_code=0)
        else:
            #create new session and create an entry for that session in the persistant sesions database
            MQTT_database.session_create(client_id)  # Create new session
            add_persistant_session(client_id)
            print(f"Current persistant sessions:{MQTT_persistant_sessions.operations.read_database()} ")
            outgoing_packet = CONNACK.encode(session_present=False, return_code=0)
    
    print(f'Client ID ({client_ID}) connected.')

    return outgoing_packet