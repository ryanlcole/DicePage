# Atlas Drive Provenance

Google Drive remains the approved artwork source. The local runtime cache is a synchronized representation, not a replacement authority.

Current Drive root:

`https://drive.google.com/drive/folders/137kbTGLvKiAOK62DlB4O_DSZc3kt5wtH`

Discovered tile hierarchy:

- `07_Media/Tiles/World_Map/Terrain`
- `07_Media/Tiles/World_Map/Landmarks`
- `07_Media/Tiles/World_Map/Landmarks/Wonders`
- `07_Media/Tiles/Region_Map/Water`
- `07_Media/Tiles/Region_Map/Travel`

The first source files imported into the local cache are:

- Plains source: Drive file `1xXUbi_2Ap7ExVt_nAPvhkPOZ2GBunkTz`
- Hydrological Wonders source: Drive file `1zKRmB_hut2O86tzEiLUFwfdEK5-zuLdg`
- Streams and Small Watercourses source: Drive file `1ev4ilc27nybpvFEWh24SMJ7J2MRu_Ge9`

These Drive files are `text/html` ChatGPT shared-image records. Their embedded image endpoints returned valid PNG source images during these passes.

Local cached source hashes:

- Plains: `54df05f9bd4d035ed30b6069310291a34b9ee90d6be87755d2ca0ff1f9907f69`
- Hydrological Wonders: `4bc3aa893c5f2ecf3ccae2f41ed78fc3c28be4f769d792b0587c53ec2eda8efb`
- Streams and Small Watercourses: `b67cc0397aeccbebcddd5d18be5a7113a00930c0cb543b96c423e7871d3f09ca`

These hashes are verification anchors. If either source changes, derived assets must be marked for regeneration rather than silently substituted.
