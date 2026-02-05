import json
from datetime import date
from datetime import datetime

class PersonalFinanceLedger:

    def __init__(self, ledger = None):
        self.ledger = []

    def add_transaction(self, option = None, category = None):
        self.option = ['income', 'expense']
        self.category_option = ["food", "rent", "transport", "other"]

        type = input("Type (income/expense):").lower()
        if type in self.option:
            while True:
                try:
                    amount = float(input("Amount (₹):"))
                    break
                except ValueError:
                    print("Invalid Amount, Please enter a valid amount")
            category = input("Category (food/rent/transport/other):").lower()
            if category in self.category_option:
                set_date = input("Date (YYYY-MM-DD) [default: today or click enter for custom date]:")
                if set_date == "":
                    set_date = date.today()
                else:
                    while True:
                        try:
                            datetime.strptime(set_date, "%Y-%m-%d")
                            break
                        except ValueError:
                            set_date  = input("Invalid Date, Please Enter a valid date")



                self.ledger.append({"type": type, "amount": amount, "category": category, "date": set_date})
            else:
                print("No such category found")

        else:
            print("No such type found")
                


    
    def display_input(self):
        while True:
            print("="*15)
            print("FIN-LEDGER (Local CLI Tracker)")
            print("="*15)
            print()
            print("1) Add transaction")
            print("2) List transactions")
            print("4) Delete transaction")
            print("5) Monthly report")
            print("6) Export JSON")
            print("0) Exit")

            try:
                choice = int(input("Choose: "))
            except ValueError:
                print("Invalid Choice")

            
            if choice == 1:
                self.add_transaction()
            elif choice == 2:
                pass
            elif choice == 3:
                pass
            elif choice == 4:
                pass
            elif choice == 5:
                pass
            elif choice == 6:
                pass
            elif choice == 7:
                print("Thank you for using finance ledger, hope we meet again!!")
                break

run_finance = PersonalFinanceLedger()
run_finance.add_transaction()
run_finance.display_input()