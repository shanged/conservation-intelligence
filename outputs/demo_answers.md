# Offline Deterministic Baseline Evaluation

These checks exercise the local deterministic answer path only; they do not call or score OpenAI synthesis. PASS validates retrieval, answer presence, and citation integrity, not human answer quality.

## 1. What documents discuss aquatic invasive species?

**Heuristic status:** PASS

### Generated answer

The most relevant corpus evidence is:
- **Aquatic Invasive Species in the Chesapeake Bay Watershed**: Many others participated in the prepa- ration of the documents related to aquatic invasive species, which are cited here. [DOC005, pp. 1–8]
- **Invasive Species Accomplishments Report**: The SEINeD is a tool that enables users to screen and link datasets for occurrences of non-native and invasive aquatic species tracked by the NAS Database. [DOC007, pp. 22–24]
- **USGS Nonindigenous Aquatic Species Database Paper**: Types of graphs currently available include: introductions over time, introductions by taxonomic group, native transplants versus foreign (exotics), introductions by pathway, and continent of origin of exotic species. [DOC011, pp. 6–7]
- **Aquatic Invasive Species Research Report**: A plan to address the spread and impact of aquatic invasive species is also provided, as directed in Section 1108(c) of the 2018 Water Resources Development Act. [DOC006, pp. 1–3]
- **National Aquatic Invasive Species Outreach Workshop Summary Report**: Introduction The National Aquatic Invasive Species Outreach Workshop was held as part of the North American Invasive Species Management Association Annual Conference in Missoula, Montana, October 1st, 2024. [DOC010, pp. 1–3]
- **Invasive Species Accomplishments Report PDF**: DEPARTMENT OF THE INTERIOR ACCOMPLISHMENTS REPORT INVASIVE SPECIES STRATEGIC PLAN 2021-2025 PROTECTING AMERICA'S RESOURCES FROM INVASIVE SPECIES Cover Images 1. [DOC008, pp. 1–5]
- **Invasive Carp Strategic Science Plan**: Department of the Interior, 54 p., accessed November 16, 2022, at https://www.doi.gov/ ppa/ doi- invasive- species- strategic- plan. [DOC012, pp. 26–29]

### Citations

[DOC005, pp. 1–8], [DOC007, pp. 22–24], [DOC011, pp. 6–7], [DOC006, pp. 1–3], [DOC010, pp. 1–3], [DOC008, pp. 1–5], [DOC012, pp. 26–29]

### Retrieved evidence

- **Aquatic Invasive Species in the Chesapeake Bay Watershed** — DOC005, 1-8; similarity 0.721. Many others participated in the prepa- ration of the documents related to aquatic invasive species, which are cited here.
  https://pubs.usgs.gov/of/2020/1057/ofr20201057.pdf
- **Invasive Species Accomplishments Report** — DOC007, 22-24; similarity 0.693. The SEINeD is a tool that enables users to screen and link datasets for occurrences of non-native and invasive aquatic species tracked by the NAS Database.
  https://www.doi.gov/media/document/invasive-species-accomplishments-report-2021-2025
- **USGS Nonindigenous Aquatic Species Database Paper** — DOC011, 6-7; similarity 0.683. Types of graphs currently available include: introductions over time, introductions by taxonomic group, native transplants versus foreign (exotics), introductions by pathway, and continent of origin of exotic species.
  https://pdfs.semanticscholar.org/8a85/a4db10dd8eb5a9fea35094ac9885e5e9974b.pdf
- **Aquatic Invasive Species Research Report** — DOC006, 1-3; similarity 0.678. A plan to address the spread and impact of aquatic invasive species is also provided, as directed in Section 1108(c) of the 2018 Water Resources Development Act.
  https://usace.contentdm.oclc.org/digital/api/collection/p16021coll5/id/35588/download
- **National Aquatic Invasive Species Outreach Workshop Summary Report** — DOC010, 1-3; similarity 0.672. Introduction The National Aquatic Invasive Species Outreach Workshop was held as part of the North American Invasive Species Management Association Annual Conference in Missoula, Montana, October 1st, 2024.
  https://www.fws.gov/carp/sites/default/files/documents/2025-09/national-aquatic-invasive-species-outreach-workshop-summary-report.pdf
- **Invasive Species Accomplishments Report PDF** — DOC008, 1-5; similarity 0.619. DEPARTMENT OF THE INTERIOR ACCOMPLISHMENTS REPORT INVASIVE SPECIES STRATEGIC PLAN 2021-2025 PROTECTING AMERICA'S RESOURCES FROM INVASIVE SPECIES Cover Images 1.
  https://www.bia.gov/sites/default/files/dup/tcinfo/invasive-species-accomplishments-report2021-2025.pdf
