# FactCheck – Automated Claim Verification System

### A full-stack NLP project for real-time fact-checking using AI.

**FactCheck** is an intelligent system that verifies the credibility of textual claims by combining:
- **Web search and evidence retrieval** from trusted online sources  
- **Natural Language Inference (NLI)** using state-of-the-art transformer models  
- **Heuristic credibility scoring** based on source reliability, recency, and coverage  

The user submits a claim, and the system:
1. Searches for relevant sources online  
2. Extracts and analyzes their content  
3. Uses an NLI model to detect support or contradiction  
4. Computes a weighted credibility score and displays it with evidence cards

---

## Tech Stack

**Backend:**  
Python, FastAPI, HuggingFace Transformers, BeautifulSoup4, Trafilatura, Serper.dev API  

**Frontend:**  
React, TailwindCSS  

---

##  Key Features
- Real-time claim verification via REST API  
- Integrated web search & scraping pipeline  
- Multilingual NLI model support (English/Hebrew)  
- Interactive, modern UI with credibility gauge  
- Weighted scoring system (AI + heuristics)  


## Future Improvements
-Enhanced source relevance filtering
-Browser extension integration – prepare the system to work as an in-browser fact-checking plugin
-User accounts and personalization – allow users to create accounts and save articles they’re interested in
-Visualization of evidence contribution – show how each source contributes to the overall score

