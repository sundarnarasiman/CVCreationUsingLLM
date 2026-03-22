# CV Creation Using Dual-LLM System - Viva Prep Sheet

## How to Use This Sheet
- Keep answers short, technical, and honest.
- Do not oversell the system as flawless or fully production-deployed.
- Emphasize architecture, engineering choices, validation, and limitations.
- When possible, answer in this pattern: problem -> design choice -> result -> limitation.

## 1. What problem does your project solve?
Model answer:
This project solves the problem of manually tailoring resumes for different job descriptions. Many candidates fail ATS screening because their resumes are not aligned with the target role in keywords, structure, or emphasis. My system automates resume extraction, job parsing, profile-job matching, ATS scoring, resume generation, iterative revision, and final export into PDF and DOCX.

## 2. Why is this a capstone-level project and not just a simple LLM application?
Model answer:
It is not a single-prompt application. It is a multi-stage pipeline with modular components: extractor, parser, matcher, generator, ATS checker, reviser, formatter, and orchestration layer. It also includes semantic similarity with embeddings, threshold-based chunking, structured merge logic, revision loops, testing, and documentation. So the project demonstrates software engineering, NLP pipeline design, and AI integration together.

## 3. Why did you use a dual-LLM design?
Model answer:
I used a dual-LLM design to balance cost and quality. GPT-4o-mini is used for extraction and parsing because those steps are more structured and cost-sensitive. GPT-4o is used for strategy generation and resume writing because those tasks require better reasoning and content quality. This reduces cost while preserving output quality where it matters most.

## 4. What is the end-to-end workflow of the system?
Model answer:
The workflow is: resume extraction from PDF, DOCX, or TXT; job description parsing; profile-job match scoring; tailored resume generation; optional iterative revision with ATS feedback; and final export to JSON, PDF, and DOCX. The main orchestration module connects all these steps in a menu-driven workflow.

## 5. Why did you include profile-job matching before generation?
Model answer:
The matching step gives an initial estimate of how suitable the candidate is for the target role before generating the final resume. This is useful because if the fit is very low, the system can warn the user instead of generating misleading output. It also improves transparency because the user sees a numerical fit score before generation starts.

## 6. Why did you use semantic matching instead of only exact keyword overlap?
Model answer:
Exact keyword overlap is too rigid because related skills may not use identical wording. For example, a job may mention distributed systems while a profile mentions microservices, or machine learning versus deep learning. By using embeddings and cosine similarity, the system can detect semantically related skills and produce a more realistic match score and ATS analysis.

## 7. How does your ATS scoring work?
Model answer:
The ATS score is a weighted composite score out of 100. It includes keyword match, formatting, section completeness, and content quality. Keyword match is the largest part and uses a hybrid exact-plus-semantic process. The system first checks exact overlap, and if that is insufficient, it performs semantic analysis with embeddings and produces a blended final keyword match percentage.

## 8. Why did you add chunking, and when is it used?
Model answer:
Chunking is used to handle larger resumes or job descriptions that may exceed practical prompt size or reduce extraction quality if processed in one pass. The system first attempts section-aware chunking, and if sections are still too large, it applies bounded chunking with overlap. Then it merges the structured outputs carefully. This makes the system more robust for long inputs.

## 9. How do you ensure the generated resume is not hallucinated or misleading?
Model answer:
I reduce this risk in three ways. First, the system extracts structured information from the source resume instead of generating from scratch. Second, the strategy and generation steps are conditioned on the extracted profile and parsed job data. Third, the revision loop allows the user to inspect, edit, and improve the result before final export. That said, the system is still AI-assisted, so human review is necessary before using the final resume.

## 10. What testing did you do to validate the project?
Model answer:
The project currently has 53 passing automated tests. The tests cover extraction and parsing edge cases, chunking behavior, merge logic, formatting, generator and reviser behavior, n-gram phrase detection, ATS keyword scoring, validation, and error handling. This shows that the system is not only functional in demos but also tested at module level.

## 11. What are the strongest technical contributions in your project?
Model answer:
The strongest technical contributions are the dual-LLM orchestration, semantic similarity matching with OpenAI embeddings, frequency-weighted keyword handling, curated multi-word phrase detection, threshold-based chunking with structured merge, iterative ATS-guided revision, and multi-format export. Together these features make the project more sophisticated than a basic LLM wrapper.

## 12. What limitations does your project currently have?
Model answer:
The main limitations are dependency on the OpenAI API and internet connectivity, sensitivity to input quality, heuristic ATS scoring rather than official vendor scoring, and the need for human review of generated content. Also, while the project is well tested functionally, it does not yet include a large benchmark dataset or comparative evaluation against commercial tools.

## 13. If an examiner asks whether this is production-ready, how should you answer?
Model answer:
I would say it is functionally complete and well engineered as a capstone prototype, but I would not claim it is fully production-ready in the enterprise sense. To become production-grade, it would need stronger benchmarking, security hardening, API rate-limit handling strategy, usage analytics, multi-user deployment support, and broader evaluation across real datasets.

## 14. What would you improve next if you had more time?
Model answer:
The next improvements would be a web interface or REST API, structured experiment tracking, an offline-safe demo mode, larger benchmark-based evaluation, multilingual support, and better reporting dashboards for ATS and profile-job analysis. I would also add stronger comparative metrics such as before-versus-after ATS score improvements across multiple resumes and job roles.

## 15. What is the main takeaway or value of your capstone?
Model answer:
The main takeaway is that this project demonstrates how LLMs can be integrated into a real software pipeline to solve a practical problem in a structured and measurable way. It combines AI capability with engineering discipline: modular architecture, validation, scoring, testing, documentation, and user-facing outputs. That is what makes it a strong capstone project.

## Fast Defense Notes
- Say "capstone prototype" instead of "fully production-ready" unless specifically asked about future deployment.
- Say "heuristic ATS score" rather than "official ATS score".
- Say "AI-assisted resume optimization" rather than "fully automatic perfect resume generation".
- Emphasize 53 passing tests, modular design, semantic matching, chunking, and revision loop.
- Acknowledge limitations early; this usually increases examiner confidence.

## 30-Second Summary
This project is a dual-LLM resume optimization system that extracts structured resume data, parses job descriptions, computes profile-job match, generates tailored ATS-friendly resumes, supports iterative revision with ATS feedback, and exports final outputs in PDF and DOCX. The project goes beyond basic prompting by adding semantic matching, chunking, modular architecture, testing, and documentation.

## 60-Second Summary
This capstone project addresses the real problem of manual resume tailoring. The system takes a resume and a target job description, converts both into structured data, estimates fit using profile-job matching, generates a tailored resume using a two-step LLM strategy, provides ATS-style feedback, supports revision, and exports the final result. Architecturally, it uses a dual-LLM design for cost and quality balance, semantic similarity with embeddings for better keyword matching, and chunking plus merge logic for larger documents. It is supported by 53 passing automated tests and full project documentation.