- **Invasive Carp Strategic Science Plan** — DOC012, 26-29; similarity 0.614. Department of the Interior, 54 p., accessed November 16, 2022, at https://www.doi.gov/ ppa/ doi- invasive- species- strategic- plan.
  https://www.govinfo.gov/content/pkg/GOVPUB-I19-PURL-gpo224710/pdf/GOVPUB-I19-PURL-gpo224710.pdf

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 2. What agencies appear most often in the corpus?

**Heuristic status:** PASS

### Generated answer

The most broadly represented agencies, measured from provenance-bearing entity occurrences, are:
- **U.S. Army Corps of Engineers** — 59 chunk occurrences across 13 documents. [DOC001, pp. 115–118]
- **U.S. Fish and Wildlife Service** — 105 chunk occurrences across 12 documents. [DOC002, pp. 3–6]
- **U.S. Department of the Interior** — 73 chunk occurrences across 12 documents. [DOC003, pp. 1–5]
- **U.S. Geological Survey** — 94 chunk occurrences across 11 documents. [DOC005, pp. 1–8]
- **Missouri Department of Conservation** — 89 chunk occurrences across 10 documents. [DOC012, pp. 38–40]
- **U.S. Environmental Protection Agency** — 75 chunk occurrences across 8 documents. [DOC009, pp. 4–6]

### Citations

[DOC001, pp. 115–118], [DOC002, pp. 3–6], [DOC003, pp. 1–5], [DOC005, pp. 1–8], [DOC012, pp. 38–40], [DOC009, pp. 4–6]

### Retrieved evidence

- **Missouri State Wildlife Action Plan** — DOC001, 115-118; similarity 1.000. Army Corps of Engineers, is a sandstone glade that is still thriving.
  https://www.mdc.mo.gov/sites/default/files/2020-04/SWAP_0.pdf
- **Missouri Wetland Program Plan** — DOC002, 3-6; similarity 1.000. Department of Agriculture USFWS U.S.
  https://www.epa.gov/system/files/documents/2024-06/missouri_wetland-program-plan-20240117-cw.pdf
- **North American Waterfowl Management Plan Update** — DOC003, 1-5; similarity 1.000. Department of the Interior, Fish and Wildlife Service SEMARNAP Mexico SEMARNAP MÉXICO Environnement Canada Service canadien de la faune Environment Canada Canadian Wildlife Service Contents Preface . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . v Acknowledgements. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .…
  https://www.fws.gov/sites/default/files/documents/2024-04/1445.pdf
- **Aquatic Invasive Species in the Chesapeake Bay Watershed** — DOC005, 1-8; similarity 1.000. Geological Survey Partners and Collaborators Cover: Aquatic habitat at Blackwater National Wildlife Refuge (Cambridge, MD), taken January 5, 2015. (photo by Christine Densmore/USGS) Aquatic Invasive Species in the Chesapeake Bay Drainage— Research-Based Needs and Priorities of U.S.
  https://pubs.usgs.gov/of/2020/1057/ofr20201057.pdf
- **Invasive Carp Strategic Science Plan** — DOC012, 38-40; similarity 1.000. Photograph by the Missouri Department of Conservation. p.
  https://www.govinfo.gov/content/pkg/GOVPUB-I19-PURL-gpo224710/pdf/GOVPUB-I19-PURL-gpo224710.pdf
- **Aquatic Invasive Species Commission Report** — DOC009, 4-6; similarity 1.000. The United States should also participate in national or binational scientific or monitoring programs providing information as result of discharge sample collection and analysis following monitoring requirements as indicated by the EPA’s Vessels General Permit (VGP).
  https://www.trcp.org/wp-content/uploads/2023/02/Aquatic-Invasive-Species-Report-3-28-2023.pdf
- **Aquatic Invasive Species in the Chesapeake Bay Watershed** — DOC005, 24-26; similarity 0.377. SRBC has a particularly unique challenge in reconciling fish passage needs related to restora- tion of important anadromous species (eel and shad) with con- tainment of invasive fish, including northern snakehead and blue catfish, at four hydroelectric dam passage barriers on the lower Susquehanna River.
  https://pubs.usgs.gov/of/2020/1057/ofr20201057.pdf
