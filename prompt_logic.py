class PromptEngine:
    @staticmethod
    def build(target, role, task, source, tone, fmt, length):
        role_str = role if role else "Experte"
        source_info = f"Nutze folgende Quelle: {source}" if source else "Keine spezifischen Quellen definiert"
        
        # Mapping für Längen-Anweisungen
        length_instructions = {
            "Kurz & Knapp": "Fasse dich extrem kurz. Antworte in maximal 2-3 prägnanten Sätzen oder sehr kurzen Stichpunkten. Vermeide jede Form von Einleitung oder ausschweifenden Erklärungen.",
            "Standard": "Gib eine ausgewogene Antwort mit moderatem Detailgrad. Strukturiere die Antwort klar.",
            "Ausführlich": "Erstelle eine detaillierte und tiefgreifende Analyse. Erläutere Hintergründe, nenne Beispiele und beleuchte verschiedene Aspekte umfassend."
        }

        if not source:
            source_info = "Nutze dein allgemeines Training-Wissen, da keine spezifischen Quellen vorliegen."
        else:
            source_info = f"Berücksichtige zwingend folgende Quellen: {source}."
        
        l_instr = length_instructions.get(length, length_instructions["Standard"])

        if target == "Claude":
            return (
                f"Handle als {role_str}.\n\n"
                f"<context>\n{source_info}\n</context>\n\n"
                f"<task>\n{task}\n</task>\n\n"
                f"<constraints>\nTonfall: {tone}\nFormat: {fmt}\nLänge: {l_instr}\n</constraints>"
            )

        elif target == "ChatGPT":
            return (
                f"Handle als {role_str}.\n"
                f"Hintergrund: {source_info}\n"
                f"Aufgabe: {task}\n\n"
                f"Anforderungen:\n- Tonfall: {tone}\n- Format: {fmt}\n"
                f"- Umfang: {l_instr}\n"
                f"- Methode: Denke Schritt für Schritt vor."
            )

        elif target == "Gemini":
            return (
                f"Rolle: {role_str}. Aufgabe: {task}.\n"
                f"Kontext: {source_info}.\n"
                f"Vorgaben: Stil={tone}, Format={fmt}.\n"
                f"WICHTIG ZUR LÄNGE: {l_instr}"
            )

        elif target == "Perplexity":
            return (
                f"Suche als {role_str} nach: {task}.\n"
                f"Quelle: {source_info}.\n"
                f"Schreibstil: {tone}, Format: {fmt}.\n"
                f"Anweisung zur Länge: {l_instr}"
            )

        return f"Rolle: {role_str}\nAufgabe: {task}\nLänge: {l_instr}\nTon: {tone}"