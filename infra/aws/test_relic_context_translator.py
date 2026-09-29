import copy
import unittest

from relic_context_translator import build_context_pack, query_terms


class ReLiCContextTranslatorTests(unittest.TestCase):
    def test_query_terms_prefers_explicit_names(self):
        terms = query_terms(
            'Fix the "MMO deed map" around Endemar and Westforde.',
            ["Endemar", "Westforde"],
        )
        self.assertEqual(terms[:2], ["Endemar", "Westforde"])
        self.assertIn("MMO deed map", terms)

    def test_pack_is_pointer_based_and_does_not_mutate_sources(self):
        project = [
            {
                "recordId": "project.endemar",
                "title": "Endemar deed boundary",
                "text": "Endemar fits entirely inside one deed zone and is not the whole world map.",
                "truthDomain": "FACT",
                "status": "documented-current",
                "sources": [{"sourceId": "source.canon"}],
            },
            {
                "recordId": "project.world-growth",
                "title": "Shaelvien growth",
                "text": "Shaelvien expands outward as players create and claim adjacent zones.",
                "truthDomain": "FACT",
                "status": "documented-current",
                "sources": [{"sourceId": "source.canon"}],
            },
        ]
        private_context = {
            "entityCount": 2,
            "entities": [
                {
                    "entity": {
                        "entityId": "neuron.endemar",
                        "label": "Endemar",
                        "entityType": "world-zone",
                        "truthDomain": "FACT",
                        "revision": 4,
                        "sourceRef": "owner-canon",
                    },
                    "relationships": [{
                        "targetId": "neuron.world",
                        "relationType": "origin-of",
                        "truthDomain": "FACT",
                    }],
                },
                {
                    "entity": {
                        "entityId": "neuron.world",
                        "label": "Shaelvien",
                        "entityType": "world",
                        "truthDomain": "FACT",
                        "revision": 9,
                        "sourceRef": "owner-canon",
                    },
                    "relationships": [],
                },
            ],
        }
        before_project = copy.deepcopy(project)
        before_private = copy.deepcopy(private_context)

        packed = build_context_pack(
            "Endemar MMO map",
            project,
            private_context,
            project_snapshot="2026-09-29",
            max_runes=4,
        )

        self.assertEqual(project, before_project)
        self.assertEqual(private_context, before_private)
        self.assertEqual(packed["format"], "RELIC-CONTEXT/1")
        self.assertLessEqual(len(packed["runes"]), 4)
        self.assertTrue(any(r["kind"] == "project-record" for r in packed["runes"]))
        self.assertTrue(any(r["kind"] == "neuron" for r in packed["runes"]))
        self.assertTrue(all("expand" in r for r in packed["runes"]))
        self.assertIn("PTR_EXPAND_ON_DEMAND", packed["compactContext"])
        self.assertIn("MEMORY!=CANON", packed["compactContext"])
        self.assertFalse("database" in packed["shaep"].get("purpose", "").casefold())

    def test_context_hash_is_deterministic(self):
        records = [{
            "recordId": "project.one",
            "title": "One",
            "text": "Stable meaning.",
            "truthDomain": "FACT",
            "status": "current",
            "sources": [],
        }]
        a = build_context_pack("one", records, None, max_runes=3)
        b = build_context_pack("one", records, None, max_runes=3)
        self.assertEqual(a["contextSha256"], b["contextSha256"])
        self.assertEqual(a["compactContext"], b["compactContext"])


if __name__ == "__main__":
    unittest.main()
