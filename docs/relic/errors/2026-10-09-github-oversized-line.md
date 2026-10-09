ReLiC ERROR RECORD

ID: RELIC-GITHUB-OVERSIZED-LINE-2026-10-09
Date: 2026-10-09
Status: OVERRIDE AUTHORIZED / METHOD CORRECTED

Symptom
A normal file fetch rendered an oversized single-line embedded CSS block as truncated output. The assistant incorrectly treated that presentation limitation as if the authoritative source itself could not be retrieved safely, blocking a narrow contributor-page update.

Root cause
The wrong retrieval path was treated as the only available source path. GitHub blob retrieval can return the complete authoritative UTF-8 blob even when line-oriented rendering truncates a very long physical line.

Correction
When an ordinary file view truncates an oversized physical line, retrieve the exact current blob by SHA before escalating. If the blob is complete, use that authoritative content for a deterministic targeted transformation and verify the resulting diff. Do not reconstruct missing text from inference.

Override authority
Ryan L. Cole explicitly authorized an override on 2026-10-09 to resolve this retrieval/tooling error. The override changes the method, not project authority or canon: preserve unrelated code, make only the requested transformation, and verify before representing the work as complete.

Rule
PRESENTATION TRUNCATION != SOURCE UNAVAILABLE.
FETCH EXACT BLOB -> TRANSFORM TARGET -> VERIFY DIFF -> WRITE -> TEST.

Related principle
Additions require compatibility. Alterations require understanding. Destruction requires justification.
