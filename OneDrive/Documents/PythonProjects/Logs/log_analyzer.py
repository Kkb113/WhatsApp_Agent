from datetime import datetime
from collections import Counter
import os
import pandas as pd

class LogAnalyzer:

    def __init__(self, log_dict = dict, log_list = dict):
        self.log_dict = []
        self.log_list = []


    def import_log_module(self, file_name = 'delta_log.log', log_path = r"add_folder_path", content: str = ''):
        self.file_name = file_name
        self.log_path = log_path
        self.content = content

        path = os.path.join(self.log_path, self.file_name)

        try:
            with open(path, mode ='r') as file:
                self.content = file.read()
        except FileNotFoundError:
            print(f"file not found for path: {path}")
            return 
        
    def parse_content_module(self):
        if not self.content or self.content == '':
            print('Content is empty of none')
            return
        
        for log_file in self.content.splitlines():
            split_content = log_file.strip().split('|')
            timestamp = split_content[0].strip()
            level = split_content[1].strip()
            user_filed = split_content[2].strip()
            acction_filed = split_content[3].strip()

            user_id = [user.split('=')[1] for user in user_filed.split()]
            action =  [user_action.split('=')[1] for user_action in acction_filed.split()]
            hour_val = pd.to_datetime(timestamp).hour
            
            self.log_list.append({
                'timestamp': timestamp,
                'level': level,
                'user': ''.join(user_id),
                'action': ''.join(action),
                'hour': hour_val
            })

    def summarize_log_module(self, info_count: int = 0, error_count: int = 0, warn_count: int = 0, event_dict = None,
                              user_lvl_dict = None, events_by_hour = None, current_streak = 0, max_streak = 0):
        self.info_count = info_count
        self.error_count = error_count
        self.warn_count = warn_count
        self.current_streak = current_streak
        self.max_streak = max_streak
        
        if event_dict is None:
            self.event_dct = {}
            self.user_lvl_dict = {}
            self.events_by_hour = {}
            
        for char in self.log_list:
            if char['level']== 'INFO':
                self.info_count +=1
            if char['level'] == 'ERROR':
                self.error_count += 1
            if char['level'] == 'WARN':
                self.warn_count += 1
        
        self.event_dct = {"INFO": self.info_count,
                          "ERROR":  self.error_count,
                          "WARN": self.warn_count
                          }

        print(f"{'*'*5}Top Events Per Level{'*'*5}")

        max_value = list(sorted(self.event_dct.items(), key = lambda x: x[1], reverse= True))

        for lvl, num in max_value:
            print(f"{lvl}: {num}")


        for event in self.log_list:
            if event['user'] in self.user_lvl_dict:
                self.user_lvl_dict[event['user']] += 1
            else:
                self.user_lvl_dict[event['user']] = 1

        print()

        top_user =list(sorted(self.user_lvl_dict.items(), key = lambda x: x[1], reverse= True))
        print(f"{'*'*5}Top 5 Users{'*'*5}")
        for user, value in top_user[:5]:
            print(f"USER = {user} -> {value} events")

        print()
        for event in self.log_list:
            if event['hour'] in self.events_by_hour:
                self.events_by_hour[event['hour']] += 1
            else:
                self.events_by_hour[event['hour']] = 1

        top_event_hour = list(sorted(self.events_by_hour.items(), key= lambda x: x[1], reverse= True))
        print(f"{'*'*5}Evenet By Hour{'*'*5}")
        for time, value in top_event_hour:
            print(f"{time} -> {value}")

        print()

        for streak in self.log_list:
            if streak['level'] == 'ERROR':
                self.current_streak += 1
                if self.current_streak > self.max_streak:
                    self.max_streak = self.current_streak
            else:
                self.current_streak = 0

        print(f"Longest ERROR streak: {self.max_streak}")

    def main(self):
        self.import_log_module()
        self.parse_content_module()
        self.summarize_log_module()

if __name__ == '__main__':
    run_parse_log = LogAnalyzer()
    run_parse_log.main()
