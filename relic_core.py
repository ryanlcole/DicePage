def on_power_change(prev_state:str,next_state:str)->None:
    print(f"[relic_core] Power: {prev_state} -> {next_state}")

def resonance_for(glyph:dict)->float:
    gid=glyph.get("id")
    tbl={"daemon":0.85,"tray":0.95,"hud":1.10,"spark":1.60,
         "solar":1.25,"lunar":0.60,"stone":0.50,
         "element":1.40,"matter":0.70,"dna":1.15,"wave":1.80}
    return tbl.get(gid,1.0)