- **Aquatic Invasive Species Commission Report** — DOC009, 8-10; similarity 0.357. Congress should direct funding to the ANSTF to commission a study or provide an updated report on the effectiveness of AIS statutes, regulations and policies at the federal, state, and tribal levels, identifying well -performing interagency regulations and making recommendations to member agencies and state and tribal governments on model legislation.
  https://www.trcp.org/wp-content/uploads/2023/02/Aquatic-Invasive-Species-Report-3-28-2023.pdf

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 3. What are the main conservation threats mentioned across the documents?

**Heuristic status:** PASS

### Generated answer

The most broadly represented extracted threats are:
- **invasive species** — 168 chunk occurrences across 18 documents. [DOC001, pp. 27–29]
- **disease** — 39 chunk occurrences across 14 documents. [DOC003, pp. 25–28]
- **habitat loss** — 60 chunk occurrences across 10 documents. [DOC005, pp. 14–15]
- **climate change** — 45 chunk occurrences across 10 documents. [DOC004, pp. 2–4]
- **flooding** — 43 chunk occurrences across 9 documents. [DOC002, pp. 14–17]
- **pollution** — 173 chunk occurrences across 8 documents. [DOC009, pp. 10–11]

### Citations

[DOC001, pp. 27–29], [DOC003, pp. 25–28], [DOC005, pp. 14–15], [DOC004, pp. 2–4], [DOC002, pp. 14–17], [DOC009, pp. 10–11]

### Retrieved evidence

- **Missouri State Wildlife Action Plan** — DOC001, 27-29; similarity 1.000. Exotic invasive species rank as the second-greatest threat, impacting 49% of the species.
  https://www.mdc.mo.gov/sites/default/files/2020-04/SWAP_0.pdf
- **North American Waterfowl Management Plan Update** — DOC003, 25-28; similarity 1.000. Disease has led to significant waterfowl mortality in certain regions of North America and continues to be a concern among waterfowl conservationists.
  https://www.fws.gov/sites/default/files/documents/2024-04/1445.pdf
- **Aquatic Invasive Species in the Chesapeake Bay Watershed** — DOC005, 14-15; similarity 1.000. Ongoing threats to Chesapeake Bay and watershed health exist from multiple sources, including habitat loss to deforestation and urbaniza- tion, chemical contaminant and nutrient loading of water, and aquatic wildlife population declines through overharvesting or disease, among others.
  https://pubs.usgs.gov/of/2020/1057/ofr20201057.pdf
- **NAWMP Value Proposition** — DOC004, 2-4; similarity 1.000. These pressures contribute to continued loss and degradation of wetlands and uplands. • Assessing the effects of climate change and alternative energy sources like wind power and ethanol fuel crop conversion.
  https://nawmp.org/sites/default/files/2022-03/NAWMP%20Value%20Prop%20Abbreviated%20version%202016%20FINAL_sm.pdf
- **Missouri Wetland Program Plan** — DOC002, 14-17; similarity 1.000. X X X X X X The department, MDC, USACE, and USFWS will explore opportunities to leverage existing programs and ongoing study efforts along the Missouri and Mississippi rivers (Upper Mississippi River Restoration Program, Navigation and Ecosystem Sustainability Program, Lower Missouri River Flood Risk and Resiliency Study) to promote wetland enhancement, rehabilitation, and restoration.
  https://www.epa.gov/system/files/documents/2024-06/missouri_wetland-program-plan-20240117-cw.pdf
- **Aquatic Invasive Species Commission Report** — DOC009, 10-11; similarity 1.000. ANSTF should encourage and facilitate state and tribal adoption and implementation of regionally coordinated approaches, such as the “Model Legal Framework for Watercraft Inspection and The most effective way to prevent AIS contamination is through robust, coordinated action on all levels – federal, state, local, tribal, industry and individual.
  https://www.trcp.org/wp-content/uploads/2023/02/Aquatic-Invasive-Species-Report-3-28-2023.pdf
- **State Wildlife Action Plans Report with State Summaries** — DOC013, 15-17; similarity 0.604. Identifying Challenges to Wildlife and their Habitats Eff ective conservation depends on an as- sessment of the specifi c issues, challeng- es, and problems that are contributing to declines in wildlife and their habitat.
  https://www.fishwildlife.org/application/files/6415/1856/1631/StateWildlifeActionPlansReportwithStateSummaries.pdf
- **DocumentCloud Wetland Search** — DOC035, 205-208; similarity 0.563. Potential impacts caused by rail line construction are discussed first for each resource, followed by potential impacts caused by rail operations.
  https://www.documentcloud.org/public/search?q=wetland

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 4. What documents discuss wetlands or wetland management?

**Heuristic status:** PASS

### Generated answer

