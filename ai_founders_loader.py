"""
ShaelvienOS • Phase 23.8 • Brain Runtime Alpha (Full Loader)
-------------------------------------------------------------
Integrates all cognitive lobes and sensory receptors into
a unified brain map.  Provides the load_founders() function
used by shaelvien_daemon.py.
"""

from pathlib import Path
import json
import math
import sys

# -------------------------------------------------
# Brain map definitions
# -------------------------------------------------
CONFIG_PATH = Path(__file__).parent / "configs"

BRAIN_MAP = {
    "FrontalLobe": {
        "SourceFiles": ["ai_founders.json"],
        "Functions": ["AnalyticalReasoning", "ProblemSolving", "Innovation"]
    },
    "TemporalLobe": {
        "SourceFiles": ["fiction_founders.json"],
        "Functions": ["NarrativeProcessing", "Creativity", "LanguagePatterning"]
    },
    "ParietalLobe": {
        "SourceFiles": ["moral_watchdog.json"],
        "Functions": ["EthicalModeration", "ContextAwareness", "EmpathyMapping"]
    },
    "OccipitalLobe": {
        "SourceFiles": ["visual_audio_particles.json"],
        "Functions": ["ParticleVisuals", "AudioResonance", "GlyphImaging"]
    },
    "CerebellumLimbic": {
        "SourceFiles": ["cerebellum_limbic.json"],
        "Functions": ["BalanceControl", "EmotionMemory", "FeedbackLoop"]
    },
    "ThalamusCore": {
        "SourceFiles": ["thalamus_core.json"],
        "Functions": ["SignalRouting", "Timing", "Synchronization"]
    },
    "ReceptorMatrix": {
        "SourceFiles": [],
        "Functions": [
            "VisionReceptor",
            "AudioReceptor",
            "EmpathyReceptor",
            "OlfactoryReceptor",
            "TactileReceptor"
        ]
    }
}

# -------------------------------------------------
# JSON helper
# -------------------------------------------------
def _load_json(fp: Path):
    try:
        with open(fp, "r", encoding="utf8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[loader] ⚠ Cannot read {fp.name}: {e}")
        return None


# -------------------------------------------------
# Main loader
# -------------------------------------------------
def load_founders():
    unified = {"BrainMap": {}, "ResonanceMatrix": []}

    for region, meta in BRAIN_MAP.items():
        region_nodes = {}
        for src in meta.get("SourceFiles", []):
            data = _load_json(CONFIG_PATH / src)
            if not data:
                continue
            nodes = (
                data.get("Founders")
                or data.get("Watchdog")
                or data.get("Modules")
                or {}
            )
            region_nodes.update(nodes)
            print(f"[loader] {region:<15} ← {len(nodes):02d} nodes from {src}")
        unified["BrainMap"][region] = {
            "Functions": meta["Functions"],
            "Nodes": region_nodes
        }

    # Calculate average resonance
    all_nodes = sum(
        [list(region["Nodes"].values()) for region in unified["BrainMap"].values()],
        []
    )
    freqs = [n.get("Frequency", 440) for n in all_nodes if isinstance(n, dict)]
    avg = round(sum(freqs) / len(freqs), 3) if freqs else 440.0
    unified["ResonanceMatrix"].append({"AverageFrequency": avg})
    print(f"[loader] Average resonance = {avg} Hz")

    # Define static receptor structures
    unified["ReceptorMatrix"] = {
        "VisionReceptor": {
            "Domain": "Visual Interpretation",
            "Parameters": {
                "ColorDepth": 24,
                "Resolution": [1920, 1080],
                "EvaluationModel": "ArtisticComposition",
                "LightTolerance": 0.85,
                "PatternRecognition": "High"
            },
            "Output": "AestheticMap"
        },
        "AudioReceptor": {
            "Domain": "Auditory Analysis",
            "Parameters": {
                "SampleRate": 44100,
                "SpectralResolution": 2048,
                "EvaluationModel": "ComposerPrecision",
                "LoudnessTolerance": 0.9,
                "SpatialAwareness": "Stereo"
            },
            "Output": "HarmonyProfile"
        },
        "EmpathyReceptor": {
            "Domain": "Behavioral and Motion Analysis",
            "Parameters": {
                "CameraInput": True,
                "MotionSensitivity": 0.95,
                "MicrogestureTracking": True,
                "ResponseModel": "PeacefulResolution",
                "ReactionTimeMs": 200
            },
            "Output": "EmotiveStateVector"
        },
        "OlfactoryReceptor": {
            "Domain": "Aroma-Frequency Interpretation",
            "Parameters": {
                "FrequencyToAromaMap": {
                    "261.6": "Citrus",
                    "329.6": "Floral",
                    "392.0": "Herbal",
                    "440.0": "Sweet",
                    "493.9": "Savory"
                },
                "InterpretationMode": "VisualToAroma",
                "ConfidenceThreshold": 0.7
            },
            "Output": "FlavorProfile"
        },
        "TactileReceptor": {
            "Domain": "Environmental Pressure and Feedback",
            "Parameters": {
                "InputStrengthScaling": "Linear",
                "Thresholds": {
                    "LightTouch": 0.2,
                    "Comfort": 0.5,
                    "Stress": 0.75,
                    "Harm": 0.9
                },
                "ResponseCurve": "Adaptive",
                "AggressionDetection": "TypingPatternAnalysis"
            },
            "Output": "FeedbackSignal"
        }
    }

    return unified


# -------------------------------------------------
# Stand-alone test + circular import guard
# -------------------------------------------------
if __name__ == "__main__":
    # Circular import check
    if "ai_founders_loader" in sys.modules and sys.modules["ai_founders_loader"] is None:
        print("[loader] ⚠ Circular import detected — exiting safely.")
        sys.exit(1)

    graph = load_founders()
    out = CONFIG_PATH / "unified_resonance_graph.json"
    try:
        with open(out, "w", encoding="utf8") as f:
            json.dump(graph, f, indent=2)
        print(f"[loader] Unified Resonance Graph → {out.name}")
    except Exception as e:
        print(f"[loader] ⚠ Failed to write unified graph: {e}")
