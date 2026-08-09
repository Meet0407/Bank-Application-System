import random
import matplotlib.pyplot as plt
import mysql.connector
from datetime import datetime
import os
import math  

# Connect to MySQL Database
conn = mysql.connector.connect(host='localhost', user='root', password='', database='bankaccountdatabase')
cursor = conn.cursor()

# Create account Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    account_number BIGINT PRIMARY KEY,
    name VARCHAR(255),
    balance FLOAT,
    pin INT,
    account_type VARCHAR(50) DEFAULT 'Savings',
    interest_rate FLOAT DEFAULT 3.2
);
""")
# Create transactions Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_number BIGINT,
    type VARCHAR(50),
    amount FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_number) REFERENCES accounts(account_number)
);
""")

# Create Loans Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number BIGINT,
    loan_type VARCHAR(50),
    loan_amount FLOAT,
    interest_rate FLOAT,
    tenure INT,
    remaining_amount FLOAT,
    status VARCHAR(50) DEFAULT 'Active',
    FOREIGN KEY (account_number) REFERENCES accounts(account_number)
);
""")

def get_numeric_input(prompt, is_float=False):
    while True:
        user_input = input(prompt)
        try:
            if is_float:
                return float(user_input)
            else:
                return int(user_input)
        except ValueError:
            print("********** Error: Please enter a valid number! **********")
            
def get_alpha_input(prompt):
    while True:
        user_input = input(prompt).strip()
        if all(x.isalpha() or x.isspace() for x in user_input) and len(user_input) > 0:
            return user_input
        else:
            print("********** Error: Name must contain only letters! **********")

class BankAccount:
    @staticmethod
    def generate_otp():
        return random.randint(1000, 9999)

    @staticmethod
    def verify_otp(generated_otp):
        user_otp = get_numeric_input("Enter the OTP: ")
        return user_otp == generated_otp

    @staticmethod
    def register(name, pin, initial_balance=0):
        
        otp = BankAccount.generate_otp()
        print(f"********** Security OTP for Registration: {otp} **********")
        
        if not BankAccount.verify_otp(otp):
            print("********** Invalid OTP. Registration failed. **********")
            return None
        
        account_number = random.randint(10000000000, 99999999999)
        account_type = "Savings"  # Default account type
        interest_rate = 3.2  # Default interest rate for Savings Account
        
        # Ensure initial balance is at least 1000
        if initial_balance < 1000:
            print("Initial balance must be at least 1000.")
            return None
        
        cursor.execute("INSERT INTO accounts (account_number, name, balance, pin, account_type, interest_rate) VALUES (%s, %s, %s, %s, %s, %s)",
                       (account_number, name, initial_balance, pin, account_type, interest_rate))
        conn.commit()
        print(f"********** {account_type} Account registered for {name} with Account Number: {account_number} **********")
        return account_number
    
    @staticmethod
    def login(account_number, pin):
        cursor.execute("SELECT name, balance, account_type, interest_rate FROM accounts WHERE account_number=%s AND pin=%s", (account_number, pin))
        result = cursor.fetchone()
        if result:
            # Generate OTP for login verification
            otp = BankAccount.generate_otp()
            print(f"********** OTP for login: {otp} **********")
            if BankAccount.verify_otp(otp):
                return BankAccount(account_number, result[0], result[1], result[2], result[3])
            else:
                print("********** Invalid OTP. Login failed. **********")
                return None
        else:
            print("********** Invalid account number or PIN. **********")
            return None
    
    def __init__(self, account_number, name, balance, account_type, interest_rate):
        self.account_number = account_number
        self.name = name
        self.balance = balance
        self.account_type = account_type
        self.interest_rate = interest_rate
        self.passbook_file = f"{self.account_number}_passbook.txt"
    
    def update_passbook(self, transaction_type, amount):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Bank and account details
        bank_name = "Bank of Baroda"
        branch_address = "Shukan Chowkdi, Nikol, Ahmedabad - 382350"
        phone_no = "1800 5700"
        ifsc_code = "BARB0VJSCIE"
        
        # Check if the passbook file exists (i.e., if it's the first transaction)
        if not os.path.exists(self.passbook_file):
            # Write bank and account details as a header
            with open(self.passbook_file, 'w') as f:
                f.write("========== Bank Details ==========\n")
                f.write(f"Bank Name: {bank_name}\n")
                f.write(f"Branch Address: {branch_address}\n")
                f.write(f"Phone No.: {phone_no}\n")
                f.write(f"IFSC Code: {ifsc_code}\n")
                f.write("========== Account Details ==========\n")
                f.write(f"Account Holder Name: {self.name}\n")
                f.write(f"Account Number: {self.account_number}\n")
                f.write(f"Account Type: {self.account_type}\n")
                f.write("\n")
                f.write("Transaction History:\n")
                f.write("=" * 50 + "\n")
        
        # Append the transaction details
        with open(self.passbook_file, 'a') as f:
            f.write(f"{timestamp} | {transaction_type} | Amount: {amount} | Balance: {self.balance}\n")
    
    def deposit(self, amount):
        self.balance += amount
        cursor.execute("UPDATE accounts SET balance=%s WHERE account_number=%s", (self.balance, self.account_number))
        cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (%s, %s, %s)",
                       (self.account_number, "Deposit", amount))
        conn.commit()
        self.update_passbook("Deposit", amount)
        print(f"********** Deposited {amount}. New balance: {self.balance} **********")
    
    def withdraw(self, amount):
        if amount > self.balance:
            print("********** Insufficient balance! **********")
        else:
            self.balance -= amount
            # Check if balance falls below 1000 after withdrawal
            if self.balance < 1000:
                penalty = 100  # Penalty amount
                self.balance -= penalty
                cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (%s, %s, %s)",
                               (self.account_number, "Penalty", penalty))
                print(f"********** Penalty of {penalty} imposed for falling below minimum balance! **********")
            
            cursor.execute("UPDATE accounts SET balance=%s WHERE account_number=%s", (self.balance, self.account_number))
            cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (%s, %s, %s)",
                           (self.account_number, "Withdrawal", amount))
            conn.commit()
            self.update_passbook("Withdrawal", amount)
            print(f"********** Withdrawn {amount}. New balance: {self.balance} **********")
    
    def transfer(self, recipient_acc, amount):
        cursor.execute("SELECT balance FROM accounts WHERE account_number=%s", (recipient_acc,))
        recipient_data = cursor.fetchone()
        if recipient_data:
            if amount > self.balance:
                print("********** Insufficient funds for transfer! **********")
            else:
                self.withdraw(amount)
                cursor.execute("UPDATE accounts SET balance=balance+%s WHERE account_number=%s", (amount, recipient_acc))
                cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (%s, %s, %s)",
                               (recipient_acc, "Transfer Received", amount))
                conn.commit()
                self.update_passbook("Transfer Sent", amount)
                print(f"********** Transferred {amount} to account {recipient_acc}. **********")
        else:
            print("********** Recipient account not found! **********")
            
    def check_balance(self):
        print(f"\n********** Account Balance **********")
        print(f"Account Holder Name: {self.name}")
        print(f"Current Balance: {self.balance}")
        print("*************************************")
    
    def show_transactions(self):
        cursor.execute("SELECT type, amount, timestamp FROM transactions WHERE account_number=%s ORDER BY id DESC LIMIT 5", (self.account_number,))
        transactions = cursor.fetchall()
        print("********** Mini Statement **********")
        for transaction in transactions:
            print(f"{transaction[2]} | {transaction[0]}: {transaction[1]}")
    
    def plot_transaction_history(self):
        cursor.execute("SELECT type, SUM(amount) FROM transactions WHERE account_number=%s GROUP BY type", (self.account_number,))
        transactions = cursor.fetchall()
        if transactions:
            labels = [t[0] for t in transactions]
            sizes = [t[1] for t in transactions]
            colors = ['green' if t[0] == 'Deposit' else 'red' for t in transactions]
            explode = [0.1] * len(labels)
            plt.figure(figsize=(5, 5))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140, shadow=True, explode=explode)
            plt.title(f"Transaction Distribution for {self.name}")
            plt.legend(labels, loc="best")
            plt.show()
        else:
            print("********** No transactions available for visualization **********")
    
    def change_pin(self, new_pin):
        # Generate OTP for PIN change verification
        otp = BankAccount.generate_otp()
        print(f"********** OTP for PIN change: {otp} **********")
        if BankAccount.verify_otp(otp):
            cursor.execute("UPDATE accounts SET pin=%s WHERE account_number=%s", (new_pin, self.account_number))
            conn.commit()
            print("********** PIN changed successfully! **********")
        else:
            print("********** Invalid OTP. PIN change failed. **********")
    
    def calculate_interest(self):
        if self.account_type == "Savings":
            interest = (self.balance * self.interest_rate) / 100
            self.balance += interest
            cursor.execute("UPDATE accounts SET balance=%s WHERE account_number=%s", (self.balance, self.account_number))
            cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (%s, %s, %s)",
                           (self.account_number, "Interest", interest))
            conn.commit()
            self.update_passbook("Interest", interest)
            print(f"********** Interest of {interest} added. New balance: {self.balance} **********")
        else:
            print("********** Interest calculation is not applicable for this account type. **********")
    
    def apply_for_loan(self):
        while True:
            print("\n********** Loan Types **********")
            print("1. Home Loan (Interest Rate: 8.5%)")
            print("2. Gold Loan (Interest Rate: 10%)")
            print("3. Personal Loan (Interest Rate: 12%)")
            loan_type_choice = input("Enter loan type (1/2/3) or 'q' to cancel: ")
            
            if loan_type_choice.lower()=='q':
                return
            
            loan_types = {"1": ("Home Loan", 8.5), "2": ("Gold Loan", 10),"3": ("Personal Loan", 12)}
        
            if loan_type_choice in loan_types:
                loan_type, interest_rate = loan_types[loan_type_choice]
                loan_amount = get_numeric_input("Enter loan amount: ",is_float=True)
                tenure = get_numeric_input("Enter loan tenure (in months): ")
            
           
                cursor.execute("""
                    INSERT INTO loans (account_number, loan_type, loan_amount, interest_rate, tenure, remaining_amount)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (self.account_number, loan_type, loan_amount, interest_rate, tenure, loan_amount))
                conn.commit()
                print(f"********** {loan_type} of {loan_amount} applied successfully! **********")
                break
            else:
                print("********** Invalid loan type! **********")
    
    def view_loans(self):
        cursor.execute("SELECT loan_id, loan_type, loan_amount, interest_rate, tenure, remaining_amount, status FROM loans WHERE account_number=%s", (self.account_number,))
        loans = cursor.fetchall()
        if loans:
            print("\n********** Your Loans **********")
            for loan in loans:
                print(f"Loan ID: {loan[0]}, Type: {loan[1]}, Amount: {loan[2]}, Interest Rate: {loan[3]}%, Tenure: {loan[4]} months, Remaining Amount: {loan[5]}, Status: {loan[6]}")
        else:
            print("********** No loans found! **********")
    
    def calculate_emi(self, loan_amount, interest_rate, tenure):
        # Convert annual interest rate to monthly and percentage to decimal
        monthly_interest_rate = (interest_rate / 12) / 100
        # EMI formula
        emi = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** tenure) / ((1 + monthly_interest_rate) ** tenure - 1)
        return emi
    
    def repay_loan(self):
        self.view_loans()
        loan_id = get_numeric_input("Enter Loan ID to repay: ")
        
        cursor.execute("SELECT loan_amount, interest_rate, tenure, remaining_amount FROM loans WHERE loan_id=%s AND account_number=%s", (loan_id, self.account_number))
        loan_data = cursor.fetchone()
        if loan_data:
            loan_amount, interest_rate, tenure, remaining_amount = loan_data
            emi = self.calculate_emi(loan_amount, interest_rate, tenure)
            print(f"********** EMI for this loan: {emi:.2f} **********")
            
            if self.balance < emi:
                print("********** Insufficient balance to pay EMI! **********")
            else:
              
                if remaining_amount - emi < 0:
                    emi = remaining_amount  
                    remaining_amount = 0  
                else:
                    remaining_amount -= emi
                
                self.balance -= emi
                cursor.execute("UPDATE loans SET remaining_amount=%s WHERE loan_id=%s", (remaining_amount, loan_id))
                if remaining_amount <= 0:
                    cursor.execute("UPDATE loans SET status='Paid' WHERE loan_id=%s", (loan_id,))
                cursor.execute("UPDATE accounts SET balance=%s WHERE account_number=%s", (self.balance, self.account_number))
                cursor.execute("INSERT INTO transactions (account_number, type, amount) VALUES (%s, %s, %s)",
                               (self.account_number, "Loan Repayment", emi))
                conn.commit()
                self.update_passbook("Loan Repayment", emi)
                print(f"********** EMI of {emi:.2f} paid successfully! Remaining loan amount: {remaining_amount:.2f} **********")
        else:
            print("********** Invalid Loan ID! **********")
            
    def delete_account(self):
        # Ask for confirmation to prevent accidental clicks
        confirm = input(f"Are you sure you want to delete account {self.account_number}? (yes/no): ").lower()
        if confirm == 'yes':
            # Security check using your existing OTP system
            otp = BankAccount.generate_otp()
            print(f"********** Security OTP for Account Deletion: {otp} **********")
            if BankAccount.verify_otp(otp):
                try:
                    # 1. Delete transactions first (Foreign Key requirement)
                    cursor.execute("DELETE FROM transactions WHERE account_number=%s", (self.account_number,))
                    # 2. Delete loans associated with the account
                    cursor.execute("DELETE FROM loans WHERE account_number=%s", (self.account_number,))
                    # 3. Finally, delete the account itself
                    cursor.execute("DELETE FROM accounts WHERE account_number=%s", (self.account_number,))
                    
                    conn.commit()
                    
                    # 4. Clean up the physical passbook file
                    if os.path.exists(self.passbook_file):
                        os.remove(self.passbook_file)
                        
                    print("********** Account and all history deleted successfully. **********")
                    return True  # Tells the menu to log the user out
                except Exception as e:
                    print(f"Error during deletion: {e}")
                    conn.rollback()
            else:
                print("********** Invalid OTP. Deletion cancelled. **********")
        else:
            print("********** Deletion cancelled. **********")
        return False
    
