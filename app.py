from flask import Flask
import os
import pandas as pd
from dotenv import load_dotenv
from twilio.rest import Client
import json
from flask import jsonify
import requests
import re
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)

class WhatsAppAgent:
    def __init__(self, memory_dir="conversations"):
        self.memory_dir = memory_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash").strip()
        self.agent_sender_name = os.getenv("AGENT_SENDER_NAME", "Recruitment Team").strip()
        self.agent_company_name = os.getenv("AGENT_COMPANY_NAME", "Intellify Solutions Pvt. Ltd.").strip()
        self.agent_role_title = os.getenv("AGENT_ROLE_TITLE", "Senior Data Scientist").strip()
        self.agent_client_name = os.getenv("AGENT_CLIENT_NAME", "our client").strip()
        self.agent_jd_link = os.getenv("AGENT_JD_LINK", "").strip()  # optional
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        self.twilio_from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip()  # usually "whatsapp:+1415..."

    def load_recipients(self, file_name='apollo-contacts-export.csv', folder_path=r"C:\Users\karth\Downloads", df='', candidate=None, junk_profils=None):
        self.file_name = file_name
        self.folder_path = folder_path
        self.candidate = []
        self.df = df
        self.junk_profils = []

        path = os.path.join(self.folder_path, self.file_name)

        try:
            self.df = pd.read_csv(path)
        except FileNotFoundError:
            print(f"File not found")
            return

        if self.df is not None:
            columns = ['First Name', 'Mobile Phone', 'Company Name']
            columns_to_check = all(col in self.df.columns for col in columns)
            found = False

            if columns_to_check:
                for index, profile in self.df.iterrows():
                    raw_val = str(profile['Mobile Phone']).strip()
                    digits = "".join(filter(str.isdigit, raw_val))

                    if not digits or raw_val.lower() == 'nan':
                        self.junk_profils.append({
                            profile['First Name']: {
                                "Phone": "No Number",
                                "Company": profile["Company Name"]
                            }
                        })
                    else:
                        if digits.startswith('91') and len(digits) >= 12:
                            number = f"+{digits}"
                        elif len(digits) == 10:
                            number = f"+91{digits}"
                        elif digits.startswith('0') and len(digits) == 11:
                            number = f"+91{digits[1:]}"
                        else:
                            number = f"+{digits}"

                        self.candidate.append({
                            profile['First Name']: {
                                "Phone": number,
                                "Company": profile["Company Name"]
                            }
                        })
                found = True

        if not found:
            print(f"{columns} Not Available")

    def build_content_variables(self, twilio_template_role=None):
        self.twilio_template_role = []

        if not self.candidate:
            print("Candidate profiles is empty")
            return

        name_index, company_index = 1, 2

        for profile in self.candidate:
            for name, data in profile.items():
                company = data["Company"]
                self.twilio_template_role.append({f"{name_index}": name, f"{company_index}": company})

    def send_template_message(self):
        if not self.candidate:
            print("Candidate list is empty")
            return

        required_keys = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER', 'TWILIO_TEMPLATE_SID']
        if not all(key in os.environ for key in required_keys):
            print("Not all key exist, please check the keys")
            return

        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        template_sid = os.getenv('TWILIO_TEMPLATE_SID')

        client = Client(account_sid, auth_token)
        for char in self.candidate:
            for name, data in char.items():
                to_number = f"whatsapp:{data['Phone']}"
                content_vars = {"1": name, "2": data["Company"]}
                message = client.messages.create(
                    from_=from_number,
                    content_sid=template_sid,
                    to=to_number,
                    body="""I am reaching out from Intellify Solutions Pvt. Ltd. We were impressed by your profile and tried to connect with you via email, but since we couldn’t find your contact details, we are reaching out through WhatsApp.
We are currently hiring for a Senior Data Scientist role for one of our clients and would like to connect with you regarding this opportunity. If you are interested, we can share the Job Description and request your resume to initiate the interview process.
If you’re interested in this opportunity, please press the “Confirm” button to move forward. If not, you may simply ignore this message.""",
                    content_variables=json.dumps(content_vars)
                )
                print(f"Sent to {to_number}: SID={message.sid}, Status={message.status}")

    def main(self):
        self.load_recipients()
        self.build_content_variables()
        self.send_template_message()

    def _sender_key(self, whatsapp_from: str) -> str:
        digits = re.sub(r"\D", "", whatsapp_from or "")
        return digits[-15:] if digits else "unknown"

    def _state_path(self, sender_key: str) -> str:
        return os.path.join(self.memory_dir, f"{sender_key}_state.json")

    def _thread_path(self, sender_key: str) -> str:
        return os.path.join(self.memory_dir, f"{sender_key}_thread.jsonl")

    def _load_state(self, sender_key: str) -> dict:
        path = self._state_path(sender_key)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self, sender_key: str, state: dict) -> None:
        path = self._state_path(sender_key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _append_thread(self, sender_key: str, role: str, content: str) -> None:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "content": content
        }
        with open(self._thread_path(sender_key), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _load_last_messages(self, sender_key: str, limit: int = 12) -> list:
        path = self._thread_path(sender_key)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-limit:]
            msgs = []
            for line in lines:
                obj = json.loads(line)
                msgs.append({"role": obj.get("role", "user"), "content": obj.get("content", "")})
            return msgs
        except Exception:
            return []

    def _twilio_client(self):
        if not (self.twilio_account_sid and self.twilio_auth_token):
            return None
        return Client(self.twilio_account_sid, self.twilio_auth_token)

    def _ensure_whatsapp_prefix(self, n: str) -> str:
        if not n:
            return n
        return n if n.startswith("whatsapp:") else f"whatsapp:{n}"

    def send_whatsapp_message(self, to_number: str, body: str) -> None:
        client = self._twilio_client()
        if client is None:
            print("Twilio client not ready (missing SID/TOKEN).")
            return

        from_number = self._ensure_whatsapp_prefix(self.twilio_from_number)
        to_number = self._ensure_whatsapp_prefix(to_number)

        msg = client.messages.create(
            from_=from_number,
            to=to_number,
            body=body
        )
        print(f"Auto-reply sent to {to_number}: SID={msg.sid}, Status={msg.status}")

    def _openrouter_chat(self, messages: list) -> str:
        if not self.openrouter_api_key:
            return ""

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", "http://localhost"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "WhatsApp Recruitment Agent"),
        }
        payload = {
            "model": self.openrouter_model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 350
        }

        r = requests.post(url, headers=headers, json=payload, timeout=45)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

    def _system_prompt(self, state: dict) -> str:
        stage = state.get("stage", "new")
        jd = self.agent_jd_link.strip()

        return f"""
You are a WhatsApp recruitment assistant for {self.agent_company_name}.
You are chatting with a candidate about a {self.agent_role_title} role for {self.agent_client_name}.
Be concise, friendly, and professional. Ask ONE question at a time.
Your goal: qualify interest and collect details needed to schedule screening.

Conversation stage: {stage}

Rules:
- If candidate says not interested / stop / unsubscribe: confirm and set stage "opted_out", and do not continue.
- If candidate is interested: ask for resume (PDF/link) OR key details (years exp, location, notice period, current CTC, expected CTC).
- If candidate asks for JD: share JD link if available; if not, offer to summarize and ask preferred email/WhatsApp for receiving JD.
- Never ask for sensitive IDs (Aadhaar, PAN, etc).
- Always include a simple opt-out line: "Reply STOP to opt out."

Output format (IMPORTANT): Return ONLY a JSON object with:
{{
  "reply_text": "...",
  "next_stage": "...",
  "lead_update": {{
    "interest": "yes/no/unknown",
    "years_experience": "",
    "location": "",
    "notice_period": "",
    "current_ctc": "",
    "expected_ctc": "",
    "email": "",
    "resume_received": "yes/no",
    "availability": ""
  }}
}}

JD link (if any): {jd}
""".strip()

    def handle_incoming(self, sender: str, user_text: str, media_urls=None) -> None:
        sender_key = self._sender_key(sender)
        state = self._load_state(sender_key) or {"stage": "new", "lead": {}}

        txt = (user_text or "").strip()
        media_urls = media_urls or []
        low = txt.lower()
        if any(k in low for k in ["stop", "unsubscribe", "do not contact", "dont contact", "don't contact"]):
            state["stage"] = "opted_out"
            self._append_thread(sender_key, "user", txt)
            self._append_thread(sender_key, "assistant", "Understood. I will not message you further. Reply START if you want to reconnect.")
            self._save_state(sender_key, state)
            self.send_whatsapp_message(sender, "Understood. I will not message you further. Reply START if you want to reconnect.")
            return
        if len(media_urls) > 0:
            state.setdefault("lead", {})
            state["lead"]["resume_received"] = "yes"


        self._append_thread(sender_key, "user", txt if txt else "[empty_message]")

        history = self._load_last_messages(sender_key, limit=10)
        system_msg = {"role": "system", "content": self._system_prompt(state)}
        user_msg = {
            "role": "user",
            "content": f"Candidate message: {txt}\nNumMedia: {len(media_urls)}"
        }

        reply_json_text = ""
        try:
            reply_json_text = self._openrouter_chat([system_msg] + history + [user_msg])
        except Exception as e:
            print("OpenRouter call failed:", e)

        if not reply_json_text:
            fallback = "Thanks for your message. Are you interested in the Senior Data Scientist role? If yes, please share your resume or key details (years of experience, location, notice period). Reply STOP to opt out."
            self._append_thread(sender_key, "assistant", fallback)
            self._save_state(sender_key, state)
            self.send_whatsapp_message(sender, fallback)
            return

        reply_text = None
        next_stage = None
        lead_update = {}

        try:
            parsed = json.loads(reply_json_text)
            reply_text = (parsed.get("reply_text") or "").strip()
            next_stage = (parsed.get("next_stage") or "").strip()
            lead_update = parsed.get("lead_update") or {}
        except Exception:
            reply_text = reply_json_text.strip()

        if next_stage:
            state["stage"] = next_stage
        state.setdefault("lead", {})
        for k, v in (lead_update or {}).items():
            if v is not None and str(v).strip() != "":
                state["lead"][k] = v

        if reply_text:
            self._append_thread(sender_key, "assistant", reply_text)
            self._save_state(sender_key, state)
            self.send_whatsapp_message(sender, reply_text)


@app.route('/send_campaign', methods=['POST'])
def send_campaign():
    agent = WhatsAppAgent()
    agent.load_recipients()
    agent.build_content_variables()
    agent.send_template_message()
    return jsonify({"status": "Campaign Triggered"})

if __name__ == '__main__':
    import sys
    sys.modules['app'] = sys.modules[__name__]
    import incoming  # noqa
    import status    # noqa

    app.run(debug=True)
