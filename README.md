# cv-builder

A Python CLI tool for building professional CVs and getting personalised job role recommendations.

## Features

- Interactive multi-stage questionnaire (personal info, education, work experience, skills, projects, additional info, job preferences)
- PDF and plain-text CV generation
- Personalised job role recommendations with match scores and skill gap analysis
- Saves progress automatically so you can resume at any time

## Requirements

- Python 3.10+
- Dependencies: `fpdf2`, `rich`, `pydantic` (see `requirements.txt`)

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Run the interactive CLI

```bash
python -m cv_builder
```

or, after installation:

```bash
cv-builder
```

The tool will guide you through 7 stages:
1. Personal Information
2. Education
3. Work Experience
4. Skills (technical, soft, languages, certifications)
5. Projects
6. Additional Information
7. Job Preferences

At the end it generates your CV as PDF and/or plain text, and shows personalised job recommendations.

## Running tests

```bash
pip install pytest
pytest tests/
```
