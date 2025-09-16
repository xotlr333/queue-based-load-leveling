import time
import os

message_type = os.getenv("MESSAGE_TYPE", "UNKNOWN")
print(f"Consumer {message_type} started")

while True:
    print(f"Processing {message_type} messages...")
    time.sleep(30)
