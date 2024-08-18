import MQTT_binary
def encode(packet_identifier: int):
    # Packet type
    packet_type = MQTT_binary.get_bits('PUBACK')

    # Flags (PUBACK packet has no flags, so it's 0000)
    flags = "0000"

    # Packet length for PUBACK is always 2 bytes
    packet_length_value = 2
    packet_length = format(packet_length_value, "08b")

    # Packet identifier
    packet_identifier_bits = format(packet_identifier, "016b")

    packet = (
        packet_type +
        flags +
        packet_length +
        packet_identifier_bits
    )

    encoded_packet = int(packet, 2).to_bytes((len(packet) + 7) // 8, byteorder="big")
    return encoded_packet

#decode incoming bytes
def decode(encoded_packet: bytes):
    # Convert the bytes to a binary string
    packet_bits = ''.join(format(byte, '08b') for byte in encoded_packet)

    # Extract the packet type (first 4 bits)
    packet_type_bits = packet_bits[:4]
    packet_type = int(packet_type_bits, 2)

    # Extract the flags (next 4 bits, should be 0000 for PUBACK)
    flags_bits = packet_bits[4:8]
    flags = int(flags_bits, 2)

    # Extract the packet length (next 8 bits, should be 00000010 for PUBACK)
    packet_length_bits = packet_bits[8:16]
    packet_length = int(packet_length_bits, 2)

    # Extract the packet identifier (last 16 bits)
    packet_identifier_bits = packet_bits[16:]
    packet_identifier = int(packet_identifier_bits, 2)

    return {
        'Packet type': packet_type,
        'Flags': flags,
        'Packet length': packet_length,
        'Packet identifier': packet_identifier
    }
