# Pre-OpenAI deterministic baseline

Captured: 2026-08-13T21:01:09+00:00

This report records the existing local, deterministic chatbot before any OpenAI integration. Answers are reproduced from the production `answer_question` path; citation validation uses the existing `validate_response` checks against SQLite metadata.

## Summary

- Required questions: 10
- Citation/integrity validation: 10/10 passed
- Median response latency: 74.9 ms
- Maximum response latency: 493.4 ms
- Completeness assessment: 8/10 answers appear complete for the deterministic prototype's documented scope. Questions 5 and 10 appear incomplete or weakly focused. This is a human-review judgment rather than a factual-correctness guarantee.

## Required demo questions

### 1. What documents discuss aquatic invasive species?

- Response latency: 493.4 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The most relevant corpus evidence is:
- **Aquatic Invasive Species in the Chesapeake Bay Watershed**: Many others participated in the prepa- ration of the documents related to aquatic invasive species, which are cited here. [DOC005, pp. 1–8]
- **Invasive Species Accomplishments Report**: The SEINeD is a tool that enables users to screen and link datasets for occurrences of non-native and invasive aquatic species tracked by the NAS Database. [DOC007, pp. 22–24]
- **USGS Nonindigenous Aquatic Species Database Paper**: Types of graphs currently available include: introductions over time, introductions by taxonomic group, native transplants versus foreign (exotics), introductions by pathway, and continent of origin of exotic species. [DOC011, pp. 6–7]
- **Aquatic Invasive Species Research Report**: A plan to address the spread and impact of aquatic invasive species is also provided, as directed in Section 1108(c) of the 2018 Water Resources Development Act. [DOC006, pp. 1–3]
- **National Aquatic Invasive Species Outreach Workshop Summary Report**: Introduction The National Aquatic Invasive Species Outreach Workshop was held as part of the North American Invasive Species Management Association Annual Conference in Missoula, Montana, October 1st, 2024. [DOC010, pp. 1–3]
- **Invasive Species Accomplishments Report PDF**: DEPARTMENT OF THE INTERIOR ACCOMPLISHMENTS REPORT INVASIVE SPECIES STRATEGIC PLAN 2021-2025 PROTECTING AMERICA'S RESOURCES FROM INVASIVE SPECIES Cover Images 1. [DOC008, pp. 1–5]
- **Invasive Carp Strategic Science Plan**: Department of the Interior, 54 p., accessed November 16, 2022, at https://www.doi.gov/ ppa/ doi- invasive- species- strategic- plan. [DOC012, pp. 26–29]

Citations:

- [DOC005, pp. 1–8]
- [DOC007, pp. 22–24]
- [DOC011, pp. 6–7]
- [DOC006, pp. 1–3]
- [DOC010, pp. 1–3]
- [DOC008, pp. 1–5]
- [DOC012, pp. 26–29]

### 2. What agencies appear most often in the corpus?

- Response latency: 74.0 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The most broadly represented agencies, measured from provenance-bearing entity occurrences, are:
- **U.S. Army Corps of Engineers** — 59 chunk occurrences across 13 documents. [DOC001, pp. 115–118]
- **U.S. Fish and Wildlife Service** — 105 chunk occurrences across 12 documents. [DOC001, pp. 18–21]
- **U.S. Department of the Interior** — 73 chunk occurrences across 12 documents. [DOC003, pp. 1–5]
- **U.S. Geological Survey** — 94 chunk occurrences across 11 documents. [DOC001, pp. 42–51]
- **Missouri Department of Conservation** — 89 chunk occurrences across 10 documents. [DOC001, pp. 1–8]
- **U.S. Environmental Protection Agency** — 75 chunk occurrences across 8 documents. [DOC001, pp. 248–253]

Citations:

- [DOC001, pp. 115–118]
- [DOC001, pp. 18–21]
- [DOC003, pp. 1–5]
- [DOC001, pp. 42–51]
- [DOC001, pp. 1–8]
- [DOC001, pp. 248–253]

### 3. What are the main conservation threats mentioned across the documents?

