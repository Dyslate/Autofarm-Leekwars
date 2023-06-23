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
                raise Exception("[-] Impossible de se connecter.")
            print("[+] Token and cookies retrieved.")
            return farmer, token, phpsessid
        except requests.exceptions.RequestException as e:
            raise Exception("[-] Erreur de connexion : " + str(e))

    def fight(self, leek_id, cookies, console):
        try:
            garden_response = requests.get("https://leekwars.com/api/garden/get", cookies=cookies)
            garden_response.raise_for_status()
            garden = garden_response.json()['garden']

            if garden['fights'] == 0:
                if self.use_gui:
                    console.insert(tk.END, "Vous n'avez pas de combats disponibles avec ce poireau !\n")
                    return
                else:
                    print("Vous n'avez pas de combats disponibles avec ce poireau !\n")
                    return
            if self.use_gui:
                console.insert(tk.END, "Vous avez " + str(garden['max_fights']) + " combats disponibles !\n")
            else:
                print("Vous avez " + str(garden['max_fights']) + " combats disponibles !\n")
                
            while garden['fights'] > 0 and not self.stop_flag:
                opponents_response = requests.get("https://leekwars.com/api/garden/get-leek-opponents/" + str(leek_id), cookies=cookies)
                opponents_response.raise_for_status()
                opponents = opponents_response.json()["opponents"]
                if not opponents:
                    break
                opponent = opponents[0]

                time.sleep(0.5)
                if self.use_gui:
                    console.insert(tk.END, "Fighting against " + opponent["name"] + " leek ! (id: "+ str(opponent['id']) +")\n")
                else:
                    print("Fighting against " + opponent["name"] + " leek ! (id: "+ str(opponent['id']) +")\n")
                fight_data = {'leek_id': str(leek_id), 'target_id': str(opponent['id'])}
                fight_response = requests.post("https://leekwars.com/api/garden/start-solo-fight", data=fight_data, cookies=cookies)
                fight_response.raise_for_status()
                if self.use_gui:
                    console.insert(tk.END, json.dumps(fight_response.json()) + "\n")
                garden['fights'] -= 1
        except requests.exceptions.RequestException as e:
            raise Exception("[-] Erreur de requête : " + str(e))

    def run_fights(self, console):
        try:
            farmer, token, phpsessid = self.generate_config()
            if self.use_gui:
                console.insert(tk.END, "Bonjour " + farmer["name"] + " !\n")
            else:
                print("Bonjour " + farmer["name"] + " !\n")

            cookies = {'token': token, 'PHPSESSID': phpsessid}

            for leek_id, leek_info in farmer["leeks"].items():
                if self.use_gui:
                    console.insert(tk.END, "Processing leek " + leek_info["name"] + "\n")
                else:
                    print("Processing leek " + leek_info["name"] + "\n")
                self.fight(leek_id, cookies, console)
                if self.stop_flag:
                    break
        except Exception as e:
            if self.use_gui:
                console.insert(tk.END, "Une erreur s'est produite : " + str(e) + "\n")
            else:
                print("Une erreur s'est produite : " + str(e) + "\n")

    def stop_program(self, start_button, stop_button):
        self.stop_flag = True
        start_button.config(state=tk.NORMAL)

    def start_program(self, login_entry, password_entry, console, start_button, stop_button):
        self.stop_flag = False

        self.login = login_entry.get()
        self.password = password_entry.get()
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        if self.use_gui:
            console.delete('1.0', tk.END)  # Clear console
        thread = Thread(target=self.run_fights, args=(console,))
        thread.start()

    def start_gui(self):
        window = tk.Tk()
        window.title("LeekWars")
        window.geometry("500x400")

        label = tk.Label(window, text="Bienvenue sur Leek Wars !")
        label.pack(pady=10)

        login_label = tk.Label(window, text="Identifiant:")
        login_label.pack()

        login_entry = tk.Entry(window)
        login_entry.pack()

        password_label = tk.Label(window, text="Mot de passe:")
        password_label.pack()

        password_entry = tk.Entry(window, show="*")
        password_entry.pack()

        console = scrolledtext.ScrolledText(window, height=10)
        console.pack(pady=10)

        button_frame = tk.Frame(window)
        button_frame.pack()

        start_button = tk.Button(button_frame, text="Lancer les combats",
                                 command=lambda: self.start_program(login_entry, password_entry, console, start_button, stop_button))
        start_button.pack(side="left", padx=5)

        stop_button = tk.Button(button_frame, text="Arrêter",
                                command=lambda: self.stop_program(start_button, stop_button), state=tk.DISABLED)
        stop_button.pack(side="left", padx=5)

        window.mainloop()

    def run(self):
        if self.use_gui:
            self.start_gui()
        else:
            console = None  # Utilisez votre propre méthode d'affichage des informations
            self.run_fights(console)


# Exemple d'utilisation
bot = LeekWarsBot(login="", password="", use_gui=False)

if len(sys.argv) > 1 and sys.argv[1] == "gui":
    bot.use_gui = True

if not bot.use_gui:
    bot.login = input("Entrez votre identifiant : ")
    bot.password = input("Entrez votre mot de passe : ")

bot.run()