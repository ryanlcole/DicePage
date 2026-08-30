# Tabletop Visibility

Tabletop records carry explicit visibility values:

- `gm_private`
- `player_private`
- `selected_players`
- `party_shared`
- `scene_shared`
- `public`
- `hidden_until_revealed`

GM projection may see all scene records. Player projection filters cards, decks, initiative entries, and lore by ownership and share state.

Client-side filtering is an alpha projection boundary, not a secrecy guarantee for shared plaintext files. GM-private source should remain outside player-accessible packages where possible.