- Response latency: 75.7 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The most broadly represented extracted threats are:
- **invasive species** — 168 chunk occurrences across 18 documents. [DOC001, pp. 27–29]
- **disease** — 39 chunk occurrences across 14 documents. [DOC001, pp. 27–29]
- **habitat loss** — 60 chunk occurrences across 10 documents. [DOC001, pp. 27–29]
- **climate change** — 45 chunk occurrences across 10 documents. [DOC001, pp. 27–29]
- **flooding** — 43 chunk occurrences across 9 documents. [DOC001, pp. 24–26]
- **pollution** — 173 chunk occurrences across 8 documents. [DOC001, pp. 27–29]

Citations:

- [DOC001, pp. 27–29]
- [DOC001, pp. 24–26]

### 4. What documents discuss wetlands or wetland management?

- Response latency: 65.9 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The most relevant corpus evidence is:
- **Missouri Wetland Program Plan**: K-12 classes where the importance of wetlands is presented to students. [DOC002, pp. 16–20]
- **EPA Wetlands Program**: The protection of wetlands is supported by various Clean Water Act programs and the EPA's initiatives. [DOC023, Web]
- **USFWS National Wetlands Inventory**: Produced on a decadal basis, these reports inform decision-makers and the public on the status of the nation's wetlands as well as potential causes and implications of wetland change. [DOC022, Web]
- **DocumentCloud Wetland Search**: Construction Wetland Habitat Fill material placed in wetlands during construction would result in the permanent loss of wetlands, associated vegetation, and any habitat that the wetland provides for fish and wildlife. [DOC035, pp. 167–168]
- **State Wildlife Action Plans Report with State Summaries**: Development of tax incentives and disincentives, easements, and cooperative management programs is crucial to the achievement of this task. [DOC013, pp. 171–172]
- **USFWS Library**: Fish and Wildlife Service is the principal federal agency tasked with providing information to the public on the extent and status of the nation’s wetland and deepwater habitats, as well as changes to these habitats over time. [DOC028, Web]
- **Missouri Wetlands Information**: As a transition zone between land and aquatic habitats (such as lakes, streams, and rivers), wetlands have one or more of these characteristics: At least periodically, the wetland is dominated by aquatic plants (hydrophytes). [DOC025, Web]

Citations:

- [DOC002, pp. 16–20]
- [DOC023, Web]
- [DOC022, Web]
- [DOC035, pp. 167–168]
- [DOC013, pp. 171–172]
- [DOC028, Web]
- [DOC025, Web]

### 5. What public documents mention waterfowl conservation?

- Response latency: 58.9 ms
- Citation validation: PASS
- Appears complete: No - several returned passages are only tangentially related to waterfowl conservation.
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The most relevant corpus evidence is:
- **North American Waterfowl Management Plan Update**: Thus, if waterfowl populations are to be sustained, conservation efforts must continually be adjusted. [DOC003, pp. 6–9]
- **NAWMP Value Proposition**: Since 1986, the Plan has been a catalyst for sustaining abundant waterfowl populations by conserving landscapes through public-private partnerships guided by sound science. [DOC004, pp. 1–3]
- **Ducks Unlimited Conservation Resources**: Learn More For People Conservation for waterfowl benefits hunters, anglers, hikers, and all society by expanding recreational opportunities, promoting productive ecosystems, and protecting open spaces, while also cleaning our water and safeguarding our communities. [DOC021, Web]
- **State Wildlife Action Plans Report with State Summaries**: Eastern red bat, Timber rattlesnake, Whip- poor-will, Bobcat Development or conversion of habitat into home lots, roads, businesses, etc.; resulting fragmentation degrades quality of remaining habitat. [DOC013, pp. 158–161]
- **USFWS Migratory Birds Program**: Fish and Wildlife Service to reduce bird collisions Spring migration is winding down and many of our favorite birds have returned to back yard feeders for their summer stay. [DOC026, Web]
- **MDC Management Plans**: Then A and B pool could be closed 2019 Schell-Osage Conservation Area Management Plan Page 25 while the remaining pools are re-opened. [DOC019, pp. 24–25]
- **North American Waterfowl Management Plan Update**: The North American Waterfowl Management Plan—A Conservation Legacy 1 The Changing Context of Waterfowl Conservation 3 Evolution of Waterfowl Conservation in North America. [DOC003, p. 5]

