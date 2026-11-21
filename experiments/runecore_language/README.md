# RuneCore / Language+Viewer experiment

Experimental, standalone RuneCore/1 interpreter and visible-atoms-only canvas viewer. The live Shaelvien app is untouched, and this feature branch is proposed for review rather than merged directly.

Local checks: `python -m unittest -v test_runecore_language`.
Run parser: `python runecore_language.py --tick 7 --view -4 -3 4 3`.
Visual demo: open `index.html` locally; drag to pan and scroll or pinch to zoom.

The viewer computes rotational bits in browser memory and only paints atoms intersecting the visible window. It runs only while the browser is open. It does **not** itself provide continuous offscreen simulation, server storage, chemical bonding, or a trained RuneCore LLM. Earlier v0.7 and v0.9 Python/SQLite prototypes remain separate until carefully integrated and tested. Ring positions use the supplied H and O patterns. Start/stop *binary opcodes* remain unspecified.

GitHub Pages can publish the HTML with no paid plan for a public repository, but an actual Pages deployment requires repository settings or workflow activation; a branch PR alone is **not** a live website. See LANGUAGE.md for exact truth boundaries and model-training research plan.
