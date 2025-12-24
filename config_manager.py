import json
import os

class ConfigManager:
    def __init__(self, filename="prompt_config.json"):
        self.filename = filename
        self.config = self.load_config()

    def load_config(self):
        default_data = {
            "config":{
                "ai_targets": ["ChatGPT", "Claude", "Gemini", "Perplexity"],
                "sources": ["Interne Dokumentation", "Web-Suche", "Wissenschaftliche Paper"],
                "tones": ["Akademisch", "Professionell", "Kreativ", "Technisch"],
                "fmts": ["Fließtext", "Bullet Points", "Markdown Tabelle"],
                "lengths" : ["Kurz & Knapp", "Standard", "Ausführlich"],
                "themes": {
                    "Dracula": {
                        "header": "#ff79c6", 
                        "label": "#8be9fd", 
                        "value": "#f1fa8c", 
                        "source_empty": "#6272a4", 
                        "bg": "#282a36"
                    },
                    "Nord": {
                        "header": "#88c0d0", 
                        "label": "#81a1c1", "value": "#a3be8c", 
                        "source_empty": "#4c566a", 
                        "bg": "#2e3440"
                    }
                }
            }
        }

        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "config" not in data:
                        print("Struktur korrigiert: 'config' Key wurde hinzugefügt.")
                        return {"config": data}
                    return data
            except:
                return default_data
        return default_data

    def save(self, data=None):
        if data is not None: 
            self.config = data
        if not self.config or self.config == "null":
            print("Abbruch: Versuch, leere Daten zu speichern wurde verhindert.")
            return
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Konfiguration erfolgreich gespeichert.")

        except Exception as e:
            print(f"Fehler beim Schreiben der Datei: {e}")

    def add_item(self, category, item):
        if category in self.config and item not in self.config[category]:
            self.config[category].append(item)
            self.save()    