The most relevant corpus evidence is:
- **Missouri Wetland Program Plan**: K-12 classes where the importance of wetlands is presented to students. [DOC002, pp. 16–20]
- **EPA Wetlands Program**: The protection of wetlands is supported by various Clean Water Act programs and the EPA's initiatives. [DOC023, Web]
- **USFWS National Wetlands Inventory**: Produced on a decadal basis, these reports inform decision-makers and the public on the status of the nation's wetlands as well as potential causes and implications of wetland change. [DOC022, Web]
- **DocumentCloud Wetland Search**: Construction Wetland Habitat Fill material placed in wetlands during construction would result in the permanent loss of wetlands, associated vegetation, and any habitat that the wetland provides for fish and wildlife. [DOC035, pp. 167–168]
- **State Wildlife Action Plans Report with State Summaries**: Development of tax incentives and disincentives, easements, and cooperative management programs is crucial to the achievement of this task. [DOC013, pp. 171–172]
- **USFWS Library**: Fish and Wildlife Service is the principal federal agency tasked with providing information to the public on the extent and status of the nation’s wetland and deepwater habitats, as well as changes to these habitats over time. [DOC028, Web]
- **Missouri Wetlands Information**: As a transition zone between land and aquatic habitats (such as lakes, streams, and rivers), wetlands have one or more of these characteristics: At least periodically, the wetland is dominated by aquatic plants (hydrophytes). [DOC025, Web]

### Citations

[DOC002, pp. 16–20], [DOC023, Web], [DOC022, Web], [DOC035, pp. 167–168], [DOC013, pp. 171–172], [DOC028, Web], [DOC025, Web]

### Retrieved evidence

- **Missouri Wetland Program Plan** — DOC002, 16-20; similarity 0.683. K-12 classes where the importance of wetlands is presented to students.
  https://www.epa.gov/system/files/documents/2024-06/missouri_wetland-program-plan-20240117-cw.pdf
- **EPA Wetlands Program** — DOC023, Web; similarity 0.682. The protection of wetlands is supported by various Clean Water Act programs and the EPA's initiatives.
  https://www.epa.gov/wetlands
- **USFWS National Wetlands Inventory** — DOC022, Web; similarity 0.640. Produced on a decadal basis, these reports inform decision-makers and the public on the status of the nation's wetlands as well as potential causes and implications of wetland change.
  https://www.fws.gov/program/national-wetlands-inventory
- **DocumentCloud Wetland Search** — DOC035, 167-168; similarity 0.628. Construction Wetland Habitat Fill material placed in wetlands during construction would result in the permanent loss of wetlands, associated vegetation, and any habitat that the wetland provides for fish and wildlife.
  https://www.documentcloud.org/public/search?q=wetland
- **State Wildlife Action Plans Report with State Summaries** — DOC013, 171-172; similarity 0.625. Development of tax incentives and disincentives, easements, and cooperative management programs is crucial to the achievement of this task.
  https://www.fishwildlife.org/application/files/6415/1856/1631/StateWildlifeActionPlansReportwithStateSummaries.pdf
- **USFWS Library** — DOC028, Web; similarity 0.612. Fish and Wildlife Service is the principal federal agency tasked with providing information to the public on the extent and status of the nation’s wetland and deepwater habitats, as well as changes to these habitats over time.
  https://www.fws.gov/library
- **Missouri Wetlands Information** — DOC025, Web; similarity 0.607. As a transition zone between land and aquatic habitats (such as lakes, streams, and rivers), wetlands have one or more of these characteristics: At least periodically, the wetland is dominated by aquatic plants (hydrophytes).
  https://mdc.mo.gov/discover-nature/habitats/wetlands

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 5. What public documents mention waterfowl conservation?

**Heuristic status:** PASS

### Generated answer