Citations:

- [DOC003, pp. 6–9]
- [DOC004, pp. 1–3]
- [DOC021, Web]
- [DOC013, pp. 158–161]
- [DOC026, Web]
- [DOC019, pp. 24–25]
- [DOC003, p. 5]

### 6. What is the relationship between invasive carp and aquatic habitat management?

- Response latency: 64.9 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The structured extraction found no direct `species_uses_habitat` relation for invasive carp, so co-mention is not treated as proof of habitat use. Retrieved evidence connects invasive-carp research and management with aquatic systems as follows:
- Geological Survey Invasive Carp Science 7 Deterrents One factor that likely contributes significantly to the inva- siveness of invasive carp is their mobility (Vallazza and oth- ers, 2020; Coulter and others, 2022). [DOC012, pp. 14–15]
- Stohlgren TJ, Folfelder KA, Graham J, Waller DM (2011) Assessing citizen science data quality: an invasive species case study. [DOC011, p. 11]
- Like terrestrial habitat systems, aquatic systems are extremely vulnerable to the effects of invasive species, especially due to the high connectivity of most aquatic systems. [DOC001, pp. 170–172]
- Invasive carp, such as Hypophthalmichthys molatrix (silver carp), also received mention by multiple agencies (3 of the 10 stakeholder groups) because these fish represent priority AIS in nearby watersheds and a threat for introduction and dis- semination within the Chesapeake Bay watershed from these neighboring regions. [DOC005, pp. 13–14]
- Chapman, D.C., 2020, “Modified Unified Method” of carp capture: U.S. [DOC012, pp. 28–30]

Citations:

- [DOC012, pp. 14–15]
- [DOC011, p. 11]
- [DOC001, pp. 170–172]
- [DOC005, pp. 13–14]
- [DOC012, pp. 28–30]

### 7. Which documents are most relevant to Missouri conservation planning?

- Response latency: 71.7 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The most relevant corpus evidence is:
- **Missouri State Wildlife Action Plan**: The CCS is a process that identifies Missouri conserva- tion priorities to inform decision-making regarding the greatest opportunities for sustainable conservation of fish, forest, and wildlife. [DOC001, pp. 17–18]
- **MDC Annual Review FY2021**: The Missouri Comprehensive Conservation Strategy (CCS) integrates the Missouri State Wildlife Action Plan, Forest Action Plan, and other conservation priorities into a comprehensive plan, meeting the requirements of both the U.S. [DOC018, Web]
- **MDC Annual Review FY2024**: Missouri Comprehensive Conservation Strategy In FY23, MDC reestablished the Comprehensive Conservation Strategy (CCS) working group, which provides guidance to CCS implementation. [DOC016, Web]
- **State Wildlife Action Plans Report with State Summaries**: Missouri’s planning approach Utilizing wildlife information gathered over the past 30 years, Missouri’s Comprehensive Wildlife Strat- egy promotes management that beneﬁ ts all wildlife, rather than targeting sin- gle species. [DOC013, pp. 139–141]
- **MDC Management Plans**: Guidelines for avoiding and minimizing impacts to federally-listed bats on Missouri Department of Conservation lands. [DOC019, pp. 17–24]
- **MDC Annual Review FY2023**: Missouri Comprehensive Conservation Strategy During this past year, 19 regional Comprehensive Conservation Strategy (CCS) trainings were provided to over 350 managers, technicians, and supervisors. [DOC017, Web]
- **Missouri Conservation Report**: Missouri’s CCS embraces landscape- scale conservation informed by natural community and wildlife diversity needs, working to maintain, enhance, restore, and re -create healthy natural systems. [DOC015, pp. 5–6]

Citations:

- [DOC001, pp. 17–18]
- [DOC018, Web]
- [DOC016, Web]
- [DOC013, pp. 139–141]
- [DOC019, pp. 17–24]
- [DOC017, Web]
- [DOC015, pp. 5–6]

### 8. Generate a short cited summary of wetland conservation evidence in the corpus.

