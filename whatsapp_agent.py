from flask import Flask
import os
import pandas as pd

class WhatsAppAgent:
    app = Flask(__name__)

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

    def build_content_variables(self, twilio_template_role = None):
        self.twilio_template_role = []


        if not self.candidate:
            print("Candidate profiles is empty")
            return
        
        name_index, company_index = 1, 2

        for profile in self.candidate:
            for name, data in profile.items():
                company = data["Company"]
                self.twilio_template_role.append({f"{name_index}": name, f"{company_index}": company})


        print(self.twilio_template_role)





    def main(self):
        self.load_recipients()
        self.build_content_variables()

if __name__ == '__main__':
    run = WhatsAppAgent()
    run.main()