The most relevant corpus evidence is:
- **North American Waterfowl Management Plan Update**: Thus, if waterfowl populations are to be sustained, conservation efforts must continually be adjusted. [DOC003, pp. 6–9]
- **NAWMP Value Proposition**: Since 1986, the Plan has been a catalyst for sustaining abundant waterfowl populations by conserving landscapes through public-private partnerships guided by sound science. [DOC004, pp. 1–3]
- **Ducks Unlimited Conservation Resources**: Learn More For People Conservation for waterfowl benefits hunters, anglers, hikers, and all society by expanding recreational opportunities, promoting productive ecosystems, and protecting open spaces, while also cleaning our water and safeguarding our communities. [DOC021, Web]
- **State Wildlife Action Plans Report with State Summaries**: Eastern red bat, Timber rattlesnake, Whip- poor-will, Bobcat Development or conversion of habitat into home lots, roads, businesses, etc.; resulting fragmentation degrades quality of remaining habitat. [DOC013, pp. 158–161]
- **USFWS Migratory Birds Program**: Fish and Wildlife Service to reduce bird collisions Spring migration is winding down and many of our favorite birds have returned to back yard feeders for their summer stay. [DOC026, Web]
- **MDC Management Plans**: Then A and B pool could be closed 2019 Schell-Osage Conservation Area Management Plan Page 25 while the remaining pools are re-opened. [DOC019, pp. 24–25]
- **North American Waterfowl Management Plan Update**: The North American Waterfowl Management Plan—A Conservation Legacy 1 The Changing Context of Waterfowl Conservation 3 Evolution of Waterfowl Conservation in North America. [DOC003, p. 5]

### Citations

[DOC003, pp. 6–9], [DOC004, pp. 1–3], [DOC021, Web], [DOC013, pp. 158–161], [DOC026, Web], [DOC019, pp. 24–25], [DOC003, p. 5]

### Retrieved evidence

- **North American Waterfowl Management Plan Update** — DOC003, 6-9; similarity 0.677. Thus, if waterfowl populations are to be sustained, conservation efforts must continually be adjusted.
  https://www.fws.gov/sites/default/files/documents/2024-04/1445.pdf
- **NAWMP Value Proposition** — DOC004, 1-3; similarity 0.631. Since 1986, the Plan has been a catalyst for sustaining abundant waterfowl populations by conserving landscapes through public-private partnerships guided by sound science.
  https://nawmp.org/sites/default/files/2022-03/NAWMP%20Value%20Prop%20Abbreviated%20version%202016%20FINAL_sm.pdf
- **Ducks Unlimited Conservation Resources** — DOC021, Web; similarity 0.576. Learn More For People Conservation for waterfowl benefits hunters, anglers, hikers, and all society by expanding recreational opportunities, promoting productive ecosystems, and protecting open spaces, while also cleaning our water and safeguarding our communities.
  https://www.ducks.org/conservation
- **State Wildlife Action Plans Report with State Summaries** — DOC013, 158-161; similarity 0.575. Eastern red bat, Timber rattlesnake, Whip- poor-will, Bobcat Development or conversion of habitat into home lots, roads, businesses, etc.; resulting fragmentation degrades quality of remaining habitat.
  https://www.fishwildlife.org/application/files/6415/1856/1631/StateWildlifeActionPlansReportwithStateSummaries.pdf
- **USFWS Migratory Birds Program** — DOC026, Web; similarity 0.550. Fish and Wildlife Service to reduce bird collisions Spring migration is winding down and many of our favorite birds have returned to back yard feeders for their summer stay.
  https://www.fws.gov/program/migratory-birds
- **MDC Management Plans** — DOC019, 24-25; similarity 0.545. Then A and B pool could be closed 2019 Schell-Osage Conservation Area Management Plan Page 25 while the remaining pools are re-opened.
  https://mdc.mo.gov/wildlife/mdc-management-plans
- **North American Waterfowl Management Plan Update** — DOC003, 5; similarity 0.658. The North American Waterfowl Management Plan—A Conservation Legacy 1 The Changing Context of Waterfowl Conservation 3 Evolution of Waterfowl Conservation in North America.
  https://www.fws.gov/sites/default/files/documents/2024-04/1445.pdf

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 6. What is the relationship between invasive carp and aquatic habitat management?

**Heuristic status:** PASS

### Generated answer

The structured extraction found no direct `species_uses_habitat` relation for invasive carp, so co-mention is not treated as proof of habitat use. Retrieved evidence connects invasive-carp research and management with aquatic systems as follows:
- Geological Survey Invasive Carp Science 7 Deterrents One factor that likely contributes significantly to the inva- siveness of invasive carp is their mobility (Vallazza and oth- ers, 2020; Coulter and others, 2022). [DOC012, pp. 14–15]
- Stohlgren TJ, Folfelder KA, Graham J, Waller DM (2011) Assessing citizen science data quality: an invasive species case study. [DOC011, p. 11]
- Like terrestrial habitat systems, aquatic systems are extremely vulnerable to the effects of invasive species, especially due to the high connectivity of most aquatic systems. [DOC001, pp. 170–172]
- Invasive carp, such as Hypophthalmichthys molatrix (silver carp), also received mention by multiple agencies (3 of the 10 stakeholder groups) because these fish represent priority AIS in nearby watersheds and a threat for introduction and dis- semination within the Chesapeake Bay watershed from these neighboring regions. [DOC005, pp. 13–14]
- Chapman, D.C., 2020, “Modified Unified Method” of carp capture: U.S. [DOC012, pp. 28–30]