# Main Menu
while True:
    print("\n********** WELCOME TO BANK OF BARODA **********")
    print("1. Register\n2. Login\n3. Exit")
    choice = input("Enter choice: ")
    
    if choice == "1":
        name = get_alpha_input("Enter your Fullname: ")
        pin = get_numeric_input("Set a 4-digit PIN: ")
        initial_balance = get_numeric_input("Enter initial balance: ", is_float=True)
        if initial_balance < 1000:
            print("Initial balance must be at least 1000.")
            initial_balance = get_numeric_input("Enter initial balance: ", is_float=True)
        account_number = BankAccount.register(name, pin, initial_balance)
    elif choice == "2":
        account_number = get_numeric_input("Enter your account number: ")
        pin = get_numeric_input("Enter PIN: ")
        account = BankAccount.login(account_number, pin)
        if account:
            while True:
                print("\n********** ACCOUNT MENU **********")
                print("1. Deposit\n2. Withdraw\n3. Transfer\n4.Check Balance\n5. Mini Statement\n6. Change PIN\n7. Transaction History Chart\n8. Calculate Interest\n9. Apply for Loan\n10. View Loans\n11. Repay Loan\n12. Logout\n13. Delete Account")
                action = input("Enter choice: ")
                if action == "1":
                    amount = get_numeric_input("Enter deposit amount: ", is_float=True)
                    account.deposit(amount)
                elif action == "2":
                    amount = get_numeric_input("Enter withdrawal amount: ", is_float=True)
                    account.withdraw(amount)
                elif action == "3":
                    receiver_acc = get_numeric_input("Enter recipient account number: ")
                    amount = get_numeric_input("Enter transfer amount: ", is_float=True)
                    account.transfer(receiver_acc, amount)
                elif action == "4":
                    account.check_balance()
                elif action == "5":
                    account.show_transactions()
                elif action == "6":
                    new_pin = get_numeric_input("Enter new 4-digit PIN: ")
                    account.change_pin(new_pin)
                elif action == "7":
                    account.plot_transaction_history()
                elif action == "8":
                    account.calculate_interest()
                elif action == "9":
                    account.apply_for_loan()
                elif action == "10":
                    account.view_loans()
                elif action == "11":
                    account.repay_loan()
                elif action == "12":
                    print("********** Logging out **********")
                    break
                elif action == "13":
                    if account.delete_account():
                        break
    elif choice == "3":
        print("********** Thank you for using our Bank! **********")
        break

# Close database connection
conn.close()
