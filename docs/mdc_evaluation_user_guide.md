# Conservation Document Intelligence Prototype

## MDC Evaluation and User Guide

**Web application:** https://shanged-conservation-intelligence.hf.space/  
**Current status:** Experimental research prototype  
**Current document collection:** 35 public conservation sources  

## 1. What is the prototype?

The Conservation Document Intelligence Prototype is an experimental research tool that explores how artificial intelligence and document-search methods might help people find, organize, and understand information distributed across conservation documents.

The current prototype uses a limited collection of public reports, plans, agency webpages, and related conservation records. It lets users browse the collection, search for relevant evidence, explore Wiki-style summaries, ask questions in everyday language, and follow citations back to source documents.

The prototype is intended for evaluation and learning. It is not an official Missouri Department of Conservation information system, policy source, or decision-support system.

## 2. Why are we developing it?

Useful conservation information is often distributed across many management plans, agency reports, program documents, scientific summaries, and public webpages. Finding an answer can require knowing which organization produced a document, what terminology it used, and where relevant information appears.

This prototype explores whether a document-intelligence tool can help conservation professionals:

- Find relevant documents and passages more quickly.
- Identify agencies, species, habitats, threats, programs, and locations mentioned across documents.
- Connect related information that appears in different sources.
- Organize evidence into Wiki-style knowledge pages.
- Ask natural-language questions about a document collection.
- Receive answers linked to supporting documents and locations.

The goal of MDC evaluation is not simply to test whether the website works. We also want to learn whether this approach could be useful for real conservation work and what would be required to make it trustworthy.

## 3. What has been implemented?

The web application contains five main sections.

### Corpus

Browse the 35 sources currently included in the prototype. The Corpus section shows titles, agencies, topics, source status, and basic information about the processed collection.

### Search

Search for words or concepts such as `wetland`, `invasive carp`, `waterfowl`, or `habitat restoration`. Results show the source title, document identifier, page or Web location, an evidence excerpt, and a link to the public source when available.

### Wiki

Browse 15 generated pages that organize evidence about selected agencies, species, habitats, and threats. Each page includes a summary, key facts, related documents, extracted relationships, supporting evidence, and questions that remain open.

### Chatbot

Ask a question about the current conservation document collection. Depending on the question and current configuration, the system may produce a local evidence-based response or an AI-assisted synthesis. The response mode is always identified.

### Evaluation

Review the ten standard demonstration questions and their integrity-check results. These checks confirm that answers and citations are structurally present; they are not expert judgments that every answer is scientifically complete or correct.

## 4. Important research prototype notice

Please keep the following limitations in mind throughout testing:

- This is an experimental research prototype, not an official MDC product.
- It contains only the current 35-source public document collection.
- An answer may be incomplete because relevant information is absent from the collection.
- Search results can be topically related without fully answering a question.
- AI-assisted answers may contain mistakes, omit context, or misinterpret evidence.
- Generated Wiki pages summarize extracted evidence and should not be treated as authoritative reference articles.
- Citations identify supporting source locations, but users must still decide whether the cited material actually supports the conclusion.

**Always verify important conclusions by opening and reading the cited source documents.**

Do not enter confidential, sensitive, private, or personally identifying information. When AI synthesis is enabled, the question and selected excerpts from the public document collection may be sent to OpenAI for response generation.

## 5. How to access the prototype

Open the application at:

https://shanged-conservation-intelligence.hf.space/

The current Space is private. You must be signed into a Hugging Face account that has been given access. If the page appears unavailable, confirm that you are signed into the correct account and contact the project owner rather than creating a second account or entering credentials elsewhere.

The application uses free CPU hosting and may sleep after inactivity. If it is waking up, allow approximately one minute before concluding that it is unavailable.

## 6. How to use the web application

### 6.1 Browse the Corpus

1. Select **Corpus**.
2. Confirm that the page shows 35 documents.
3. Use the agency or topic filters to narrow the list.
4. Review source titles, document identifiers, years, status, and source links.
5. Note whether the collection appears to contain the kinds of documents you would expect for your question.

Document identifiers such as `DOC002` are stable labels used throughout the prototype. They allow search results, Wiki pages, chatbot answers, and evaluation records to refer to the same source consistently.

### 6.2 Search the documents

1. Select **Search**.
2. Enter a conservation term or phrase, such as `wetland restoration`.
3. Choose the available search method and result count if you want to compare results.
4. Review the title, document ID, page or Web location, and excerpt for each result.
5. Use **Open source document** to examine the original public source.

When evaluating a result, ask whether the excerpt is directly relevant or only shares similar terminology.

### 6.3 Browse the Wiki