### Citations

[DOC012, pp. 14–15], [DOC011, p. 11], [DOC001, pp. 170–172], [DOC005, pp. 13–14], [DOC012, pp. 28–30]

### Retrieved evidence

- **Invasive Carp Strategic Science Plan** — DOC012, 14-15; similarity 0.725. Geological Survey Invasive Carp Science 7 Deterrents One factor that likely contributes significantly to the inva- siveness of invasive carp is their mobility (Vallazza and oth- ers, 2020; Coulter and others, 2022).
  https://www.govinfo.gov/content/pkg/GOVPUB-I19-PURL-gpo224710/pdf/GOVPUB-I19-PURL-gpo224710.pdf
- **USGS Nonindigenous Aquatic Species Database Paper** — DOC011, 11; similarity 0.671. Stohlgren TJ, Folfelder KA, Graham J, Waller DM (2011) Assessing citizen science data quality: an invasive species case study.
  https://pdfs.semanticscholar.org/8a85/a4db10dd8eb5a9fea35094ac9885e5e9974b.pdf
- **Missouri State Wildlife Action Plan** — DOC001, 170-172; similarity 0.652. Like terrestrial habitat systems, aquatic systems are extremely vulnerable to the effects of invasive species, especially due to the high connectivity of most aquatic systems.
  https://www.mdc.mo.gov/sites/default/files/2020-04/SWAP_0.pdf
- **Aquatic Invasive Species in the Chesapeake Bay Watershed** — DOC005, 13-14; similarity 0.635. Invasive carp, such as Hypophthalmichthys molatrix (silver carp), also received mention by multiple agencies (3 of the 10 stakeholder groups) because these fish represent priority AIS in nearby watersheds and a threat for introduction and dis- semination within the Chesapeake Bay watershed from these neighboring regions.
  https://pubs.usgs.gov/of/2020/1057/ofr20201057.pdf
- **Invasive Carp Strategic Science Plan** — DOC012, 28-30; similarity 0.719. Chapman, D.C., 2020, “Modified Unified Method” of carp capture: U.S.
  https://www.govinfo.gov/content/pkg/GOVPUB-I19-PURL-gpo224710/pdf/GOVPUB-I19-PURL-gpo224710.pdf
