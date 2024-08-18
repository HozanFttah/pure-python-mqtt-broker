import json
import os
def initialize_database():

    # Create database file
    if not os.path.exists("MQTT_persistant_sessions/db_persistance.json"):
        with open("MQTT_persistant_sessions/db_persistance.json", "w+") as db:
            db.write('{ "Sessions" : []}')
initialize_database()
def read_database():
    # Read database file
    with open("MQTT_persistant_sessions/db_persistance.json", "r") as db:
        database = json.load(db)

    return database
# Write content to database file
def write_database(database):
    with open("MQTT_persistant_sessions/db_persistance.json", "w") as file:
        json.dump(database, file, indent=4, sort_keys=True)

def add_value_to_topic(client_id,topic,value):
    database=read_database()
    sessions=database.get("Sessions")
    # Iterate through the 'Sessions' list
    for session in sessions:
        # Check if the specified 'client_id' is a key in the current dictionary
        if client_id in session:
            # Access the 'Subscriptions' dictionary of the current 'client_id'
            subscriptions = session[client_id]['Subscriptions']
            # Check if the 'topic' exists in the 'Subscriptions' dictionary
            if topic in subscriptions:
                # Append the new 'value' to the existing 'topic' list
                subscriptions[topic].append(value)
            else:
                # If the 'topic' does not exist, create it with the new 'value'
                subscriptions[topic] = [value]
            database.update({"Sessions": sessions})
            write_database(database)
            break  # Exit the loop after appending the value
def add_persistant_session(client_id):
    # Check if the client_id already exists in the sessions
    database = read_database()
    sessions = database.get("Sessions")
    for session in sessions:
        if client_id in session:
            print(f"Session for client_id {client_id} already exists.")
            return sessions
    # If the client_id does not exist, add a new session
    new_persistant_session = {client_id: {"Subscriptions": {}}}
    sessions.append(new_persistant_session)
    database.update({"Sessions": sessions})
    write_database(database)

def search_client_id(client_id):
    database = read_database()
    sessions = database.get("Sessions")
    for session in sessions:
        if client_id in session:
            return True
    return False
def delete_persistant_session(client_id):
    database = read_database()
    sessions = database.get("Sessions")
    for i, session in enumerate(sessions):
        if client_id in session:
            # Delete the dictionary with 'MQTT_FX_Client' key
            del sessions[i]
            break  # Exit the loop after deleting the entry
    database.update({"Sessions": sessions})
    write_database(database)

def delete_all_persistant_sessions():
    database=read_database()
    sessions=[]
    database.update({"Sessions": sessions})
    write_database(database)
def delete_topic_from_presistant_session(client_id,topic):
    database = read_database()
    sessions = database.get("Sessions")
    for session in sessions:
        # Check if 'hozan' is a key in the session
        if client_id  in session:
            # Access 'hozan's subscriptions
            subscriptions = session[client_id]["Subscriptions"]
            # Check if 'web' is a key in the subscriptions
            if topic in subscriptions:
                # Delete the 'web' entry
                del subscriptions[topic]
                break  # Exit the loop after deleting the entry
    database.update({"Sessions": sessions})
    write_database(database)
