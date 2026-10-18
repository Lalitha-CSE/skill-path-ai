# Skill Path AI

## 🚀 Live Demo
[Click here to try Skill Path AI](https://skill-path-ai-y2ht.onrender.com)

## 📌 About the Project
Skill Path AI is a Flask-based learning assistant
that provides relevant answers from a curated knowledge base.



# Skill Path AI

AI/ML student learning companion and knowledge-based question-answering agent.

**Tagline:** Learn. Build. Grow.

Students can ask questions about Python, Artificial Intelligence, Machine
Learning, Data Science, AI projects, interview preparation, internships,
GitHub, and career roadmaps. The agent searches its local JSON knowledge base,
identifies the most relevant note using TF-IDF and cosine similarity, shows the
source note, and provides an answer based on that source.

This is a working full-stack application — not a static demo. Everything runs
locally without an API key or internet connection after dependencies are
installed.

## Folder structure

```
skill-path-ai/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore                # Git ignore rules
├── data/
│   └── knowledge.json        # Starter knowledge base (20+ notes)
├── utils/
│   ├── __init__.py
│   └── knowledge_agent.py    # TF-IDF + cosine similarity retrieval agent
├── templates/
│   ├── index.html            # Home page with Q&A interface
│   └── about.html            # About page
├── static/
│   ├── css/
│   │   └── style.css         # Styles
│   ├── js/
│   │   └── script.js         # Frontend interactivity
│   └── images/               # (reserved for future images)
└── tests/
    └── test_agent.py         # Unit tests
```

## Prerequisites

- Python 3.9 or higher (Python 3.13 recommended)
- pip (comes with Python)
- Visual Studio Code (optional, recommended)

No Node.js is required.

## Windows VS Code setup

1. Open VS Code.
2. Select **File > Open Folder** and choose `C:\KIET PROJECTS\skill path AI`.
3. Open a terminal in VS Code (**Terminal > New Terminal**).

## Virtual environment

Create and activate a virtual environment:

```powershell
# Create the virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by PowerShell execution policy, run once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then re-run the activation command.

## Install dependencies

With the virtual environment activated:

```powershell
pip install -r requirements.txt
```

## Launch the application

With the virtual environment activated:

```powershell
python app.py
```

Open your browser to:

```
http://127.0.0.1:5000
```

The About page is at `http://127.0.0.1:5000/about`.

## Run the tests

With the virtual environment activated:

```powershell
python -m unittest discover -s tests -v
```

## How to add or edit knowledge notes

Edit `data/knowledge.json`. Each note needs these fields:

- `id` — unique identifier (e.g. `py-001`)
- `topic` — short topic title
- `keywords` — comma-separated keywords used for matching
- `text` — the answer text returned to the student
- `status` — `verified` for reviewed content, `draft` for unreviewed content

Restart `python app.py` after changing the knowledge base so Flask reloads it.

## Known limitations

- Answers come only from the local starter knowledge base in `data/knowledge.json`.
- The similarity score measures textual relevance, not factual correctness.
- Some notes are marked as drafts and carry a warning.
- Roadmaps and career guidance are general suggestions, not personalized plans.
- No external AI model or paid API is used.
