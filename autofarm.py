import json
import requests
import time
import tkinter as tk
import sys

from tkinter import scrolledtext
from threading import Thread


class LeekWarsBot:
    def __init__(self, login, password, use_gui=True):
        self.login = login
        self.password = password
        self.use_gui = use_gui
        self.stop_flag = False
        self.console = None

    def generate_config(self):
        try:
            payload = {'login': self.login, 'password': self.password, 'keep_connected': 'true'}
            response = requests.post("https://leekwars.com/api/farmer/login", data=payload)
            response.raise_for_status()
            data = response.json()
            token = response.cookies.get('token')
            phpsessid = response.cookies.get('PHPSESSID')
            farmer = data['farmer']
            if token is None:
                raise Exception("[-] Unable to log in.")
            print("[+] Token and cookies retrieved.")
            return farmer, token, phpsessid
        except requests.exceptions.RequestException as e:
            self.handle_error("Connection error: " + str(e))

    def fight(self, leek_id, cookies):
        try:
            garden_response = requests.get("https://leekwars.com/api/garden/get", cookies=cookies)
            garden_response.raise_for_status()
            garden = garden_response.json()['garden']

            if garden['fights'] == 0:
                self.handle_error("You have no available fights with this leek!")
                return
            self.display_message("You have " + str(garden['max_fights']) + " available fights!")

            while garden['fights'] > 0 and not self.stop_flag:
                opponents_response = requests.get("https://leekwars.com/api/garden/get-leek-opponents/" + str(leek_id), cookies=cookies)
                opponents_response.raise_for_status()
                opponents = opponents_response.json()["opponents"]
                if not opponents:
                    break
                opponent = opponents[0]

                time.sleep(0.5)
                self.display_message("Fighting against " + opponent["name"] + " leek! (id: " + str(opponent['id']) + ")")
                fight_data = {'leek_id': str(leek_id), 'target_id': str(opponent['id'])}
                fight_response = requests.post("https://leekwars.com/api/garden/start-solo-fight", data=fight_data, cookies=cookies)
                fight_response.raise_for_status()
                self.display_message(json.dumps(fight_response.json()))
                garden['fights'] -= 1
        except requests.exceptions.RequestException as e:
            self.handle_error("Request error: " + str(e))

    def run_fights(self):
        try:
            farmer, token, phpsessid = self.generate_config()
            self.display_message("Hello " + farmer["name"] + "!")
            cookies = {'token': token, 'PHPSESSID': phpsessid}

            for leek_id, leek_info in farmer["leeks"].items():
                self.display_message("Processing leek " + leek_info["name"] + "\n")
                self.fight(leek_id, cookies)
                if self.stop_flag:
                    break
        except Exception as e:
            self.handle_error(str(e))

    def stop_program(self, start_button, stop_button):
        self.stop_flag = True
        start_button.config(state=tk.NORMAL)

    def start_program(self, login_entry, password_entry, start_button, stop_button):
        self.stop_flag = False

        self.login = login_entry.get()
        self.password = password_entry.get()
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        if self.use_gui:
            self.console.delete('1.0', tk.END)  # Clear console
        thread = Thread(target=self.run_fights)
        thread.start()

    def start_gui(self):
        window = tk.Tk()
        window.title("LeekWars")
        window.geometry("500x400")

        label = tk.Label(window, text="Welcome to Leek Wars!")
        label.pack(pady=10)

        login_label = tk.Label(window, text="Username:")
        login_label.pack()

        login_entry = tk.Entry(window)
        login_entry.pack()

        password_label = tk.Label(window, text="Password:")
        password_label.pack()

        password_entry = tk.Entry(window, show="*")
        password_entry.pack()

        self.console = scrolledtext.ScrolledText(window, height=10)
        self.console.pack(pady=10)

        button_frame = tk.Frame(window)
        button_frame.pack()

        start_button = tk.Button(button_frame, text="Start Fights",
                                 command=lambda: self.start_program(login_entry, password_entry, start_button, stop_button))
        start_button.pack(side="left", padx=5)

        stop_button = tk.Button(button_frame, text="Stop",
                                command=lambda: self.stop_program(start_button, stop_button), state=tk.DISABLED)
        stop_button.pack(side="left", padx=5)

        window.mainloop()

    def run(self):
        if self.use_gui:
            self.start_gui()
        else:
            console = None  # Use your own method for displaying information
            self.run_fights()  # Remove the 'console' argument here

    def handle_error(self, error_message):
        if self.use_gui:
            self.console.insert(tk.END, "An error occurred: " + error_message + "\n")
        else:
            print("An error occurred: " + error_message + "\n")

    def display_message(self, message):
        if self.use_gui:
            self.console.insert(tk.END, message + "\n")
        else:
            print(message)


# Example usage
bot = LeekWarsBot(login="", password="", use_gui=False)

if len(sys.argv) > 1 and sys.argv[1] == "gui":
    bot.use_gui = True

if not bot.use_gui:
    bot.login = input("Enter your username: ")
    bot.password = input("Enter your password: ")

bot.run()