1. Select **Wiki**.
2. Choose an available entity type and page.
3. Read the summary and key facts.
4. Review **Related Documents**, **Related Entities**, and **Evidence**.
5. Notice the distinction between an explicit extracted relationship and simple co-occurrence.
6. Use the citations to check representative source passages.

Wiki pages are generated from the current document collection. They do not claim to describe everything known about the topic outside this corpus.

### 6.4 Ask the Chatbot

1. Select **Chatbot**.
2. Enter one clear conservation question.
3. Submit the question and allow the response to complete.
4. Read the displayed answer mode:
   - **Local response** or **Local deterministic fallback** means the answer was assembled from local evidence without AI synthesis.
   - **AI synthesis** means selected evidence was provided to an AI model to help compose the answer.
5. Review the document citations included with the claims.
6. Expand the Sources section and open the original documents.

The system may say that the corpus does not provide enough evidence. That is an appropriate research result and is preferable to an unsupported answer.

### 6.5 Check citations

A citation appears in forms such as:

```text
[DOC002, pp. 16-20]
[DOC023, Web]
```

To evaluate a citation:

1. Identify the statement immediately before the citation.
2. Expand the Sources section.
3. Confirm that the document ID and page/Web location match.
4. Open the original source.
5. Decide whether the source actually supports the statement and whether important context is missing.

A citation can be technically valid while the answer is still incomplete or too broad. Your conservation judgment is essential.

### 6.6 Review Evaluation

1. Select **Evaluation**.
2. Review the ten standard questions.
3. Expand questions that are relevant to your work.
4. Compare the deterministic and hybrid examples where available.
5. Treat a `PASS` as an integrity check, not as confirmation of scientific quality.

## 7. Example questions to try

Try several of the standard questions before asking your own:

1. What documents discuss aquatic invasive species?
2. What agencies appear most often in the corpus?
3. What are the main conservation threats mentioned across the documents?
4. What documents discuss wetlands or wetland management?
5. What public documents mention waterfowl conservation?
6. What is the relationship between invasive carp and aquatic habitat management?
7. Which documents are most relevant to Missouri conservation planning?
8. Generate a short cited summary of wetland conservation evidence in the corpus.
9. What Wiki pages were generated for species, habitats, threats, and agencies?
10. What important questions remain unanswered by this corpus?

Afterward, ask questions related to your actual conservation work. Questions that expose missing documents, terminology, geographic coverage, or management context are especially useful for this evaluation.

## 8. How we would like MDC collaborators to evaluate it

For each question you test, consider the following.

### Answer quality

- Was the response relevant to the question?
- Was it scientifically and professionally reasonable?
- Was it clear and understandable?
- Did it make claims that were too broad or too confident?
- Was important information or context missing?

### Evidence and citations

- Did the cited documents actually support the answer?
- Were the page or Web locations useful for finding the evidence?
- Did the response combine information from sources appropriately?
- Were any important contradictory or qualifying sources absent?

### Practical usefulness

- Did the system find information that would otherwise have been difficult or time-consuming to locate?
- Would this type of tool be useful in your conservation work?
- What kinds of conservation questions should a future system answer?
- What additional documents or data would make it more useful?
- What would make you trust—or not trust—an AI system for conservation information?

### Suggested feedback record

For each tested question, record:

| Field | What to record |
|---|---|
| Question | The exact question entered. |
| Answer mode | Local response, local fallback, or AI synthesis. |
| Relevance | Whether the response addressed the question. |
| Scientific reasonableness | Any statements that seemed correct, questionable, or misleading. |
| Citation support | Whether the cited passages supported the associated claims. |
| Missing information | Important documents, context, viewpoints, or caveats that were absent. |
| Usefulness | How this might help—or fail to help—real conservation work. |
| Suggested improvement | The most important change you would recommend. |

## 9. What feedback is most valuable?

The most useful feedback is specific. Instead of saying only that an answer was “good” or “bad,” identify:

- The exact question you asked.
- The sentence or claim that helped or caused concern.
- The citation you checked.
- What the source actually said.
- What information or source you expected to see.
- How the result would affect a real conservation task.

Please also report confusing labels, navigation problems, slow or failed responses, broken source links, and questions for which the system should have admitted that evidence was insufficient.

## 10. Suggested evaluation session

A useful first evaluation session can be completed in approximately 30-45 minutes:

1. Spend five minutes reviewing the Corpus.
2. Run two or three Search queries.
3. Review two Wiki pages.
4. Ask three standard Chatbot questions.
5. Ask two questions from your own work.
6. Open citations for at least two answers.
7. Record answer-quality, evidence, and usefulness feedback.
8. Identify one additional source collection or capability that would most improve the prototype.

Thank you for helping evaluate how document-intelligence methods might support conservation research and practice.
