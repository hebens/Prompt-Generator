from config_manager import ConfigManager
from ui_components import PromptApp

def main():
    
    #try:
        cm = ConfigManager()
        app = PromptApp(cm)
        app.mainloop()

    #except Exception as e:
    #    print(f"Kritischer Fehler beim Starten: {e}")

if __name__ == "__main__":
    main()