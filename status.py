from app import app
from flask import request
import os
import pandas as pd


@app.route('/status', methods = ['POST'])
def status():

    message_sid = request.values.get("MessageSid")
    message_status = request.values.get("MessageStatus")
    to_number = request.values.get("To")

    data = {
        "MessageSid": message_sid,
        "Recipient": to_number,
        "DeliveryStatus": message_status.capitalize()   
    }

    print(f"Status update: {message_sid} → {message_status}")
    df = pd.DataFrame([data])

    df.to_csv("Delivery_status.csv", mode= 'a', header=not os.path.exists("Delivery_status.csv"), index=False)

    return 'OK', 200