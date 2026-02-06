from app import app, WhatsAppAgent
from flask import request
import pandas as pd
import os

@app.route('/incoming', methods=['POST'])
def incoming():
    sender = request.values.get("From")
    recipient = request.values.get("To")
    button_text = request.values.get("ButtonText") or request.values.get("ButtonPayload")
    body = button_text or request.values.get("Body")
    message_sid = request.values.get("MessageSid")

    num_media_raw = request.values.get("NumMedia", "0")
    try:
        num_media = int(num_media_raw)
    except ValueError:
        num_media = 0

    media_urls = []
    for i in range(num_media):
        mu = request.values.get(f"MediaUrl{i}")
        if mu:
            media_urls.append(mu)

    data = {
        "Message_id": message_sid,
        "Sender": sender,
        "Recipient": recipient,
        "Text_Message": body
    }

    print(f"Incoming from {sender}: {body}")
    df = pd.DataFrame([data])
    df.to_csv("Leads.csv", mode='a', header=not os.path.exists("Leads.csv"), index=False)

    try:
        agent = WhatsAppAgent()
        agent.handle_incoming(sender=sender, user_text=body, media_urls=media_urls)
    except Exception as e:
        print("Agent auto-reply failed:", e)

    return 'OK', 200
