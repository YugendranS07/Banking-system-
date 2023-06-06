import sys
import mysql.connector
import smtplib
import random

# Connect to the database
db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="atm"
)

# Create a cursor
cursor = db.cursor()

# Function to display the login menu
# Function to display the login menu
def login_menu():
    print("Welcome to the ATM")
    account_number = input("Enter your account number: ")
    pin = input("Enter your PIN: ")
    cursor.execute("SELECT * FROM accounts WHERE account_number = %s AND pin = %s", (account_number, pin))
    account = cursor.fetchone()
    if account:
        print("Login successful")
        otp = send_otp(account_number)
        otp_attempts = 0
        while otp_attempts < 3:
            user_otp = input("Enter OTP: ")
            if user_otp == otp:
                print("OTP verification successful")
                main_menu(account_number)
                break
            else:
                otp_attempts += 1
                if otp_attempts < 3:
                    print("Incorrect OTP. Please try again.")
                else:
                    print("Maximum number of attempts exceeded")
                    try:
                        cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
                        user = cursor.fetchone()
                        sender_email = "atmtranscation@gmail.com"
                        receiver_email = user[4] # email is stored in the 4th column of the accounts table
                        password ="ugqz qxtn ocrd vwuz"
                        message = f"Subject: Maximum OTP Attempts Exceeded\n\nDear Account Holder,\n\nThe maximum number of OTP attempts has been exceeded for your account ({account_number}). Please contact customer support for assistance.\n\nThank you,\nATM Team"
                        with smtplib.SMTP('smtp.gmail.com', 587) as server:
                            server.starttls()
                            server.login(sender_email, password)
                            server.sendmail(sender_email, receiver_email, message)
            
                        print("Email notification sent to account holder")
                    except:
                        print("Unable to send email notification")
                    break
                    break
    else:
        print("Invalid account number or PIN")
        login_menu()
        
# Function to verify the account number and PIN
def verify_pin(account_number, pin):
    cursor.execute("SELECT id FROM accounts WHERE account_number = %s AND pin = %s", (account_number, pin))
    result = cursor.fetchone()
    if result:
        return True
    else:
        return False

# Function to display the main menu
def main_menu(account_number):
    account_id = get_account_id(account_number)
    print("Main Menu")
    print("1. Check balance")
    print("2. Withdraw")
    print("3. Deposit")
    print("4. Transaction history")
    print("5. Change PIN")
    print("6. Exit")
    choice = input("Enter choice: ")
    if choice == "1":
        check_balance(account_id)
    elif choice == "2":
        withdraw_menu(account_id)
    elif choice == "3":
        deposit_menu(account_id)
    elif choice == "4":
        history_menu(account_id)
    elif choice == "5":
        change_pin_menu(account_id)
    elif choice == "6":
        print("Goodbye!")
        sys.exit()
    else:
        print("Invalid choice")
        main_menu(account_number)

# Function to get the account ID from the account number
def get_account_id(account_number):
    cursor.execute("SELECT id FROM accounts WHERE account_number = %s", (account_number,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None
    
def get_balance(account_id):
        # Execute the SELECT query to get the account balance
        query = "SELECT balance FROM accounts WHERE account_number = %s"
        cursor.execute(query, (account_id,))
        
        # Fetch the result and return the balance
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None
# Function to display the check balance menu
def check_balance(account_id):
    cursor.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
    balance = cursor.fetchone()[0]
    print("Your current balance is: " + str(balance))
    main_menu(get_account_number(account_id))

# Function to display the withdraw menu
def withdraw_menu(account_id):
    print("Withdraw Menu")
    amount = float(input("Enter amount to withdraw: "))
    if amount < 0:
        print("Invalid amount")
        withdraw_menu(account_id)
    else:
        cursor.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
        balance = cursor.fetchone()[0]
        if amount > balance:
            print("Insufficient funds")
            withdraw_menu(account_id)
        else:
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account_id))
            db.commit()
            cursor.execute("SELECT account_number FROM accounts WHERE id = %s", (account_id,))

# fetch the account number from the query result
            account_number = cursor.fetchone()[0]
            add_transaction(account_id, "Withdrawal", amount,account_number)
            print("Withdrawal successful")
            main_menu(get_account_number(account_id))

# Function to display the deposit menu
def deposit_menu(account_id):
    print("Deposit Menu")
    amount = float(input("Enter amount to deposit: "))
    if amount < 0:
        print("Invalid amount")
        deposit_menu(account_id)
    else:
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount,account_id))
        db.commit()
        cursor.execute("SELECT account_number FROM accounts WHERE id = %s", (account_id,))

# fetch the account number from the query result
        account_number = cursor.fetchone()[0]
        add_transaction(account_id, "Deposit", amount,account_number)
        print("Deposit successful")
        main_menu(get_account_number(account_id))

# Function to display the transaction history menu
def history_menu(account_id):
    print("Transaction History")
    cursor.execute("SELECT type, amount, date FROM transactions WHERE account_id = %s", (account_id,))
    transactions = cursor.fetchall()
    if len(transactions) == 0:
        print("No transactions found")
    else:
        print("{:<10} {:<10} {}".format("Type", "Amount", "Date"))
        for transaction in transactions:
            print("{:<10} {:<10} {}".format(transaction[0], transaction[1], transaction[2]))
    main_menu(get_account_number(account_id))

# Function to display the change PIN menu
def change_pin_menu(account_id):
    print("Change PIN Menu")
    new_pin = input("Enter new PIN: ")
    confirm_pin = input("Confirm new PIN: ")
    if new_pin != confirm_pin:
        print("PINs do not match")
        change_pin_menu(account_id)
    else:
        cursor.execute("UPDATE accounts SET pin = %s WHERE id = %s", (new_pin, account_id))
        db.commit()
        print("PIN changed successfully")
        main_menu(get_account_number(account_id))

# Function to add a transaction to the database
def add_transaction(account_id, transaction_type, amount, account_number):
    cursor.execute("INSERT INTO transactions (account_id, type, amount, date) VALUES (%s, %s, %s, NOW())", (account_id, transaction_type, amount))
    db.commit()

    # Send email to user with transaction details
    cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
    user = cursor.fetchone()
    sender_email = "atmtranscation@gmail.com"
    receiver_email = user[4] # email is stored in the 4th column of the accounts table
    password ="ugqz qxtn ocrd vwuz"
    message = "Subject: Transaction Details\n\nDear " + user[1] + ",\n\nYour " + transaction_type.lower() + " of Rs." + str(amount) + " has been processed. Your current balance is Rs." + str(get_balance(account_id)) + ".\n\nThank you for using our ATM.\n\nBest regards,\nThe ATM Team"
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

# Function to get the account number from the account ID
def get_account_number(account_id):
    cursor.execute("SELECT account_number FROM accounts WHERE id = %s", (account_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

# Function to send an OTP to the user's email
def send_otp(account_number):
    cursor.execute("SELECT email FROM accounts WHERE account_number = %s", (account_number,))
    email = cursor.fetchone()[0]
    otp = str(random.randint(100000, 999999))
    subject = "ATM Withdrawal OTP"
    message = "Your OTP is: " + otp
    sender_email = "atmtranscation@gmail.com"
    sender_password ="ugqz qxtn ocrd vwuz"
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, 'Subject: {}\n\n{}'.format(subject, message))
        print("OTP sent to your email")
        return otp
    except:
        print("Failed to send email")

# Call the login menu function to start the program
login_menu()
