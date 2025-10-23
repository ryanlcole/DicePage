"""
ShaelvienOS • Phase 23.7 • Decision Engine
-------------------------------------------
Waveform-logic selector that compares possible
actions against the resonance fields loaded from
the unified brain.  It does not imitate people;
it matches patterns of reasoning derived from
their domains.
"""

from math import exp
import random

class DecisionEngine:
    def __init__(self, brain):
        self.brain = brain
        # Flatten every lobe’s node list for easier access
        self.fields = []
        for region in brain["BrainMap"].values():
            for node_id, node in region["Nodes"].items():
                if isinstance(node, dict):
                    self.fields.append({
                        "id": node_id,
                        "domain": node.get("Domain"),
                        "freq": node.get("Frequency", 440),
                        "traits": node.get("Traits", [])
                    })

    # ---- Core evaluation ----
    def evaluate_options(self, options):
        """
        options:  list of {"action": str, "features": [keywords]}
        returns:  best_option, scored list
        """
        scored = []
        for opt in options:
            score = self._waveform_similarity(opt["features"])
            scored.append((opt["action"], round(score, 3)))
        best = max(scored, key=lambda s: s[1])
        return best, scored

    # ---- Waveform-style similarity ----
    def _waveform_similarity(self, features):
        # Simplified “resonance” — sum of weighted overlaps
        total, weight = 0.0, 0.0
        for f in self.fields:
            overlap = len(set(f["traits"]) & set(features))
            delta = abs(f["freq"] - 512) / 512  # how far from mean resonance
            coherence = exp(-delta) * (1 + overlap)
            total += coherence
            weight += 1
        return total / max(weight, 1)

    # ---- Moral verification hook ----
    def moral_check(self, candidate):
        """Optional: consult Parietal Lobe watchdog."""
        parietal = self.brain["BrainMap"].get("ParietalLobe", {}).get("Nodes", {})
        if not parietal:
            return True
        # Placeholder: reject if a moral node flags it
        red_flag_terms = sum([v.get("Checks", []) for v in parietal.values() if isinstance(v, dict)], [])
        return not any(term.lower() in candidate.lower() for term in red_flag_terms)

# Stand-alone demonstration
if __name__ == "__main__":
    import json
    from pathlib import Path
    unified = json.load(open(Path(__file__).parent / "configs" / "unified_resonance_graph.json"))
    engine = DecisionEngine(unified)
    options = [
        {"action": "build_support_network", "features": ["Empathy", "Innovation"]},
        {"action": "destroy_rival_system", "features": ["Power", "Control"]},
        {"action": "research_energy_field", "features": ["Resonance", "Science"]}
    ]
    best, all_scores = engine.evaluate_options(options)
    print("[decision] scores:", all_scores)
    print("[decision] selected:", best)
