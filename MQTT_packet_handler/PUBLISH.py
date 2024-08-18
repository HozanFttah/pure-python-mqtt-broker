from MQTT_control_packets import PUBLISH
import MQTT_database

def handle(incoming_packet: dict, client_ID: str):

    topic = incoming_packet.get('Topic')
    payload = incoming_packet.get('Payload')
    # Update topic
    if MQTT_database.topic_update_value(topic, payload):
        print(f'Client ID ({client_ID}) updated topic ({topic}) updated value to: {payload}')

    # Create publish packet but before check if the QOS level, beacuse the decoded packet differ
    if incoming_packet.get('Flags')[1] == '0' and incoming_packet.get('Flags')[2] == '0':
        outgoing_packet = PUBLISH.encode(topic, payload)
    elif incoming_packet.get('Flags')[1] == '0' and incoming_packet.get('Flags')[2] == '1':
        outgoing_packet = PUBLISH.encode_QOS1(topic, payload)
    #here should add the QOS 2 handel
    return outgoing_packet