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
        self.var_inputs = {}
        self.var_values = {}
        
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
        self.tab_library = self.tabview.add("Bibliothek")
        self.tab_config = self.tabview.add("Konfiguration")

        # --- TAB: PROMPT BUILDER ---
        container = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Linke Spalte als CTkScrollableFrame (SCROLLBAR GEMACHT)
        left_p = ctk.CTkScrollableFrame(container, width=450)
        left_p.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(left_p, text="1. Rolle & Aufgabe", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
        self.role_input = ctk.CTkEntry(left_p, placeholder_text=self.placeholder_role)
        self.role_input.pack(fill="x", padx=20, pady=5)
        self.role_input.bind("<KeyRelease>", lambda e: self.update_preview())

        self.task_input = ctk.CTkTextbox(left_p, height=140)
        self.task_input.pack(fill="x", padx=20, pady=5)
        self.task_input.insert("0.0", self.placeholder_task)
        self.task_input.bind("<FocusIn>", self.clear_placeholder)
        self.task_input.bind("<FocusOut>", self.restore_placeholder)
        self.task_input.bind("<KeyRelease>", lambda e: self.update_preview())

        # Frame für dynamische Variablen-Eingaben
        self.vars_frame = ctk.CTkFrame(left_p, fg_color="transparent")
        self.vars_frame.pack(fill="x", padx=20, pady=(5, 0))

        if "config" not in self.cm.config:
            messagebox.showerror("Fehler", "Die Konfigurationsstruktur ist beschädigt!")
            return

        conf = self.cm.config["config"]

        # Dropdowns
        self.create_dropdown(left_p, "Ziel-KI:", conf["ai_targets"], "target")
        self.create_dropdown(left_p, "Tonalität:", conf["tones"], "tone")
        self.create_dropdown(left_p, "Format:", conf["fmts"], "fmt")
        self.create_dropdown(left_p, "Umfang:", conf["lengths"], "length")

        ctk.CTkLabel(left_p, text="Quellen auswählen:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
        
        # Frame für die Checkboxen
        self.source_frame = ctk.CTkFrame(left_p, fg_color="transparent")
        self.source_frame.pack(fill="x", padx=20, pady=5)
        
        self.source_vars = {}
        self.rebuild_source_list()

        # Klickbare PDF-Dropzone
        self.drop_frame = ctk.CTkFrame(left_p, fg_color="#2b2b2b", border_color="#e67e22", border_width=1)
        self.drop_frame.pack(fill="x", padx=20, pady=5)

        lbl_icon = ctk.CTkLabel(self.drop_frame, text="📄 PDF Dokument auswählen", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_icon.pack(pady=(10, 2))

        lbl_sub = ctk.CTkLabel(self.drop_frame, text="Klicken, um Datei auszuwählen", font=ctk.CTkFont(size=10), text_color="gray")
        lbl_sub.pack(pady=(0, 10))

        for widget in (self.drop_frame, lbl_icon, lbl_sub):
            widget.bind("<Button-1>", lambda e: self.load_pdf_as_source())
            widget.configure(cursor="hand2")   

        self.pdf_vault = {}

        self.progress_bar = ctk.CTkProgressBar(left_p, orientation="horizontal", mode="determinate")
        self.progress_bar.pack(pady=5, padx=20, fill="x")
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="#e67e22")
        
        self.status_label = ctk.CTkLabel(left_p, text="Bereit", font=ctk.CTkFont(size=10))
        self.status_label.pack(pady=0)
        
        # Theme Selector
        ctk.CTkLabel(left_p, text="Vorschau Theme:").pack(anchor="w", padx=20, pady=(10,0))
        theme_names = list(conf["themes"].keys())
        self.theme_menu = ctk.CTkOptionMenu(left_p, values=theme_names, command=self.apply_theme)
        self.theme_menu.pack(fill="x", padx=20, pady=(0, 10))

        # Rechte Spalte (Vorschau)
        right_p = ctk.CTkFrame(container, fg_color="#1a1a1a")
        right_p.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(right_p, text="Live-Vorschau (Syntax Highlighted)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.preview_area = ctk.CTkTextbox(right_p, font=("Courier New", 13), wrap="word")
        self.preview_area.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.preview_area.tag_config("header", foreground="#ff79c6")
        self.preview_area.tag_config("label", foreground="#8be9fd")
        self.preview_area.tag_config("value", foreground="#f1fa8c")
        self.preview_area.tag_config("fmt", foreground="#90e1dc")
        self.preview_area.tag_config("length", foreground="#9E9F9D")
        self.preview_area.tag_config("source_empty", foreground="#6272a4")

        self.stats_label = ctk.CTkLabel(
            right_p, 
            text="Wörter: 0 | Zeichen: 0 | Tokens (ca.): 0", 
            font=ctk.CTkFont(family="Courier New", size=11),
            text_color="#888888"
        )
        self.stats_label.pack(anchor="e", padx=15, pady=(2, 5))

        self.copy_btn = ctk.CTkButton(right_p, text="Prompt Kopieren", command=self.copy_to_clipboard, fg_color="#27ae60")
        self.copy_btn.pack(pady=(20, 5))

        self.library_btn = ctk.CTkButton(
            right_p, 
            text="In Library archivieren", 
            command=self.export_to_library, 
            fg_color="#2980b9",
            hover_color="#3498db"
        )
        self.library_btn.pack(pady=5)

        self.setup_config_tab()
        self.setup_library_tab()

    def update_variable_fields(self, task_text):
        if task_text == self.placeholder_task:
            task_text = ""

        # Findet Variablen wie {unternehmen}, {sprache} etc.
        found_vars = list(dict.fromkeys(re.findall(r"\{([a-zA-Z0-9_]+)\}", task_text)))

        # 1. Gelöschte Variablen entfernen
        current_vars = list(self.var_inputs.keys())
        for var_name in current_vars:
            if var_name not in found_vars:
                self.var_inputs[var_name]["frame"].destroy()
                del self.var_inputs[var_name]

        # 2. Neue Variablen-Inputfelder aufbauen
        for var_name in found_vars:
            if var_name not in self.var_inputs:
                row_frame = ctk.CTkFrame(self.vars_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=3)

                lbl = ctk.CTkLabel(
                    row_frame, 
                    text=f"{{{var_name}}}:", 
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#e67e22"
                )
                lbl.pack(side="left", padx=(0, 5))

                entry = ctk.CTkEntry(row_frame, placeholder_text=f"Wert für {var_name}...")
                entry.pack(side="right", fill="x", expand=True)
                entry.bind("<KeyRelease>", lambda e: self.update_preview())

                self.var_inputs[var_name] = {
                    "frame": row_frame,
                    "entry": entry
                }

    def update_preview(self, *args):
        try:
            target_var = self.selections.get("target")
            target = target_var.get() if target_var else "ChatGPT"
            
            role = self.role_input.get().strip()
            
            raw_task = self.task_input.get("0.0", "end").strip()
            
            # 1. Dynamische Variablen-Inputfelder synchronisieren
            self.update_variable_fields(raw_task)

            # Prüfen ob Platzhalter noch drin steht
            display_task = "" if raw_task == self.placeholder_task else raw_task

            # 2. Platzhalter {variable} durch Benutzereingaben ersetzen
            for var_name, data in self.var_inputs.items():
                val = data["entry"].get().strip()
                replacement = val if val else f"{{{var_name}}}"
                display_task = display_task.replace(f"{{{var_name}}}", replacement)

            tone_var = self.selections.get("tone")
            tone = tone_var.get() if tone_var else "Standard"
            
            fmt_var = self.selections.get("format")
            fmt = fmt_var.get() if fmt_var else "Fließtext"
            
            len_var = self.selections.get("length")
            length = len_var.get() if len_var else "Standard"

            context_parts = []
            seen_sources = set()

            items = list(self.source_vars.items())
            for name, var in items:
                if var.get():
                    if name not in seen_sources:
                        if name in self.pdf_vault:
                            content = self.pdf_vault[name]
                            context_parts.append(f"--- DOKUMENT: {name} ---\n{content}")
                        else:
                            context_parts.append(f"Quelle: {name}")
                        seen_sources.add(name)

            source_string = "\n\n".join(context_parts) if context_parts else ""

            final_prompt = PromptEngine.build(
                target, role, display_task, source_string, tone, fmt, length
            )

            self.preview_area.delete("0.0", "end")
            self.preview_area.insert("0.0", final_prompt)

            self.apply_highlighting_tags(target)

            text_length = len(final_prompt.strip())
            words_count = len(final_prompt.split())
            approx_tokens = int(text_length / 4) if text_length > 0 else 0

            self.stats_label.configure(
                text=f"Wörter: {words_count} | Zeichen: {text_length} | Tokens (ca.): {approx_tokens}"
            )
        except Exception as e:
            print(f"KRITISCHER FEHLER in update_preview: {e}")

    def clear_placeholder(self, event):
        if self.task_input.get("0.0", "end").strip() == self.placeholder_task:
            self.task_input.delete("0.0", "end")
            self.update_preview()

    def restore_placeholder(self, event):
        if not self.task_input.get("0.0", "end").strip():
            self.task_input.insert("0.0", self.placeholder_task)
            self.update_preview()

    def setup_config_tab(self):
        add_frame = ctk.CTkLabel(self.tab_config, text="Schnell-Hinzufügen", font=ctk.CTkFont(weight="bold"))
        add_frame.pack(pady=(10,0))
        
        row = ctk.CTkFrame(self.tab_config, fg_color="transparent")
        row.pack(fill="x", padx=40, pady=10)
        
        self.new_item_entry = ctk.CTkEntry(row, placeholder_text="Name des Eintrags...")
        self.new_item_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        self.cat_select = ctk.CTkOptionMenu(row, values=["ai_targets", "sources", "tones", "fmts"])
        self.cat_select.pack(side="left", padx=5)
        
        ctk.CTkButton(row, text="+", width=40, command=self.quick_add).pack(side="left", padx=5)

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
            self.preview_area.tag_config("fmt", foreground=colors.get("value", "#5b7c89"))                        
            self.preview_area.tag_config("source_empty", foreground=colors.get("source_empty", "#555555"))           
            self.update_preview()

        except KeyError:
            print("Fehler: Die JSON-Struktur 'themes' wurde nicht gefunden.")

    def quick_add(self):
        val = self.new_item_entry.get().strip()
        cat = self.cat_select.get()
        if val:
            self.cm.add_item(cat, val)
            self.new_item_entry.delete(0, 'end')
            self.refresh_ui_from_config()

    def apply_highlighting_tags(self, target):
        self.preview_area.tag_add("header", "1.0", "1.end")
        content = self.preview_area.get("1.0", "end")

        for m in re.finditer(r"(ROLLE|AUFGABE|QUELLE|PARAMETER|FORMAT|TON):", content):
            start = f"1.0 + {m.start()} chars"
            end = f"1.0 + {m.end()} chars"
            self.preview_area.tag_add("label", start, end)

    def save_json_and_refresh(self):
        try:
            raw_text = self.config_editor.get("0.0", "end").strip()
            new_cfg = json.loads(raw_text)
            if "config" not in new_cfg:
                new_cfg = {"config": new_cfg}
            self.cm.save(new_cfg)
            self.refresh_ui_from_config()
            messagebox.showinfo("Erfolg", "Konfiguration aktualisiert!")
        except json.JSONDecodeError as e:
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
        self.rebuild_source_list()
        self.refresh_editor_text()
        self.update_preview()
        messagebox.showinfo("Update", "Die UI und Quellen wurden aktualisiert!")

    def refresh_editor_text(self):
        self.config_editor.delete("0.0", "end")
        self.config_editor.insert("0.0", json.dumps(self.cm.config, indent=4, ensure_ascii=False))

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.preview_area.get("0.0", "end"))
        self.copy_btn.configure(text="✓ Kopiert", fg_color="#2ecc71")
        self.after(1500, lambda: self.copy_btn.configure(text="Prompt Kopieren", fg_color="#27ae60"))

    def export_to_library(self):
        lib_path = "library"
        if not os.path.exists(lib_path):
            os.makedirs(lib_path)
            
        role = self.role_input.get().strip() or "Universal"
        clean_role = "".join(x for x in role if x.isalnum() or x in (" ", "_")).replace(" ", "_")
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{lib_path}/{timestamp}_{clean_role}.md"
        
        content = self.preview_area.get("0.0", "end").strip()
        
        if not content or content == self.placeholder_task:
            messagebox.showwarning("Leerer Prompt", "Es gibt keinen Inhalt zum Speichern!")
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            messagebox.showinfo("Erfolg", f"Prompt erfolgreich archiviert:\n{filename}")
            
            self.library_btn.configure(text="✓ Archiviert", fg_color="#2ecc71")
            self.after(2000, lambda: self.library_btn.configure(text="In Library archivieren", fg_color="#2980b9"))
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {str(e)}")

    def rebuild_source_list(self):
        conf = self.cm.config["config"]
        for widget in self.source_frame.winfo_children():
            widget.destroy()
        
        self.source_vars = {}
        for src in conf["sources"]:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self.source_frame, text=src, variable=var, 
                                 command=lambda: self.update_preview())
            cb.pack(anchor="w", padx=5, pady=2)
            self.source_vars[src] = var 

    def ask_page_range(self):
        dialog = ctk.CTkInputDialog(text="Seitenbereich eingeben (z.B. 1-3 oder 5):\nLeer lassen für alle (max. 15)", title="PDF Seiten")
        return dialog.get_input()
    
    def load_pdf_as_source(self):
        from tkinter import filedialog
        import threading
        
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return
            
        page_range_str = self.ask_page_range()    

        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_in_pdf = len(reader.pages)
                requested_pages = self._parse_pages(page_range_str, total_in_pdf)
                
                if len(requested_pages) > 20:
                    answer = messagebox.askyesno("Warnung", 
                        f"Du versuchst {len(requested_pages)} Seiten zu laden. "
                        "Das könnte den Prompt zu groß für die KI machen. Fortfahren?")
                    if not answer:
                        return
        except Exception as e:
            print(f"Vorab-Check fehlgeschlagen: {e}")

        self.status_label.configure(text="Lese PDF ein...")
        self.progress_bar.set(0)
        
        thread = threading.Thread(target=self._pdf_worker, args=(file_path, page_range_str))
        thread.start()

    def _parse_pages(self, range_str, max_pages):
        pages = []
        try:
            if not range_str or range_str.strip() == "":
                return list(range(min(max_pages, 10)))
            
            if "-" in range_str:
                start, end = map(int, range_str.split("-"))
                for p in range(start-1, end):
                    if 0 <= p < max_pages:
                        pages.append(p)
            else:
                p = int(range_str) - 1
                if 0 <= p < max_pages:
                    pages.append(p)
        except:
            return list(range(min(max_pages, 10)))
        return pages

    def _pdf_worker(self, file_path, page_range_str):
        import PyPDF2
        import re
        
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                total_in_pdf = len(reader.pages)
                
                target_pages = self._parse_pages(page_range_str, total_in_pdf)
                
                raw_text = ""
                for idx, p_num in enumerate(target_pages):
                    page_text = reader.pages[p_num].extract_text()
                    if page_text:
                        raw_text += f"\n[Seite {p_num+1}]\n" + page_text + " "
                    
                    progress = (idx + 1) / len(target_pages)
                    self.after(0, lambda p=progress: self.progress_bar.set(p))
                
                clean_text = re.sub(r'\s+', ' ', raw_text.replace('\n', ' ')).strip()
                display_name = f"{file_name} (S.{page_range_str})" if page_range_str else file_name
                self.pdf_vault[display_name] = clean_text
                
                self.after(0, lambda: self._finalize_pdf_load(display_name))
                
        except Exception as e:
            def handle_error():
                self.progress_bar.configure(progress_color="#e74c3c")
                self.status_label.configure(text="Fehler!", text_color="#e74c3c")
                self.after(0, lambda: messagebox.showerror("Fehler", f"PDF-Bereich Fehler: {e}"))
                self.after(3000, self._reset_progress_ui)
            self.after(0, handle_error)

    def _finalize_pdf_load(self, file_name):
        var = ctk.BooleanVar(value=True)
        cb = ctk.CTkCheckBox(self.source_frame, text=f"📄 {file_name}", 
                                variable=var, command=lambda: self.update_preview())
        cb.pack(anchor="w", padx=5, pady=2)
        self.source_vars[file_name] = var
            
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color="#2ecc71")
        self.status_label.configure(text="Abgeschlossen!", text_color="#2ecc71")
            
        self.update_preview()
        self.after(3000, self._reset_progress_ui)

    def _reset_progress_ui(self):
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color="#e67e22")
        self.status_label.configure(text="Bereit", text_color=["black", "white"])

    def setup_library_tab(self):
        top_bar = ctk.CTkFrame(self.tab_library, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(top_bar, placeholder_text="Bibliothek durchsuchen...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_library_list())

        ctk.CTkButton(top_bar, text="🔄 Aktualisieren", width=110, command=self.refresh_library_list).pack(side="right")

        content_frame = ctk.CTkFrame(self.tab_library, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.lib_file_list = ctk.CTkScrollableFrame(content_frame, width=300)
        self.lib_file_list.pack(side="left", fill="both", padx=(0, 10))

        right_view = ctk.CTkFrame(content_frame)
        right_view.pack(side="right", fill="both", expand=True)

        self.lib_preview = ctk.CTkTextbox(right_view, font=("Courier New", 12), wrap="word")
        self.lib_preview.pack(fill="both", expand=True, padx=10, pady=10)

        action_bar = ctk.CTkFrame(right_view, fg_color="transparent")
        action_bar.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(action_bar, text="In Zwischenablage kopieren", fg_color="#27ae60", 
                      command=lambda: self.copy_text_to_clipboard(self.lib_preview.get("0.0", "end"))).pack(side="left", padx=5)
        
        ctk.CTkButton(action_bar, text="🗑 Löschen", fg_color="#c0392b", 
                      command=self.delete_selected_library_file).pack(side="right", padx=5)

        self.current_lib_file = None
        self.refresh_library_list()

    def refresh_library_list(self):
        for widget in self.lib_file_list.winfo_children():
            widget.destroy()

        lib_dir = "library"
        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        query = self.search_entry.get().lower().strip()
        files = sorted([f for f in os.listdir(lib_dir) if f.endswith(".md")], reverse=True)

        for filename in files:
            if query and query not in filename.lower():
                continue

            btn = ctk.CTkButton(
                self.lib_file_list, 
                text=filename, 
                anchor="w", 
                fg_color="transparent",
                text_color=("black", "white"),
                hover_color="#34495e",
                command=lambda f=filename: self.load_library_file(f)
            )
            btn.pack(fill="x", pady=2)

    def load_library_file(self, filename):
        self.current_lib_file = filename
        filepath = os.path.join("library", filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.lib_preview.delete("0.0", "end")
            self.lib_preview.insert("0.0", content)
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht lesen: {e}")

    def delete_selected_library_file(self):
        if not self.current_lib_file:
            messagebox.showwarning("Hinweis", "Bitte wähle zuerst eine Datei aus.")
            return

        if messagebox.askyesno("Löschen", f"Soll '{self.current_lib_file}' wirklich gelöscht werden?"):
            filepath = os.path.join("library", self.current_lib_file)
            if os.path.exists(filepath):
                os.remove(filepath)
                self.lib_preview.delete("0.0", "end")
                self.current_lib_file = None
                self.refresh_library_list()

    def copy_text_to_clipboard(self, text):
        if text.strip():
            self.clipboard_clear()
            self.clipboard_append(text.strip())
            messagebox.showinfo("Erfolg", "Prompt wurde in die Zwischenablage kopiert!")