- **USGS Nonindigenous Aquatic Species Database Paper** — DOC011, 10-11; similarity 0.654. 2014), and national policy making (silver carp listing in the Lacey Act) (U.S.
  https://pdfs.semanticscholar.org/8a85/a4db10dd8eb5a9fea35094ac9885e5e9974b.pdf

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 7. Which documents are most relevant to Missouri conservation planning?

**Heuristic status:** PASS

### Generated answer

The most relevant corpus evidence is:
- **Missouri State Wildlife Action Plan**: The CCS is a process that identifies Missouri conserva- tion priorities to inform decision-making regarding the greatest opportunities for sustainable conservation of fish, forest, and wildlife. [DOC001, pp. 17–18]
- **MDC Annual Review FY2021**: The Missouri Comprehensive Conservation Strategy (CCS) integrates the Missouri State Wildlife Action Plan, Forest Action Plan, and other conservation priorities into a comprehensive plan, meeting the requirements of both the U.S. [DOC018, Web]
- **MDC Annual Review FY2024**: Missouri Comprehensive Conservation Strategy In FY23, MDC reestablished the Comprehensive Conservation Strategy (CCS) working group, which provides guidance to CCS implementation. [DOC016, Web]
- **State Wildlife Action Plans Report with State Summaries**: Missouri’s planning approach Utilizing wildlife information gathered over the past 30 years, Missouri’s Comprehensive Wildlife Strat- egy promotes management that beneﬁ ts all wildlife, rather than targeting sin- gle species. [DOC013, pp. 139–141]
- **MDC Management Plans**: Guidelines for avoiding and minimizing impacts to federally-listed bats on Missouri Department of Conservation lands. [DOC019, pp. 17–24]
- **MDC Annual Review FY2023**: Missouri Comprehensive Conservation Strategy During this past year, 19 regional Comprehensive Conservation Strategy (CCS) trainings were provided to over 350 managers, technicians, and supervisors. [DOC017, Web]
- **Missouri Conservation Report**: Missouri’s CCS embraces landscape- scale conservation informed by natural community and wildlife diversity needs, working to maintain, enhance, restore, and re -create healthy natural systems. [DOC015, pp. 5–6]

### Citations

[DOC001, pp. 17–18], [DOC018, Web], [DOC016, Web], [DOC013, pp. 139–141], [DOC019, pp. 17–24], [DOC017, Web], [DOC015, pp. 5–6]

### Retrieved evidence

- **Missouri State Wildlife Action Plan** — DOC001, 17-18; similarity 0.740. The CCS is a process that identifies Missouri conserva- tion priorities to inform decision-making regarding the greatest opportunities for sustainable conservation of fish, forest, and wildlife.
  https://www.mdc.mo.gov/sites/default/files/2020-04/SWAP_0.pdf
- **MDC Annual Review FY2021** — DOC018, Web; similarity 0.716. The Missouri Comprehensive Conservation Strategy (CCS) integrates the Missouri State Wildlife Action Plan, Forest Action Plan, and other conservation priorities into a comprehensive plan, meeting the requirements of both the U.S.
  https://mdc.mo.gov/magazines/missouri-conservationist/2023-01/annual-review
- **MDC Annual Review FY2024** — DOC016, Web; similarity 0.692. Missouri Comprehensive Conservation Strategy In FY23, MDC reestablished the Comprehensive Conservation Strategy (CCS) working group, which provides guidance to CCS implementation.
  https://mdc.mo.gov/magazines/missouri-conservationist/2025-01/annual-review-fiscal-year-july-1-2023-june-30-2024
- **State Wildlife Action Plans Report with State Summaries** — DOC013, 139-141; similarity 0.669. Missouri’s planning approach Utilizing wildlife information gathered over the past 30 years, Missouri’s Comprehensive Wildlife Strat- egy promotes management that beneﬁ ts all wildlife, rather than targeting sin- gle species.
  https://www.fishwildlife.org/application/files/6415/1856/1631/StateWildlifeActionPlansReportwithStateSummaries.pdf
- **MDC Management Plans** — DOC019, 17-24; similarity 0.669. Guidelines for avoiding and minimizing impacts to federally-listed bats on Missouri Department of Conservation lands.
  https://mdc.mo.gov/wildlife/mdc-management-plans
- **MDC Annual Review FY2023** — DOC017, Web; similarity 0.654. Missouri Comprehensive Conservation Strategy During this past year, 19 regional Comprehensive Conservation Strategy (CCS) trainings were provided to over 350 managers, technicians, and supervisors.
  https://mdc.mo.gov/magazines/missouri-conservationist/2024-01/annual-review-fiscal-year-2023
- **Missouri Conservation Report** — DOC015, 5-6; similarity 0.613. Missouri’s CCS embraces landscape- scale conservation informed by natural community and wildlife diversity needs, working to maintain, enhance, restore, and re -create healthy natural systems.
  https://irp.cdn-website.com/92033df0/files/uploaded/mo_rpt25.pdf

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 8. Generate a short cited summary of wetland conservation evidence in the corpus.

**Heuristic status:** PASS

### Generated answer

The corpus highlights several complementary approaches to wetland conservation:
- **Protection and restoration.** EPA conservation programs pair wetland protection with restoration initiatives across its regions. [DOC023, Web]
- **Monitoring and assessment.** Monitoring and assessment track wetland status and change so decision-makers can understand causes and implications. [DOC022, Web]
- **Ecological and community benefits.** Wetlands filter water, protect communities from floods, and provide habitat for fish and other wildlife. [DOC029, Web]

### Citations

[DOC023, Web], [DOC022, Web], [DOC029, Web]

### Retrieved evidence

- **EPA Wetlands Program** — DOC023, Web; similarity 0.686. Learn about the EPA's Programs Protecting Wetlands Find more on the EPA's efforts for wetlands protection and restoration through case studies from the EPA's 10 Regions.
  https://www.epa.gov/wetlands
- **USFWS National Wetlands Inventory** — DOC022, Web; similarity 0.682. Produced on a decadal basis, these reports inform decision-makers and the public on the status of the nation's wetlands as well as potential causes and implications of wetland change.
  https://www.fws.gov/program/national-wetlands-inventory
- **NOAA Habitat Conservation** — DOC029, Web; similarity 0.564. Coastal Wetlands Wetlands filter our water, protect our coastal communities from floods, and provide habitat for fish and other wildlife—but they’re quickly disappearing.
  https://www.fisheries.noaa.gov/topic/habitat-conservation

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 9. What wiki pages were generated for species, habitats, threats, and agencies?

**Heuristic status:** PASS

### Generated answer

The generated wiki currently contains:
- **agency:** Missouri Department of Conservation, U.S. Army Corps of Engineers, U.S. Department of the Interior, U.S. Fish and Wildlife Service. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **habitat:** forest. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **location:** Great Lakes, Missouri. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **species:** invasive carp, silver carp, zebra mussel. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **threat:** climate change, habitat loss, invasive species. [DOC001, pp. 1–8] [DOC003, pp. 1–5]
- **wetland:** marsh, wetland. [DOC001, pp. 1–8] [DOC003, pp. 1–5]

### Citations

[DOC001, pp. 1–8], [DOC003, pp. 1–5]

### Retrieved evidence

- **Missouri State Wildlife Action Plan** — DOC001, 1-8; similarity 1.000. Missouri State Wildlife Action Plan Missouri Department of Conservation Conserving healthy fish, forests, and wildlife 2015 Missouri State Wildlife Action Plan 2015 Missouri is a national leader in fish, forest, and wildlife conservation due to Missouri citizens’ unique and proactive support of conservation efforts.
  https://www.mdc.mo.gov/sites/default/files/2020-04/SWAP_0.pdf
- **North American Waterfowl Management Plan Update** — DOC003, 1-5; similarity 1.000. Department of the Interior, Fish and Wildlife Service SEMARNAP Mexico SEMARNAP MÉXICO Environnement Canada Service canadien de la faune Environment Canada Canadian Wildlife Service Contents Preface . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . v Acknowledgements. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .…
  https://www.fws.gov/sites/default/files/documents/2024-04/1445.pdf
- **USGS Nonindigenous Aquatic Species Database Paper** — DOC011, 3-4; similarity 0.535. The reference database is open to public query http://nas.er.usgs.gov/queries/references/default.aspx) by any field in a citation (author, title, journal, etc.), as well as key words.
  https://pdfs.semanticscholar.org/8a85/a4db10dd8eb5a9fea35094ac9885e5e9974b.pdf
- **State Wildlife Action Plans Report with State Summaries** — DOC013, 75-77; similarity 0.517. This approach to the overall planning and strategy development was chosen in the recognition that conserv- ing and protecting Hawaii’s unique native wildlife and habitats for future genera- tions is everyone’s responsibility, duty, and honor.
  https://www.fishwildlife.org/application/files/6415/1856/1631/StateWildlifeActionPlansReportwithStateSummaries.pdf
- **Invasive Species Accomplishments Report** — DOC007, 22-24; similarity 0.503. The SEINeD is a tool that enables users to screen and link datasets for occurrences of non-native and invasive aquatic species tracked by the NAS Database.
  https://www.doi.gov/media/document/invasive-species-accomplishments-report-2021-2025
- **Missouri State Wildlife Action Plan** — DOC001, 22-24; similarity 0.458. The Department’s interdivisional Wildlife Diversity Team is currently refining a process for prioritizing species inventory needs to better focus available resources.
  https://www.mdc.mo.gov/sites/default/files/2020-04/SWAP_0.pdf
- **USGS Nonindigenous Aquatic Species Database Paper** — DOC011, 4-6; similarity 0.521. The primary information products of the NAS database are summary factsheets on spec ies’ biology, ecology, and impacts, and records of species occurrences presented both in tabular format and distribution maps.
  https://pdfs.semanticscholar.org/8a85/a4db10dd8eb5a9fea35094ac9885e5e9974b.pdf
- **State Wildlife Action Plans Report with State Summaries** — DOC013, 58-60; similarity 0.489. Connecticut’s plan identiﬁ es 43 threats to wildlife species and their habitats.
  https://www.fishwildlife.org/application/files/6415/1856/1631/StateWildlifeActionPlansReportwithStateSummaries.pdf

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.

## 10. What important questions remain unanswered by this corpus?

**Heuristic status:** PASS

### Generated answer

The current evidence leaves several recurring questions open:
- Which findings remain current, especially where reports describe plans rather than measured outcomes? [DOC032, pp. 34–35]

### Citations

[DOC032, pp. 34–35]

### Retrieved evidence

- **DocumentCloud Environment Project Search** — DOC032, 34-35; similarity 0.319. 341 In its guidelines to data preservation, the IAEA recommends an assessment of records for their level of importance (e.g., critical, necessary, or useful) to ensure appropriate resources go towards the preservation of important documents.
  https://www.documentcloud.org/public/search/project:environment

### Notes

- Deterministic answer, evidence, and citations passed automated integrity checks; AI synthesis was not evaluated.
