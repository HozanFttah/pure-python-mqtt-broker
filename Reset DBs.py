import MQTT_database
import MQTT_persistant_sessions.operations

MQTT_database.topic_delete_all()
MQTT_database.session_delete_all()
MQTT_persistant_sessions.operations.delete_all_persistant_sessions()
print("Database Resetd")