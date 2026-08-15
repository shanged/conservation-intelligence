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

The live failure analysis showed that free-form inline E-ID formatting was too
fragile. The Responses API now returns schema-constrained claim objects, each
with prose-only text and an `evidence_ids` array restricted to the IDs supplied
for that request. Local code places those IDs adjacent to their claims and then
performs the existing SQLite provenance validation and trusted citation
rendering. A bounded repair request remains for malformed legacy output.

## Routing rules

The hybrid entry point routes the following deterministic patterns before
retrieval or API client construction:

- structured entity-frequency questions (`agencies appear most often`);
- generated wiki inventory and grounded unanswered-question inventory;
- document-list questions phrased as `what/which documents discuss/mention`.

Relationship, summary, and structured threat questions use local retrieval
followed by OpenAI synthesis when enabled because cautious prose combination
can improve their utility. Citation validation and deterministic fallback
remain active.
