# shaelvien_ai_adapter.py
import random
from glyph_core import GlyphCore

class ShaelvienAI:
    """
    AI adapter stub. For now, this acts as a rule-based 'local LLM'
    that can identify glyphs and form simple responses.
    """
    def __init__(self):
        self.glyphs = GlyphCore()

    def chat(self, messages):
        """Simulate conversation; messages is a list of dicts [{role, content}]"""
        user_msg = messages[-1]["content"].lower()
        if "glyph" in user_msg or "rune" in user_msg:
            found = self.glyphs.search(user_msg)
            if not found:
                return "No matching glyphs found."
            chosen = random.choice(found)
            return (f"Activated {chosen['name']} "
                    f"({chosen['element']} | flex={chosen['flex']} | mass={chosen['mass']}).")
        elif "status" in user_msg:
            return "System field stable. All daemons synchronized."
        elif "help" in user_msg:
            return "Commands: glyph <name>, status, stop."
        else:
            return "Shaelvien Core acknowledges."

if __name__ == "__main__":
    ai = ShaelvienAI()
    print(ai.chat([{"role":"user","content":"summon fire glyph"}]))
