import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import json
import os
import io

# ==========================================
# CONFIGURATION
# ==========================================
JSON_PATH = "results/classement.json"
IMAGE_CACHE_DIR = "images"
OVERWATCH_ORANGE = "#f99e1a"
DARK_BG = "#212121"
DARK_PANEL = "#2b2b2b"
TEXT_COLOR = "#ffffff"

class OverwatchLeaderboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Overwatch 2 - Classement des Joueurs")
        self.root.geometry("1100x650")
        self.root.configure(bg=DARK_BG)
        
        # Initialisation
        self.data = self.load_data()
        self.portraits_urls = self.fetch_portraits_urls()
        self.current_role = None
        self.hero_images = {} # Cache en RAM pour les images
        
        os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
        
        self.setup_ui()
        self.apply_styles()

    def load_data(self):
        """Charge le fichier JSON généré par l'autre script."""
        if not os.path.exists(JSON_PATH):
            messagebox.showerror("Erreur", f"Le fichier {JSON_PATH} est introuvable.\nVeuillez d'abord générer le classement.")
            return {"Tank": {}, "Damage": {}, "Support": {}}
        
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def fetch_portraits_urls(self):
        """Récupère dynamiquement l'URL des portraits depuis l'API Overfast."""
        print("Récupération des URLs d'images...")
        try:
            resp = requests.get("https://overfast-api.tekrop.fr/heroes", timeout=5)
            if resp.status_code == 200:
                return {h['key']: h['portrait'] for h in resp.json()}
        except Exception as e:
            print(f"Erreur lors de la récupération des images : {e}")
        return {}

    def get_hero_image(self, hero_key):
        """Récupère l'image depuis le cache local, ou la télécharge si manquante."""
        img_path = os.path.join(IMAGE_CACHE_DIR, f"{hero_key}.png")
        
        if not os.path.exists(img_path) and hero_key in self.portraits_urls:
            # Téléchargement de l'image
            try:
                img_data = requests.get(self.portraits_urls[hero_key]).content
                with open(img_path, 'wb') as handler:
                    handler.write(img_data)
            except:
                return None
                
        if os.path.exists(img_path):
            img = Image.open(img_path)
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        return None

    def apply_styles(self):
        """Applique un thème sombre (Dark Mode) au tableau."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Style du Treeview (Tableau)
        style.configure("Treeview", 
                        background=DARK_PANEL, 
                        foreground=TEXT_COLOR, 
                        fieldbackground=DARK_PANEL,
                        rowheight=30,
                        font=("Segoe UI", 10))
        
        style.configure("Treeview.Heading", 
                        background=OVERWATCH_ORANGE, 
                        foreground="black", 
                        font=("Segoe UI", 10, "bold"))
                        
        style.map("Treeview", background=[('selected', '#444444')])

    def setup_ui(self):
        """Mise en place des panneaux de l'interface."""
        # --- Panneau de Gauche (Rôles) ---
        self.role_frame = tk.Frame(self.root, bg=DARK_BG, width=150)
        self.role_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(self.role_frame, text="RÔLES", bg=DARK_BG, fg=OVERWATCH_ORANGE, font=("Arial", 14, "bold")).pack(pady=10)
        
        for role in ["Tank", "Damage", "Support"]:
            btn = tk.Button(self.role_frame, text=role.upper(), bg=DARK_PANEL, fg=TEXT_COLOR, 
                            font=("Arial", 12), relief=tk.FLAT, activebackground=OVERWATCH_ORANGE,
                            command=lambda r=role: self.show_heroes(r))
            btn.pack(fill=tk.X, pady=5)

        # --- Panneau Central (Héros) ---
        self.hero_frame = tk.Frame(self.root, bg=DARK_BG, width=200)
        self.hero_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(self.hero_frame, text="HÉROS", bg=DARK_BG, fg=OVERWATCH_ORANGE, font=("Arial", 14, "bold")).pack(pady=10)
        
        # Liste avec scrollbar pour les héros
        self.hero_listbox = tk.Listbox(self.hero_frame, bg=DARK_PANEL, fg=TEXT_COLOR, font=("Arial", 12), 
                                       selectbackground=OVERWATCH_ORANGE, selectforeground="black",
                                       relief=tk.FLAT, highlightthickness=0)
        self.hero_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.hero_listbox.bind('<<ListboxSelect>>', self.on_hero_select)
        
        scrollbar = tk.Scrollbar(self.hero_frame, command=self.hero_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hero_listbox.config(yscrollcommand=scrollbar.set)

        # --- Panneau de Droite (Classement & Image) ---
        self.main_frame = tk.Frame(self.root, bg=DARK_BG)
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # En-tête (Image + Nom)
        self.header_frame = tk.Frame(self.main_frame, bg=DARK_BG)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.lbl_image = tk.Label(self.header_frame, bg=DARK_BG)
        self.lbl_image.pack(side=tk.LEFT, padx=(0, 20))
        
        self.lbl_title = tk.Label(self.header_frame, text="Sélectionnez un héros", bg=DARK_BG, fg=TEXT_COLOR, font=("Arial", 24, "bold"))
        self.lbl_title.pack(side=tk.LEFT)

        # Tableau (Treeview)
        columns = ("Rang", "Pseudo", "Score", "Temps (h)", "Winrate", "KDA", "Elims", "Assists", "Dégâts", "Soins")
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show="headings")
        
        # Configuration des colonnes
        for col in columns:
            self.tree.heading(col, text=col)
            width = 100 if col == "Pseudo" else 70
            self.tree.column(col, width=width, anchor=tk.CENTER)
            
        self.tree.pack(fill=tk.BOTH, expand=True)

    def show_heroes(self, role):
        """Affiche la liste des héros correspondant au rôle sélectionné."""
        self.current_role = role
        self.hero_listbox.delete(0, tk.END)
        
        if role in self.data:
            heroes = sorted(self.data[role].keys())
            for h in heroes:
                # Affichage propre (ex: wrecking-ball -> Wrecking Ball)
                display_name = h.replace("-", " ").title()
                self.hero_listbox.insert(tk.END, display_name)

    def on_hero_select(self, event):
        """Se déclenche lorsqu'un héros est cliqué dans la liste."""
        selection = self.hero_listbox.curselection()
        if not selection:
            return
            
        hero_display_name = self.hero_listbox.get(selection[0])
        hero_key = hero_display_name.lower().replace(" ", "-")
        
        self.update_leaderboard(hero_key, hero_display_name)

    def update_leaderboard(self, hero_key, display_name):
        """Met à jour l'image et le tableau des scores."""
        self.lbl_title.config(text=f"Classement - {display_name}")
        
        # Mise à jour de l'image
        img = self.get_hero_image(hero_key)
        if img:
            self.lbl_image.config(image=img)
            self.lbl_image.image = img # Garde une référence pour éviter le garbage collection
        else:
            self.lbl_image.config(image='')
            
        # Vider le tableau actuel
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Remplir avec les nouvelles données
        players = self.data[self.current_role].get(hero_key, [])
        for index, p in enumerate(players):
            rang = f"#{index + 1}"
            
            # Formater l'affichage de la ligne
            values = (
                rang,
                p["pseudo"],
                f"{p['score']}",
                f"{p['Temps_Jeu_Heures']}h",
                f"{p['Winrate_%']}%",
                p["KDA"],
                p["Elims_Moyenne"],
                p["Assists_Moyenne"],
                p["Degats_Moyenne"],
                p["Soins_Moyenne"]
            )
            self.tree.insert("", tk.END, values=values)

if __name__ == "__main__":
    root = tk.Tk()
    app = OverwatchLeaderboardApp(root)
    root.mainloop()