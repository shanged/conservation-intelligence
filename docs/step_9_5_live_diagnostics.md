# Step 9.5 live-result diagnosis

This diagnosis uses the saved Step 9 outputs. The application intentionally did
not persist rejected raw model text, so the exact malformed token in questions
1, 4, and 5 cannot be reconstructed. Their recorded failure class is
`invalid_openai_response`; likely causes are identified conservatively rather
than presented as observed model text.

| # | Question class | V1 outcome | Likely cause | V2 routing |
|---:|---|---|---|---|
| 1 | Document inventory: aquatic invasive species | Citation-validation fallback | Likely E-ID/claim-association noncompliance; seven useful local results already existed | Deterministic structured document list |
| 2 | Agency frequency | Overly conservative insufficient response | Aggregate counts are not established by semantic excerpts | Deterministic entity aggregation |
| 3 | Main threats | Overly conservative insufficient response | Aggregate wording requires structured corpus-wide counts | Deterministic entity aggregation |
| 4 | Document inventory: wetlands | Citation-validation fallback | Likely E-ID/claim-association noncompliance; seven useful local results already existed | Deterministic structured document list |
| 5 | Document inventory: waterfowl | Citation-validation fallback | Likely E-ID/claim-association noncompliance; seven useful local results already existed | Deterministic structured document list |
| 6 | Carp/habitat relationship | Overly conservative insufficient response | Prompt treated partial evidence as grounds to refuse; three directly relevant excerpts were supplied | OpenAI synthesis with cautious-partial-evidence instructions |
| 7 | Missouri planning documents | Successful useful OpenAI answer | Evidence and E-ID contract were adequate | OpenAI synthesis |
| 8 | Wetland evidence summary | Successful useful OpenAI answer | Evidence and E-ID contract were adequate | OpenAI synthesis |
| 9 | Generated wiki inventory | Overly conservative insufficient response | Inventory is stored structured data, not a semantic-synthesis task | Deterministic wiki inventory |
| 10 | Unanswered-question inventory | Overly conservative insufficient response | Existing deterministic logic constructs grounded research gaps; one excerpt is unsuitable for LLM synthesis | Deterministic grounded open-question path |

## Structured-output decision

Keep free-form answer text with inline E-IDs. A JSON wrapper could make fields
such as `used_evidence_ids` easier to parse, but it would not establish that each
claim has an adjacent citation. The existing local validator already enforces
claim-level placement, rejects unknown IDs and model-created source metadata,
and renders final citations from SQLite. A bounded formatting-repair request is
smaller and preserves this stronger claim-level contract.

## Routing rules

The hybrid entry point routes the following deterministic patterns before
retrieval or API client construction:

- structured entity-frequency questions (`agencies appear most often`);
- structured threat aggregation (`main conservation threats`);
- generated wiki inventory and grounded unanswered-question inventory;
- document-list questions phrased as `what/which documents discuss/mention`.

Relationship and summary questions continue to use local retrieval followed by
OpenAI synthesis because cautious prose combination can improve their utility.
