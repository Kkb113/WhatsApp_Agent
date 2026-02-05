import os
from string import punctuation
import string 
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class FreqCounter:
    def __init__(self):
        self.check_dict = {}


    def import_txt_module(self, file_name: str = 'text.txt', folder_path: str = r'folder_path', content: str = ''):
        self.file_name = file_name
        self.folder_path = folder_path
        self.content = content

        path = os.path.join(self.folder_path, self.file_name)

        try:
            with open(path, mode = 'r', encoding= 'utf-8') as file:
                self.content = file.read()
        except FileNotFoundError:
            print("File not found")
            return
        
        self.content = (self.content.replace("’", "'")
                            .replace("‘", "'")
                            .replace("‑", "-")
                            .replace("–", "-")
                            .replace("—", "-"))

    def strip_possessive_text_module(self, words = None):
        self.words = []


        for word in self.content.split():
            word = word.lower()
            if word.endswith("'s"):
                word = word[:-2]
            self.words.append(word)


    def clean_word_module(self, clean_word = None):
        self.clean_word = []

        for word in self.words:
            
            word = ''.join(ch for ch in word if ch not in string.punctuation)

            if word:
                self.clean_word.append(word)


    def remove_stop_words(self, filtered_words = None):
        self.filtered_words = filtered_words

        stop_words = set(stopwords.words('english'))

        self.filtered_words = [char for char in self.clean_word if char not in stop_words]
        


    def analyze_module(self):

        if not self.filtered_words:
            print("No list found")
            return
        
        for char in self.filtered_words:
            if char in self.check_dict:
                self.check_dict[char] += 1
            else:
                self.check_dict[char] = 1

        top_text = dict(sorted(self.check_dict.items(), key = lambda x: x[1], reverse=True)[:10])
        total_words = len(self.filtered_words)
        print(f"{'No.':<4} {'Word':<15} | {'Count':<5} | {'Percentage'}")
        print("-" * 40)  
        for index, (key, value) in enumerate(top_text.items(), start=0):
            percentage = (value/total_words) * 100
            print(f"{index+1:<3}) {key:<15} | {value:<5} | {percentage:>6.2f}%")

    def main(self):
        self.import_txt_module()
        self.strip_possessive_text_module()
        self.clean_word_module()
        self.remove_stop_words()
        self.analyze_module()


if __name__ == '__main__':
    run = FreqCounter()
    run.main()
