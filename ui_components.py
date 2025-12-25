import customtkinter as ctk
import json
from tkinter import messagebox
import re
import os
from prompt_logic import PromptEngine

# Definition der Themes für das Syntax-Highlighting
THEMES = {
    "Dracula": {
        "header": "#ff79c6", "label": "#8be9fd", "value": "#f1fa8c", 
        "source_empty": "#6272a4", "bg": "#282a36"
    },
    "Nord": {
        "header": "#88c0d0", "label": "#81a1c1", "value": "#a3be8c", 
        "source_empty": "#4c566a", "bg": "#2e3440"
    },
    "Monokai": {
        "header": "#f92672", "label": "#66d9ef", "value": "#e6db74", 
        "source_empty": "#75715e", "bg": "#272822"
    }
}

class PromptApp(ctk.CTk):
    def __init__(self, config_manager):
        super().__init__()
        self.cm = config_manager

        self.selections = {}
        self.dropdown_widgets = {}
        
        self.placeholder_task = "Beschreibe hier deine Kern-Aufgabe..."
        self.placeholder_role = "z.B. Security Analyst"
        
        self.title("AI Prompt Architect Pro 2025")
        self.geometry("1200x900")
        ctk.set_appearance_mode("dark")

        self.setup_ui()
        # Initiales Theme anwenden und Vorschau laden
        themes_dict = self.cm.config.get("themes", {})
        themes_list = list(themes_dict.keys())
        if themes_list:
                self.apply_theme(themes_list[0])

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tab_main = self.tabview.add("Prompt Builder")
        self.tab_config = self.tabview.add("Konfiguration")

        # --- TAB: PROMPT BUILDER ---
        container = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Linke Spalte
        left_p = ctk.CTkFrame(container, width=450)
        left_p.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(left_p, text="1. Rolle & Aufgabe", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
        self.role_input = ctk.CTkEntry(left_p, placeholder_text=self.placeholder_role)
        self.role_input.pack(fill="x", padx=20, pady=5)
        self.role_input.bind("<KeyRelease>", lambda e: self.update_preview())

        self.task_input = ctk.CTkTextbox(left_p, height=150)
        self.task_input.pack(fill="x", padx=20, pady=5)
        self.task_input.insert("0.0", self.placeholder_task)
        self.task_input.bind("<FocusIn>", self.clear_placeholder)
        self.task_input.bind("<FocusOut>", self.restore_placeholder)
        self.task_input.bind("<KeyRelease>", lambda e: self.update_preview())

        if "config" not in self.cm.config:
            messagebox.showerror("Fehler", "Die Konfigurationsstruktur ist beschädigt!")
            return

        conf = self.cm.config["config"] # Lokale Referenz für kürzeren Code

        # Dropdowns
        self.create_dropdown(left_p, "Ziel-KI:", conf["ai_targets"], "target")
        #self.create_dropdown(left_p, "Quelle:", self.cm.config["sources"], "source")
        self.create_dropdown(left_p, "Tonalität:", conf["tones"], "tone")
        self.create_dropdown(left_p, "Format:", conf["fmts"], "fmt")
        self.create_dropdown(left_p, "Umfang:", conf["lengths"], "length")

        ctk.CTkLabel(left_p, text="Quellen auswählen:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
        # Frame für die Checkboxen
        self.source_frame = ctk.CTkScrollableFrame(left_p, height=40)
        self.source_frame.pack(fill="x", padx=20, pady=5)
        
        self.source_vars = {} # Speichert die BooleanVars der Checkboxen
        self.rebuild_source_list()

        self.pdf_btn = ctk.CTkButton(left_p, text="+ PDF Dokument laden", 
                                     command=self.load_pdf_as_source,
                                     fg_color="#e67e22")
        self.pdf_btn.pack(pady=5, padx=20, fill="x")
        
        # Speicher für PDF-Inhalte
        self.pdf_vault = {}

        # In setup_ui (Linke Spalte) unter dem pdf_btn:
        self.progress_bar = ctk.CTkProgressBar(left_p, orientation="horizontal", mode="determinate")
        self.progress_bar.pack(pady=5, padx=20, fill="x")
        self.progress_bar.set(0) # Start bei 0%
        
        # Ein Label für den Status-Text (optional)
        self.status_label = ctk.CTkLabel(left_p, text="Bereit", font=ctk.CTkFont(size=10))
        self.status_label.pack(pady=0)
        
        # Theme Selector
        ctk.CTkLabel(left_p, text="Vorschau Theme:").pack(anchor="w", padx=20, pady=(10,0))
        # Holt die Keys direkt aus der Config
        theme_names = list(conf["themes"].keys())
        self.theme_menu = ctk.CTkOptionMenu(left_p, values=theme_names, command=self.apply_theme)
        self.theme_menu.pack(fill="x", padx=20, pady=(0, 10))

        # Rechte Spalte (Vorschau)
        right_p = ctk.CTkFrame(container, fg_color="#1a1a1a")
        right_p.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(right_p, text="Live-Vorschau (Syntax Highlighted)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.preview_area = ctk.CTkTextbox(right_p, font=("Courier New", 13), wrap="word")
        self.preview_area.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Tags für Highlighting konfigurieren
        self.preview_area.tag_config("header", foreground="#ff79c6")
        self.preview_area.tag_config("label", foreground="#8be9fd")
        self.preview_area.tag_config("value", foreground="#f1fa8c")
        self.preview_area.tag_config("fmt", foreground="#90e1dc")
        self.preview_area.tag_config("length", foreground="#9E9F9D")
        self.preview_area.tag_config("source_empty", foreground="#6272a4")

        # Rechte Spalte (Vorschau-Bereich)
        self.copy_btn = ctk.CTkButton(right_p, text="Prompt Kopieren", command=self.copy_to_clipboard, fg_color="#27ae60")
        self.copy_btn.pack(pady=(20, 5)) # Kleinerer Abstand nach unten

        # NEU: Der Library-Speicher-Button
        self.library_btn = ctk.CTkButton(
            right_p, 
            text="In Library archivieren", 
            command=self.export_to_library, 
            fg_color="#2980b9", # Ein schönes Blau
            hover_color="#3498db"
        )
        self.library_btn.pack(pady=5)

        # --- TAB: KONFIGURATION ---
        self.setup_config_tab()

    def setup_config_tab(self):
        # Quick-Add Section
        add_frame = ctk.CTkLabel(self.tab_config, text="Schnell-Hinzufügen", font=ctk.CTkFont(weight="bold"))
        add_frame.pack(pady=(10,0))
        
        row = ctk.CTkFrame(self.tab_config, fg_color="transparent")
        row.pack(fill="x", padx=40, pady=10)
        
        self.new_item_entry = ctk.CTkEntry(row, placeholder_text="Name des Eintrags...")
        self.new_item_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        self.cat_select = ctk.CTkOptionMenu(row, values=["ai_targets", "sources", "tones", "fmts"])
        self.cat_select.pack(side="left", padx=5)
        
        ctk.CTkButton(row, text="+", width=40, command=self.quick_add).pack(side="left", padx=5)

        # JSON Editor
        ctk.CTkLabel(self.tab_config, text="JSON Rohdaten Editor", font=ctk.CTkFont(size=14)).pack(pady=(20,0))
        self.config_editor = ctk.CTkTextbox(self.tab_config, height=400, corner_radius=5, font=("Courier New", 12))
        self.config_editor.pack(fill="both", expand=True, padx=40, pady=10)
        self.refresh_editor_text()

        ctk.CTkButton(self.tab_config, text="JSON Speichern & UI Refresh", 
                     fg_color="#c0392b", command=self.save_json_and_refresh).pack(pady=10)

    def create_dropdown(self, parent, label_text, options, key):
        lbl = ctk.CTkLabel(parent, text=label_text)
        lbl.pack(anchor="w", padx=20, pady=(5,0))
        var = ctk.StringVar(value=options[0] if options else "")
        menu = ctk.CTkOptionMenu(parent, values=options, variable=var, command=lambda x: self.update_preview())
        menu.pack(fill="x", padx=20, pady=(0, 10))
        self.selections[key] = var
        self.dropdown_widgets[key] = menu

    def apply_theme(self, theme_name):
        try:
            colors = self.cm.conf["themes"].get(theme_name)
            if not colors: 
                print(f"Theme {theme_name} nicht in prompt_config gefunden.")
                return
            self.preview_area.configure(fg_color=colors["bg"])

            self.preview_area.tag_config("header", foreground=colors.get("header", "#ffffff"))
            self.preview_area.tag_config("label", foreground=colors.get("label", "#888888"))
            self.preview_area.tag_config("value", foreground=colors.get("value", "#cccccc"))
            self.preview_area.tag_config("length", foreground=colors.get("value", "#458979"))
            self.preview_area.tag_config("fmt", foreground=colors.get("value", "#5b7c89"))                        
            self.preview_area.tag_config("source_empty", foreground=colors.get("source_empty", "#555555"))           
            self.update_preview()

        except KeyError:
            print("Fehler: Die JSON-Struktur 'themes' wurde nicht gefunden.")

    def update_preview(self, *args):
        try:
            # 1. Daten aus der UI sammeln
            target = self.selections["target"].get() if "target" in self.selections else "ChatGPT"
            role = self.role_input.get().strip()
            task = self.task_input.get("0.0", "end").strip()
            if task == self.placeholder_task: task = ""
            tone = self.selections["tone"].get() if "tone" in self.selections else "Standard"
            fmt = self.selections["fmt"].get() if "fmt" in self.selections else "Fließtext"
            length = self.selections["length"].get() if "length" in self.selections else "Standard"
            source = self.selections["source"].get() if "source" in self.selections else ""
           
            # Multi-Quellen auslesen
            selected_sources = [name for name, var in self.source_vars.items() if var.get()]
            # Wenn keine gewählt ist, übergeben wir einen leeren String oder "Keine"
            sources_string = ", ".join(selected_sources) if selected_sources else ""

            context_parts = []
            for src in selected_sources:
                if src in self.pdf_vault:
                    # Inhalt aus PDF hinzufügen
                    context_parts.append(f"INHALT AUS DATEI '{src}':\n{self.pdf_vault[src]}")
                else:
                    # Nur den Namen der Standard-Quelle
                    context_parts.append(src)

            source_string = "\n---\n".join(context_parts) if context_parts else ""
            source_string = source_string + ";" + sources_string
            # Engine aufrufen (der 4. Parameter ist nun unser kombinierter String)
            final_prompt = PromptEngine.build(
                target, role, task, source_string, tone, fmt, length
            )

            # 2. Den "rohen" Prompt über die Engine bauen lassen
            #final_prompt = PromptEngine.build(target, role, task, source, tone, fmt, length)

            # 3. Das Textfeld leeren und neu befüllen
            self.preview_area.delete("0.0", "end")
            
            # Den Prompt einfügen:
            self.preview_area.insert("end", final_prompt)

            self.apply_highlighting_tags(target)

        
        except KeyError as e:
            # Falls ein Key in self.selections noch nicht existiert (beim Start)
            print(f"Fehler in update_preview: {e}")

    def quick_add(self):
        val = self.new_item_entry.get().strip()
        cat = self.cat_select.get()
        if val:
            self.cm.add_item(cat, val)
            self.new_item_entry.delete(0, 'end')
            self.refresh_ui_from_config()

    def apply_highlighting_tags(self, target):
        # Beispiel: Markiere die Zeilen, die mit Großbuchstaben und Doppelpunkt enden
        
        KEYWORDS = ["Aufgabe", "Format", "Länge", "Tonalität", "else", "for", "while"]
        
        self.preview_area.tag_add("header", "1.0", "1.end") # Die erste Zeile immer als Header
        #self.preview_area.tag_add("Aufgabe:",start, end)
        content = self.preview_area.get("1.0", "end")

        for m in re.finditer(r"(ROLLE|AUFGABE|QUELLE|PARAMETER|FORMAT|TON):", content):
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            self.preview_area.tag_add("label", start, end)

        """
            self.preview_area.insert("end", "ROLLE: ", "header")
            self.preview_area.insert("end", f"{role}\n", "value")
            
            self.preview_area.insert("end", "QUELLE: ", "label")
            if not source:
                self.preview_area.insert("end", "Keine spezifischen Quellen definiert\n", "source_empty")
            else:
                self.preview_area.insert("end", f"{source}\n", "value")

            self.preview_area.insert("end", "\nAUFGABE:\n", "label")
            self.preview_area.insert("end", f"{task}\n\n", "value")

            self.preview_area.insert("end", "TON: ", "label")
            self.preview_area.insert("end", f"{tone}\n", "value")

            self.preview_area.insert("end", "Länge: ", "label")
            self.preview_area.insert("end", f"{length}\n", "value")

            self.preview_area.insert("end", "FORMAT: ", "label")
            self.preview_area.insert("end", f"{fmt}\n","value")"""

    def save_json_and_refresh(self):
        try:
            #new_cfg = json.loads(self.config_editor.get("0.0", "end"))
            raw_text = self.config_editor.get("0.0", "end").strip()
            # self.cm.config = new_cfg
            new_cfg = json.loads(raw_text)
            if "config" not in new_cfg:
                new_cfg = {"config": new_cfg}
            self.cm.save(new_cfg)
            self.refresh_ui_from_config()
            messagebox.showinfo("Erfolg", "Konfiguration aktualisiert!")
        except json.JSONException as e:
            messagebox.showerror("JSON Fehler", f"Ungültiges JSON: {e}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")

    def refresh_ui_from_config(self):
        conf = self.cm.config["config"]
        mapping = {"target": "ai_targets", 
                   "source": "sources", 
                   "tone": "tones", 
                   "format": "fmts"}
        for key, cfg_key in mapping.items():
            if key in self.dropdown_widgets:
                new_opts = conf.get(cfg_key, [])
                self.dropdown_widgets[key].configure(values=new_opts)
                if new_opts:
                    self.selections[key].set(new_opts[0])
            """new_opts = self.cm.config.get(cfg_key, [])
            self.dropdown_widgets[key].configure(values=new_opts)"""
        self.rebuild_source_list()
        self.refresh_editor_text()
        self.update_preview()
        messagebox.showinfo("Update", "Die UI und Quellen wurden aktualisiert!")

    def refresh_editor_text(self):
        self.config_editor.delete("0.0", "end")
        self.config_editor.insert("0.0", json.dumps(self.cm.config, indent=4, ensure_ascii=False))

    def clear_placeholder(self, event):
        if self.task_input.get("0.0", "end").strip() == self.placeholder_task:
            self.task_input.delete("0.0", "end")

    def restore_placeholder(self, event):
        if not self.task_input.get("0.0", "end").strip():
            self.task_input.insert("0.0", self.placeholder_task)

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.preview_area.get("0.0", "end"))
        self.copy_btn.configure(text="✓ Kopiert", fg_color="#2ecc71")
        self.after(1500, lambda: self.copy_btn.configure(text="Prompt Kopieren", fg_color="#27ae60"))

    def export_to_library(self):
        import os
        from datetime import datetime
        
        # 1. Pfad sicherstellen
        lib_path = "library"
        if not os.path.exists(lib_path):
            os.makedirs(lib_path)
            
        # 2. Dateinamen generieren (basierend auf Rolle und Zeit)
        role = self.role_input.get().strip() or "Universal"
        # Dateiname von Sonderzeichen säubern
        clean_role = "".join(x for x in role if x.isalnum() or x in (" ", "_")).replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{lib_path}/{timestamp}_{clean_role}.md"
        
        # 3. Inhalt aus der Preview-Area holen
        content = self.preview_area.get("0.0", "end").strip()
        
        if not content or content == self.placeholder_task:
            messagebox.showwarning("Leerer Prompt", "Es gibt keinen Inhalt zum Speichern!")
            return

        # 4. Datei schreiben
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Feedback an den User
            messagebox.showinfo("Erfolg", f"Prompt erfolgreich archiviert:\n{filename}")
            
            # Button kurzzeitig als Erfolg markieren
            self.library_btn.configure(text="✓ Archiviert", fg_color="#2ecc71")
            self.after(2000, lambda: self.library_btn.configure(text="In Library archivieren", fg_color="#2980b9"))
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {str(e)}")

    def rebuild_source_list(self):
        # Bestehende Checkboxen löschen
        conf = self.cm.config["config"]
        for widget in self.source_frame.winfo_children():
            widget.destroy()
        
        self.source_vars = {}
        # Quellen aus der Config laden self.cm.config["config"]
        for src in conf["sources"]:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self.source_frame, text=src, variable=var, 
                                 command=lambda: self.update_preview())
            cb.pack(anchor="w", padx=5, pady=2)
            self.source_vars[src] = var 

    def load_pdf_as_source(self):
        from tkinter import filedialog
        import threading
        
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return
            
        # UI vorbereiten
        self.pdf_btn.configure(state="disabled")
        self.status_label.configure(text="Lese PDF ein...")
        self.progress_bar.set(0)
        
        # Thread starten, damit die UI nicht einfriert
        thread = threading.Thread(target=self._pdf_worker, args=(file_path,))
        thread.start()

    def _pdf_worker(self, file_path):
        import PyPDF2
        import re
        import os
        
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                total_pages = min(len(reader.pages), 10) # Wir lesen max 10 Seiten
                raw_text = ""
                
                for i in range(total_pages):
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        raw_text += page_text + " "
                    
                    # Progress-Bar aktualisieren (muss in 0.0 bis 1.0 angegeben werden)
                    progress = (i + 1) / total_pages
                    self.after(0, lambda p=progress: self.progress_bar.set(p))
                
                # Text-Bereinigung (Fließtext-Logik)
                clean_text = re.sub(r'\s+', ' ', raw_text.replace('\n', ' ')).strip()
                self.pdf_vault[file_name] = clean_text[:5000] # Cap bei 5000 Zeichen

                # UI-Update nach Erfolg (muss über .after laufen, da Thread-sicher)
                self.after(0, lambda: self._finalize_pdf_load(file_name))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Fehler", f"PDF-Fehler: {e}"))
            self.after(0, lambda: self.pdf_btn.configure(state="normal"))