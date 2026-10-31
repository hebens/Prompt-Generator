import customtkinter as ctk
import json
import os

class PromptGenerator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_file = "prompt_config.json"
        self.load_config()
        
        # Initialisierung der Datenstrukturen
        self.selections = {} 
        self.placeholder_task = "Beschreibe hier deine Kern-Aufgabe..."
        self.placeholder_role = "z.B. Senior Cyber Security Analyst"
        
        self.title("AI Prompt Architect Pro - Config Edition")
        self.geometry("1000x900")
        ctk.set_appearance_mode("dark")

        self.setup_ui()
        self.update_preview()

    def load_config(self):
        """Lädt die Konfiguration oder erstellt eine Standard-Datei."""
        default_config = {
            "ai_targets": ["ChatGPT", "Claude", "Gemini", "Perplexity"],
            "sources": ["Interne Dokumentation", "Web-Suche", "Wissenschaftliche Paper", "GitHub Repos"],
            "tones": ["Akademisch", "Professionell", "Kreativ", "Technisch"],
            "formats": ["Fließtext", "Bullet Points", "Markdown Tabelle"]
        }
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Speichert die aktuelle Konfiguration in die JSON-Datei."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def setup_ui(self):
        # Tabview für Hauptmenü und Einstellungen
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_main = self.tabview.add("Prompt Builder")
        self.tab_config = self.tabview.add("Konfiguration")

        # --- TAB: PROMPT BUILDER (Zweispaltig wie zuvor) ---
        container = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Linke Seite (Inputs)
        left = ctk.CTkFrame(container)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
   
        ctk.CTkLabel(left, text="1. Rolle der KI (Persona):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.role_input = ctk.CTkEntry(left, width=600, placeholder_text=self.placeholder_role)
        self.role_input.pack(pady=(5, 15))
        self.role_input.bind("<KeyRelease>", lambda e: self.update_preview())

        ctk.CTkLabel(left, text="Aufgabe:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.task_input = ctk.CTkTextbox(left, height=120)
        self.task_input.pack(fill="x", padx=20, pady=5)
        self.task_input.insert("0.0", self.placeholder_task)
        self.task_input.bind("<KeyRelease>", lambda e: self.update_preview())
        self.task_input.bind("<FocusIn>", self.clear_placeholder)
        self.task_input.bind("<FocusOut>", self.restore_placeholder)

        # Dynamische Dropdowns aus Config
        self.create_dropdown(left, "Ziel-KI:", self.config["ai_targets"], "target")
        self.create_dropdown(left, "Quelle einbeziehen:", self.config["sources"], "source")
        self.create_dropdown(left, "Tonalität:", self.config["tones"], "tone")

        # Rechte Seite (Vorschau)
        right = ctk.CTkFrame(container, fg_color="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(right, text="Live-Vorschau", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.preview_area = ctk.CTkTextbox(right, font=("Courier New", 12))
        self.preview_area.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.copy_btn = ctk.CTkButton(right, text="Kopieren", command=self.copy_to_clipboard)
        self.copy_btn.pack(pady=15)

        # --- TAB: KONFIGURATION (Editor) ---
        ctk.CTkLabel(self.tab_config, text="JSON Konfiguration bearbeiten", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.config_editor = ctk.CTkTextbox(self.tab_config, height=400, font=("Courier New", 12))
        self.config_editor.pack(fill="both", expand=True, padx=40, pady=10)
        self.config_editor.insert("0.0", json.dumps(self.config, indent=4, ensure_ascii=False))

        save_cfg_btn = ctk.CTkButton(self.tab_config, text="Änderungen Speichern & Programm Neustarten", 
                                      fg_color="#c0392b", command=self.apply_new_config)
        save_cfg_btn.pack(pady=20)

    def clear_placeholder(self, event):
        if self.task_input.get("0.0", "end").strip() == self.placeholder_task:
            self.task_input.delete("0.0", "end")
            self.task_input.configure(text_color="white")

    def restore_placeholder(self, event):
        if not self.task_input.get("0.0", "end").strip():
            self.task_input.insert("0.0", self.placeholder_task)
            self.task_input.configure(text_color="gray")
        self.update_preview()
    
    def create_dropdown(self, parent, label_text, options, key):
        lbl = ctk.CTkLabel(parent, text=label_text)
        lbl.pack(anchor="w", padx=20, pady=(5,0))
        start_val = options[0] if (options and options[0] != "") else "Bitte wählen..."
        var = ctk.StringVar(value=start_val)
        menu = ctk.CTkOptionMenu(parent, values=options, variable=var, command=lambda x: self.update_preview())
        menu.pack(fill="x", padx=20, pady=(0, 10))
        self.selections[key] = var

    def apply_new_config(self):
        """Liest den Text aus dem Editor, validiert JSON und speichert."""
        try:
            new_data = json.loads(self.config_editor.get("0.0", "end"))
            self.config = new_data
            self.save_config()
            # Einfacher "Restart" Effekt: UI neu aufbauen oder App schließen
            print("Konfiguration aktualisiert. Bitte starten Sie die App neu für alle Änderungen.")
            self.destroy() # Schließt die App, damit die neue Config beim nächsten Start zieht
        except Exception as e:
            print(f"Fehler in der JSON-Struktur: {e}")

    def update_preview(self):
        role = self.role_input.get() or "Experte"
        task = self.task_input.get("0.0", "end").strip()
        target = self.selections["target"].get()        
        source = self.selections["source"].get()
        # Falls kein Wert gewählt oder die Liste leer ist
        if not source or source == "":
            source_display = "Keine spezifischen Quellen definiert"
        else:
            source_display = f"Genutzte Quelle(n): {source}"

        """preview = f"### SYSTEM PROMPT ({target}) ###\n" """
        preview = f"Handle als: {role}\n"
        preview += f"Primäre Quelle: {source}\n\n"
        preview += f"Aufgabe: {task}\n\n"
        preview += f"Anforderung: Nutze einen {self.selections['tone'].get()} Tonfall."
        
        self.preview_area.delete("0.0", "end")
        self.preview_area.insert("0.0", preview)

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.preview_area.get("0.0", "end"))

if __name__ == "__main__":
    app = PromptGenerator()
    app.mainloop()