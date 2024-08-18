import MQTT_binary
#module for retrasnmit the non acked QOS1 packets
def encode(topic: str, payload: str,packet_identifier):
    # Packet type
    packet_type = MQTT_binary.get_bits('PUBLISH')
    # Flags
    flags = "1010"  # Assuming QoS level 1 (010) and the messages is duplecated (retransmitted) (1010)

    # Packet length
    packet_length = len(topic) + len(payload) + 4
    packet_length_bits = format(packet_length, "08b")

    # Topic length
    topic_length = format(len(topic), "016b")

    # Topic
    topic_bits = ''.join(format(ord(i), '08b') for i in topic)

    # Payload
    payload_bits = ''.join(format(ord(i), '08b') for i in payload)

    # Packet Identifier (for QoS 1)
    packet_identifier_bits = ''
    if packet_identifier is not None:
        packet_identifier_bits = format(packet_identifier, "016b")

    packet = (
        packet_type +
        flags +
        packet_length_bits +
        topic_length +
        topic_bits +
        packet_identifier_bits +  # Append Packet Identifier for QoS 1
        payload_bits
    )

    encoded_packet = int(packet, 2).to_bytes((len(packet) + 7) // 8, byteorder="big")
    return encoded_packet

