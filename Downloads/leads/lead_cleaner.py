import json
import os
import sys
import re

class CleanLeads:

    def __init__(self, lead_info = None):
        if lead_info is None:
            self.lead_info = []

    def import_json_module(self, file_name: str = 'file_name.json', folder_path: str = r'folder_path', content = ''):

        self.file_name = file_name
        self.folder_path = folder_path
        self.content = content

        path = os.path.join(self.folder_path, self.file_name)

        try:
            with open(path, mode = 'r', encoding= 'utf-8') as file:
                self.content = json.load(file)
        except FileNotFoundError:
            print("No json file found")

        found = False
        for char in self.content:
            keys = ['id', 'name', 'company', 'email', 'phone']
            if all(char.get(k) is not None for k in keys):
                self.lead_info.append({
                    'id': char['id'],
                    'name': char['name'],
                    'company': char['company'],
                    'email': char['email'],
                    'phone': char['phone']
                })
                found = True

        if not found:
            print('no such keys found')

        record_count = len(self.lead_info)
        first_record = self.lead_info[0]

        print(f"Loaded {record_count} records from leads.json.")
        print(f"First record: {json.dumps(first_record)}")
        print()

    def normalization_module(self, normalization_output = None):
        self.normalization_output = []


        for char in self.lead_info:
            if char['email'] != '':
                clean_email = char['email'].lower().strip()
            else:
                clean_email = ''
            clean_name = char['name'].lower().strip()
            clean_company = char['company'].lower().strip()
            clean_phone = re.sub (r'[^0-9]', '', char['phone'])

            self.normalization_output.append({
                "id": char['id'],
                "name": clean_name,
                "company": clean_company,
                "email": clean_email,
                "phone": clean_phone,
                "last_6_digit_phone": clean_phone[-6:]
            })


    def clustering_module(self, clusters = None):
        self.clusters = {}

        if self.normalization_output is None:
            print("Error: No data found in normalization_output")
            return

        for record in self.normalization_output:
            email = record.get('email')

            if email:
                key = email
            else:
                key = record['name'] + "|" + record['company'] + "|" + record['last_6_digit_phone']

            if key in self.clusters:
                self.clusters[key].append(record['id'])
            else:
                self.clusters[key] = [record['id']]


    def merging_module(self):
        if not hasattr(self, "clusters") or not self.clusters:
            print("Error: No clusters found. Run clustering_module first.")
            return

        self.merged_output = []
        self.merge_report = []




        for cluser_key, id_list in self.clusters.items():

            records = [rec for rec in self.normalization_output if rec['id'] in id_list]

            email_candidates = [rec['email'] for rec in records if rec['email']]
            email = email_candidates[0] if email_candidates else ""

            name_candidates = [rec['name'] for rec in records if rec['name']]
            name = name_candidates[0] if name_candidates else ""


            phone_candidate = [rec['phone'] for rec in records if rec['phone']]
            phone = max(phone_candidate, key= len) if phone_candidate else ""
            last_6_digit_phone = phone[-6:] if phone else ""

            company_candidate = [rec['company'] for rec in records if rec['company']]
            company = company_candidate[0] if company_candidate else ""


            merged_record = {
                "ids": id_list,
                "name": name,
                "company": company,
                "email": email,
                "phone": phone,
                "last_6_digit_phone": last_6_digit_phone
            }
            self.merged_output.append(merged_record)

            report_entry = f"Cluster {cluser_key} → merged IDs {id_list}"
            self.merge_report.append(report_entry)

            print("\nMerged Output:")
            for rec in self.merged_output:
                print(rec)

            print("\nMerge Report:")
            for report in self.merge_report:
                print(report)



    def main(self):
        self.import_json_module()
        self.normalization_module()
        self.clustering_module()
        self.merging_module()

if __name__ == '__main__':
    run = CleanLeads()
    run.main()
