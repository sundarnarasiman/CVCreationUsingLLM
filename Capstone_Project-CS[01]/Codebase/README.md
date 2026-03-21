# CV Creation Using LLM

A dual-LLM system for creating tailored, ATS-optimized CVs using OpenAI's GPT-4o-mini and GPT-4o models.

## 🌟 Features

### Feature 1: Resume Data Extraction
- **Input**: Unstructured resume documents (PDF, Word, TXT)
- **Process**: LLM-powered extraction using GPT-4o-mini
- **Output**: Structured JSON with personal details, education, experience, skills, projects, certifications

### Feature 2: Job Description Parsing
- **Input**: Job descriptions (file or paste)
- **Process**: LLM-powered parsing using GPT-4o-mini
- **Output**: Structured JSON with requirements, responsibilities, keywords

### Feature 3: Resume Tailoring and Generation
- **Two-Step LLM Process**:
  1. **Strategic Analysis**: GPT-4o reviews profile-job fit and creates tailoring strategy
  2. **Content Generation**: GPT-4o synthesizes personalized, keyword-rich resume content
- **Output**: ATS-optimized resume JSON with keyword coverage metrics

### Feature 4: User Review and Iterative Revision
- **Interactive editing**: Accept user edits through terminal
- **Real-time ATS feedback**: Live scoring (0-100) and keyword analysis
- **LLM refinement**: GPT-4o incorporates edits and missing keywords
- **Revision history**: Track all iterations with before/after scores

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Internet connection (for API calls)

## 🚀 Installation

### 1. Clone or Download the Project

```bash
cd Capstone_Project-CS[01]/Codebase
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `langchain==0.1.0` - LLM orchestration framework
- `langchain-openai==0.0.5` - OpenAI integration for LangChain
- `python-dotenv==1.0.0` - Environment variable management
- `pdfplumber==0.10.3` - PDF text extraction
- `python-docx==1.1.0` - Word document handling
- `fpdf2==2.7.6` - PDF generation
- `reportlab==4.0.7` - Advanced PDF formatting
- `openai==1.10.0` - OpenAI API client

### 3. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Replace 'your_openai_api_key_here' with your actual key
```

**.env file contents:**
```
OPENAI_API_KEY=sk-your-actual-api-key-here
EXTRACTION_MODEL=gpt-4o-mini
GENERATION_MODEL=gpt-4o
EXTRACTION_TEMPERATURE=0.3
GENERATION_TEMPERATURE=0.7
ATS_SCORE_THRESHOLD=75
```

## 💻 Usage

### Complete Workflow (Recommended for First-Time Users)

```bash
python main.py
```

Follow the interactive menu:
1. Select option `1` for complete workflow
2. Provide your resume file (PDF/DOCX/TXT)
3. Provide job description (file or paste)
4. Review profile-job match score
5. Wait for tailored resume generation
6. Optionally revise with ATS feedback
7. Export to PDF/DOCX

### Individual Features

You can also run features independently:

#### Feature 1: Extract Resume Data
```bash
python extractor.py
```
Input: Resume file (PDF/DOCX/TXT)
Output: `output/<filename>_extracted.json`

#### Feature 2: Parse Job Description
```bash
python parser.py
```
Input: Job description file or paste
Output: `output/job_parsed.json`

#### Feature 3: Generate Tailored Resume
```bash
python generator.py
```
Input: Extracted profile JSON + Parsed job JSON
Output: `output/<name>_<job>_resume.json`

#### Feature 4: Revise with ATS Feedback
```bash
python reviser.py
```
Input: Resume JSON + Job JSON
Output: Multiple versioned files + final resume

#### ATS Checker (Standalone)
```bash
python ats_checker.py
```
Input: Resume JSON + Job JSON
Output: ATS score and feedback

#### Profile-Job Matcher
```bash
python matcher.py
```
Input: Profile JSON + Job JSON
Output: Match score and analysis

## 📁 Project Structure

```
Codebase/
├── main.py                  # Main orchestration and menu
├── extractor.py             # Feature 1: Resume extraction
├── parser.py                # Feature 2: Job parsing
├── generator.py             # Feature 3: Resume generation
├── reviser.py               # Feature 4: Iterative revision
├── ats_checker.py           # ATS compatibility checker
├── formatters.py            # PDF/DOCX output formatters
├── matcher.py               # Profile-job matching
├── requirements.txt         # Python dependencies
├── .env.example             # Environment configuration template
├── input/
│   ├── profiles/           # Place resume files here
│   └── jobs/               # Place job descriptions here
└── output/                 # All generated files
```

## 📊 ATS Scoring System

The ATS checker evaluates resumes on a 0-100 scale:

- **Keyword Match (50 points)**: How many job keywords appear in resume
- **Formatting (25 points)**: ATS-friendly structure and layout
- **Section Completeness (15 points)**: Required sections present
- **Content Quality (10 points)**: Optimal word count and detail level

**Score Interpretation:**
- 85-100: Excellent ATS compatibility ✅
- 70-84: Good compatibility ✓
- Below 70: Needs improvement ⚠️

## 🎯 Best Practices

### Input Files

**Resumes:**
- Supported formats: PDF, DOCX, TXT
- Place files in `input/profiles/` (optional, can use any path)
- Ensure text is extractable (not scanned images)

**Job Descriptions:**
- Preferred format: Plain text (.txt)
- Can also paste directly in terminal
- Include full description with requirements and responsibilities

### Using the System

1. **Start with Complete Workflow**: Use option 1 for guided experience
2. **Check Match Score**: Review before spending time on generation
3. **Iterate on Revisions**: Use Feature 4 multiple times to optimize ATS score
4. **Target 75+ ATS Score**: This is the recommended threshold for most ATS systems
5. **Export Both Formats**: PDF for viewing, DOCX for further editing

### Cost Optimization

- **Extraction (GPT-4o-mini)**: ~$0.001-0.002 per resume
- **Parsing (GPT-4o-mini)**: ~$0.001 per job description
- **Generation (GPT-4o)**: ~$0.01-0.03 per tailored resume
- **Revision (GPT-4o)**: ~$0.01 per iteration

**Total cost per complete workflow**: Typically $0.02-0.05

## 🔧 Troubleshooting

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "OpenAI API key not configured"
- Ensure `.env` file exists in the Codebase directory
- Check that OPENAI_API_KEY is set correctly
- Verify no extra spaces or quotes around the key

### "No text could be extracted from the document"
- Ensure PDF is not a scanned image (use OCR if needed)
- Try converting to TXT manually first
- Check file is not corrupted

### "Error during extraction/generation"
- Check your OpenAI API key has available credits
- Verify internet connection
- Try with a smaller resume or simpler job description

### "ATS score is low"
- Run Feature 4 to get specific improvement suggestions
- Ensure job description is detailed and complete
- Add more relevant keywords from the job posting

## 🧪 Testing the System

### Sample Workflow Test

1. Create a sample resume in `input/profiles/sample_resume.txt`:
```
John Doe
Email: john@example.com | Phone: (555) 123-4567

EXPERIENCE
Software Engineer at Tech Corp (2020-2023)
- Developed web applications using Python and JavaScript
- Built REST APIs with Flask and Django
- Improved system performance by 40%

EDUCATION
BS Computer Science, State University (2020)

SKILLS
Python, JavaScript, React, Django, SQL, Git
```

2. Create a sample job in `input/jobs/sample_job.txt`:
```
Senior Software Engineer

REQUIREMENTS:
- 3+ years of Python development
- Experience with web frameworks (Django/Flask)
- Strong understanding of REST APIs
- Bachelor's degree in Computer Science

RESPONSIBILITIES:
- Design and implement scalable web applications
- Collaborate with cross-functional teams
- Write clean, maintainable code
```

3. Run the complete workflow:
```bash
python main.py
# Select option 1
# Provide paths when prompted
```

## 📝 Sample Output Files

After running the complete workflow, you'll see files like:

```
output/
├── sample_resume_extracted.json       # Feature 1 output
├── job_parsed.json                    # Feature 2 output
├── john_doe_senior_engineer_resume.json  # Feature 3 output
├── john_doe_senior_engineer_strategy.json # Generation strategy
├── john_doe_senior_engineer_resume_v1.json # Revision iteration 1
├── john_doe_senior_engineer_resume_final.json # Final version
├── john_doe_senior_engineer_resume_final.pdf  # PDF export
├── john_doe_senior_engineer_resume_final.docx # DOCX export
└── john_doe_senior_engineer_resume_final_ats_feedback.json
```

## 🤝 Contributing

This is a capstone project. For improvements or bug fixes, please document changes in the Report folder.

## 📄 License

See LICENSE file in the project root.

## 🎓 Academic Context

**Project**: CV Creation Using LLM  
**Course**: Capstone Project - CS[01]  
**Technology Stack**:
- LangChain for LLM orchestration
- OpenAI GPT-4o-mini (extraction/parsing)
- OpenAI GPT-4o (generation/revision)
- Python 3.8+

## 📞 Support

For issues or questions:
1. Check this README's Troubleshooting section
2. Review the execution.txt file for example workflows
3. Verify all prerequisites are met
4. Check that input files are properly formatted

---

**Last Updated**: March 2026  
**Version**: 1.0