- Response latency: 266.4 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The corpus highlights several complementary approaches to wetland conservation:
- **Protection and restoration.** EPA conservation programs pair wetland protection with restoration initiatives across its regions. [DOC023, Web]
- **Monitoring and assessment.** Monitoring and assessment track wetland status and change so decision-makers can understand causes and implications. [DOC022, Web]
- **Ecological and community benefits.** Wetlands filter water, protect communities from floods, and provide habitat for fish and other wildlife. [DOC029, Web]

Citations:

- [DOC023, Web]
- [DOC022, Web]
- [DOC029, Web]

### 9. What wiki pages were generated for species, habitats, threats, and agencies?

- Response latency: 208.9 ms
- Citation validation: PASS
- Appears complete: Yes
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The generated wiki currently contains:
- **agency:** Missouri Department of Conservation, U.S. Army Corps of Engineers, U.S. Department of the Interior, U.S. Fish and Wildlife Service. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **habitat:** forest. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **location:** Great Lakes, Missouri. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **species:** invasive carp, silver carp, zebra mussel. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **threat:** climate change, habitat loss, invasive species. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **wetland:** marsh, wetland. [DOC001, pp. 1–8] [DOC003, pp. 1–5]

Citations:

- [DOC001, pp. 1–8]
- [DOC003, pp. 1–5]

### 10. What important questions remain unanswered by this corpus?

- Response latency: 125.1 ms
- Citation validation: PASS
- Appears complete: No - the response identifies only one open question and does not synthesize the broader corpus gaps.
- Insufficient evidence: No
- Validation notes: None

Deterministic answer:

The current evidence leaves several recurring questions open:
- Which findings remain current, especially where reports describe plans rather than measured outcomes? [DOC032, pp. 34–35]

Citations:

- [DOC032, pp. 34–35]

## Insufficient-evidence behavior

Probe: What does this corpus say about coral reef restoration on Mars?

- Response latency: 89.5 ms
- Insufficient flag: No
- Citations returned: 6

The most relevant corpus evidence is:
- **NOAA Habitat Conservation**: The framework that guides NOAA’s approach is the Habitat Blueprint It’s helping us to think and act strategically to address the growing challenges facing our coastal and marine habitats. [DOC029, Web]
- **DocumentCloud Water Quality Search**: The accuracy of the predictions is discussed in this section. [DOC033, pp. 132–133]
- **State Wildlife Action Plans Report with State Summaries**: Not surprisingly, most of the public opinion was delivered verbal- ly, in small groups or through individual interviews. [DOC013, pp. 184–186]
- **Ducks Unlimited Conservation Resources**: See what techniques we use to protect and enhance existing habitats while restoring those previously degraded.​ Learn More Science Since 1937, we’ve relied on sound science to guide our conservation. [DOC021, Web]
- **DocumentCloud Environment Project Search**: The Convention on Biological Diversity acknowledges that there is a “close and traditional dependence” of local communities on biological resources and that sustainable use of biological diversity is necessary for the benefit of present and future generations. [DOC032, p. 15]
- **MDC Annual Review FY2023**: This area is a crown jewel of woodland and glade restoration in this Upper Niangua River conservation opportunity area. [DOC017, Web]
- **NOAA Habitat Conservation**: We also explore and protect coral habitat in the deep sea, which is the least explored place on Earth. [DOC029, Web]

## Observed failure cases and limitations

- No required demo question failed the existing automated citation/integrity validator (10/10 passed).
- The validator checks answer presence, evidence, citation syntax/IDs, and SQLite locations; it does not prove factual correctness, relevance, or completeness.
- Some retrieved/extractive passages contain OCR artifacts, broken hyphenation, table-of-contents-like text, or weakly focused sentences.
- Semantic similarity can return tangential evidence; the observed `wetland restoration` result set included a bibliography-like top passage.
- DOC007 and DOC008 represent the same underlying report, which can reduce source diversity despite snippet deduplication.
- Three corpus sources require manual intervention (DOC014, DOC027, DOC030).
- **Failure:** the intentionally out-of-scope probe did not trigger insufficient-evidence behavior. It returned seven tangential evidence bullets and six citations, so refusal behavior is not reliable for arbitrary unsupported questions.
