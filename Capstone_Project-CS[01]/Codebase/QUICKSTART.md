# Quick Start Guide - CV Creation Using LLM

## 🚀 Get Started in 5 Minutes

### Step 1: Create Virtual Environment (1 minute)

**On Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 2: Install Dependencies (1 minute)
```bash
pip install -r requirements.txt
```

### Step 3: Configure API Key (1 minute)
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Replace: your_openai_api_key_here
# With: sk-your-actual-openai-api-key
```

On Linux/Mac:
```bash
nano .env
```

On Windows:
```bash
notepad .env
```

### Step 4: Run with Sample Data (2 minutes)
```bash
python main.py
```

**Follow these prompts:**
1. Select: `1` (Complete workflow)
2. Resume path: `input/profiles/sample_resume.txt`
3. Job option: `1` (Load from file)
4. Job path: `input/jobs/sample_job.txt`
5. Continue: `y`
6. Review: `n` (for quick test, or `y` to try revision)
7. Export: `3` (Both PDF and DOCX)

**Expected Output:**
- The system will process the sample resume and job description
- Generate a tailored resume optimized for the job
- Export PDF and DOCX files to the `output/` folder
- Total time: ~30-60 seconds

### Step 5: View Results
```bash
ls output/
```

You should see:
- `sample_resume_extracted.json` - Extracted profile data
- `job_parsed.json` - Parsed job requirements
- `john_doe_senior_backend_engineer_resume.json` - Generated resume
- `john_doe_senior_backend_engineer_resume.pdf` - PDF output
- `john_doe_senior_backend_engineer_resume.docx` - DOCX output

---

## 🎯 Use with Your Own Resume

### Option 1: Your Resume + Sample Job
```bash
python main.py
# Select 1
# Enter: /path/to/your/resume.pdf
# Select 1
# Enter: input/jobs/sample_job.txt
```

### Option 2: Your Resume + Your Job
```bash
# First, create a job description file
nano input/jobs/my_job.txt
# Paste the job description and save

# Then run
python main.py
# Select 1
# Enter: /path/to/your/resume.pdf
# Select 1
# Enter: input/jobs/my_job.txt
```

### Option 3: Paste Job Description
```bash
python main.py
# Select 1
# Enter: /path/to/your/resume.pdf
# Select 2 (Paste job description)
# Paste the full job description
# Type END on a new line
```

---

## 💡 Tips for Best Results

### Resume Files
✅ **Good:**
- PDF files with extractable text
- Word documents (.docx)
- Plain text files (.txt)

❌ **Avoid:**
- Scanned PDFs (images)
- Password-protected files
- Heavily formatted tables

### Job Descriptions
✅ **Include:**
- Full job title
- Required qualifications
- Job responsibilities
- Technical skills needed
- Preferred qualifications

❌ **Don't:**
- Use partial or incomplete descriptions
- Skip required qualifications section
- Omit technical skills

### ATS Optimization
- Target score: **75+** for good compatibility
- Run Feature 4 (Revision) to improve scores
- Add missing keywords naturally
- Use simple, clean formatting

---

## 🔧 Quick Troubleshooting

### "OpenAI API key not configured"
```bash
# Check .env file exists
ls -la .env

# Verify it contains your key
cat .env | grep OPENAI_API_KEY
```

### "ModuleNotFoundError"
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### "No text extracted from PDF"
```bash
# Convert to text first
# Option 1: Use an online PDF to TXT converter
# Option 2: Copy-paste into a .txt file manually
```

---

## 📊 Understanding the Output

### ATS Score (0-100)
- **85-100**: ✅ Excellent - Ready to apply
- **70-84**: ✓ Good - Minor tweaks recommended
- **50-69**: ⚠️ Fair - Needs keyword optimization
- **Below 50**: ❌ Poor - Significant revision needed

### Keyword Match (%)
Shows what percentage of job keywords appear in your resume.
- **70%+**: Strong keyword coverage
- **50-69%**: Moderate coverage
- **Below 50%**: Add more relevant keywords

### Match Score (0-100)
Shows overall fit between your profile and the job.
- **80+**: Strong match - Apply confidently
- **60-79**: Good match - Tailor resume
- **40-59**: Moderate match - Significant tailoring needed
- **Below 40**: Weak match - Consider if role is right fit

---

## 🎓 Learning the Features

### Individual Feature Testing

**Extract resume data only:**
```bash
python extractor.py
# Input: Your resume file
# Output: Structured JSON with all info
```

**Parse job description only:**
```bash
python parser.py
# Input: Job description
# Output: Structured requirements and keywords
```

**Check profile-job match:**
```bash
python matcher.py
# Input: Profile JSON + Job JSON
# Output: Match score and analysis
```

**Generate tailored resume:**
```bash
python generator.py
# Input: Profile JSON + Job JSON
# Output: Optimized resume content
```

**Get ATS feedback:**
```bash
python ats_checker.py
# Input: Resume JSON + Job JSON
# Output: ATS score and suggestions
```

---

## 📝 Next Steps

1. ✅ Run with sample data to verify setup
2. ✅ Test with your own resume
3. ✅ Try the revision feature to improve ATS scores
4. ✅ Experiment with different job descriptions
5. ✅ Export in both PDF and DOCX formats
6. ✅ Read the full README.md for advanced features

---

## 🆘 Need Help?

1. **Read the full README.md** for comprehensive documentation
2. **Check execution.txt** for detailed command examples
3. **Verify all prerequisites** are met (Python 3.8+, API key, dependencies)
4. **Test with sample data first** to ensure everything works

---

## 📈 Cost Estimate

Using the sample data:
- **Extraction**: ~$0.001
- **Parsing**: ~$0.001
- **Generation**: ~$0.02-0.03
- **Revision**: ~$0.01 per iteration
- **Total**: ~$0.03-0.05 per complete workflow

Actual costs may vary based on resume and job description length.

---

## 🔄 Virtual Environment Management

### Activating the Environment
Before running any Python commands, always activate:

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

### Deactivating the Environment
When you're done working:

```bash
deactivate
```

### Checking if Activated
Look for `(venv)` prefix in your terminal:
```bash
(venv) ➜  Codebase
```

### Reinstalling Dependencies
If you encounter issues:

```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt --force-reinstall
```

---

**Ready to create your ATS-optimized resume? Run: `python main.py`**
