import json
import re

try:
    import ollama
except ImportError:
    ollama = None

MODEL = "llama3.2"   # optional: "qwen2.5:3b" or "qwen2.5:7b" if your PC allows


# ------------------------------------------------------------
# TEXT HELPERS
# ------------------------------------------------------------

def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#]+", " ", text)
    return " ".join(text.split())


def padded(text):
    return " " + normalize(text) + " "


def find_first(text_padded, terms):
    """Return (position, term) of the earliest term found, else None."""
    best = None
    for t in terms:
        i = text_padded.find(" " + t + " ")
        if i != -1 and (best is None or i < best[0]):
            best = (i, t)
    return best


# ------------------------------------------------------------
# SKILL TAXONOMY
# add(label, words that trigger it in the JOB DESCRIPTION,
#            words that prove it in the RESUME)
# You can add your own skills here any time.
# ------------------------------------------------------------

TAXONOMY = []


def add(label, jd_terms, resume_terms=None):
    TAXONOMY.append((
        label,
        [normalize(x) for x in jd_terms],
        [normalize(x) for x in (resume_terms or jd_terms)],
    ))


# Programming languages
add("Python", ["python"])
add("Java", ["java"])
add("C++", ["c++"])
add("C#", ["c#"])
add("C programming", ["c programming"])
add("JavaScript", ["javascript", "js"])
add("TypeScript", ["typescript"])
add("PHP", ["php"])
add("R programming", ["r programming"])
add("Programming fundamentals",
    ["programming fundamentals", "programming basics",
     "at least one programming language", "programming language",
     "programming languages"],
    ["python", "java", "c++", "c#", "c programming", "javascript",
     "typescript", "php", "programming fundamentals"])

# Web
add("HTML", ["html", "webpage structure", "web page structure"],
    ["html", "html5"])
add("CSS", ["css", "website styling", "web styling"],
    ["css", "css3", "bootstrap", "tailwind", "sass"])
add("Frontend functionality",
    ["frontend functionality", "front end functionality",
     "frontend development", "front end development", "frontend",
     "front end"],
    ["html", "css", "javascript", "react", "angular", "vue",
     "front end", "frontend"])
add("React", ["react", "reactjs", "react js"], ["react", "reactjs", "react js"])
add("Angular", ["angular"])
add("Node.js", ["node js", "nodejs", "node"], ["node js", "nodejs"])
add("Django", ["django"])
add("Flask", ["flask"])
add("REST APIs", ["rest api", "rest apis", "restful api", "api development"],
    ["rest api", "rest apis", "restful", "api"])

# Databases
add("SQL", ["sql"],
    ["sql", "mysql", "postgresql", "sqlite", "sql server", "oracle sql"])
add("MySQL", ["mysql"])
add("PostgreSQL", ["postgresql", "postgres"], ["postgresql", "postgres"])
add("MongoDB", ["mongodb", "nosql"], ["mongodb", "nosql"])
add("Database operations",
    ["database operations", "database management", "databases",
     "database", "dbms", "rdbms"],
    ["sql", "mysql", "postgresql", "sqlite", "mongodb", "firebase",
     "database", "databases", "dbms", "rdbms"])

# CS fundamentals
add("OOPs (classes, objects, inheritance)",
    ["oop", "oops", "object oriented", "object oriented programming",
     "classes objects inheritance", "inheritance", "polymorphism"],
    ["oop", "oops", "object oriented", "object oriented programming",
     "inheritance", "polymorphism", "encapsulation"])
add("Data structures (arrays, linked lists, stacks)",
    ["data structures", "data structure", "dsa", "linked list",
     "linked lists", "arrays strings linked lists stacks", "stacks"],
    ["data structures", "data structure", "dsa", "linked list",
     "linked lists", "stacks", "queues", "binary tree", "hash map"])
add("Algorithms", ["algorithms", "algorithm"], ["algorithms", "algorithm", "dsa"])

# Tools
add("Version control", ["version control"],
    ["git", "github", "gitlab", "bitbucket", "svn", "version control"])
add("Git", ["git"], ["git", "github", "gitlab"])
add("GitHub", ["github"])
add("Docker", ["docker"])
add("Linux", ["linux"])
add("Jira", ["jira"])
add("Agile / Scrum", ["agile", "scrum"], ["agile", "scrum"])

# Data / analytics / AI
add("Excel", ["excel", "ms excel", "advanced excel"],
    ["excel", "ms excel"])
add("Power BI", ["power bi", "powerbi"], ["power bi", "powerbi"])
add("Tableau", ["tableau"])
add("Power Query / DAX", ["power query", "dax"])
add("Pandas", ["pandas"])
add("NumPy", ["numpy"])
add("Matplotlib / Seaborn", ["matplotlib", "seaborn"], ["matplotlib", "seaborn"])
add("Data visualization",
    ["data visualization", "data visualisation", "dashboards", "dashboard"],
    ["data visualization", "data visualisation", "visualization",
     "visualisation", "power bi", "tableau", "matplotlib", "seaborn",
     "dashboard"])
add("Data analysis", ["data analysis", "data analytics", "analyze data",
                      "analyse data"],
    ["data analysis", "data analytics", "analyzing data", "analysing data"])
add("Data cleaning", ["data cleaning", "data cleansing", "data preparation",
                      "data wrangling"],
    ["data cleaning", "data cleansing", "data preparation", "data wrangling",
     "preprocessing"])
add("Statistics", ["statistics", "statistical analysis"],
    ["statistics", "statistical"])
add("Machine learning", ["machine learning", "ml"],
    ["machine learning", "tensorflow", "scikit learn", "sklearn", "pytorch"])
add("Deep learning", ["deep learning"],
    ["deep learning", "neural network", "tensorflow", "pytorch", "keras"])
add("NLP", ["nlp", "natural language processing"],
    ["nlp", "natural language processing"])
add("TensorFlow", ["tensorflow"])
add("PyTorch", ["pytorch"])
add("Scikit-learn", ["scikit learn", "sklearn"], ["scikit learn", "sklearn"])
add("ETL", ["etl"])
add("Spark / Hadoop", ["spark", "pyspark", "hadoop"],
    ["spark", "pyspark", "hadoop"])

# Cloud
add("AWS", ["aws", "amazon web services"], ["aws", "amazon web services"])
add("Azure", ["azure"])
add("Google Cloud", ["gcp", "google cloud"], ["gcp", "google cloud"])

# Soft skills
add("Problem solving / logical thinking",
    ["problem solving", "problem solver", "logical thinking",
     "analytical thinking", "analytical skills"],
    ["problem solving", "problem solver", "logical thinking", "analytical"])
add("Communication", ["communication skills", "communication", "communicate"],
    ["communication", "communicator", "presentation skills"])
add("Teamwork", ["teamwork", "team player", "collaboration", "collaborate"],
    ["teamwork", "team player", "collaboration", "collaborative", "team"])


# ------------------------------------------------------------
# STEP 1: FIND REQUIREMENTS IN THE JOB DESCRIPTION
# ------------------------------------------------------------

LANG = r"(?:python|java(?!script)|c\+\+|c#)"
LANG_GROUP = re.compile(LANG + r"(?:\s*(?:/|,|\bor\b)\s*" + LANG + r")+")


def rule_requirements(job_description):
    jd_pad = padded(job_description)
    reqs = []

    for label, jd_terms, resume_terms in TAXONOMY:
        hit = find_first(jd_pad, jd_terms)
        if hit:
            reqs.append({
                "label": label,
                "pos": hit[0],
                "resume_terms": resume_terms,
            })

    # "Python / Java" means ONE of them is enough
    raw = job_description.lower()
    by_label = {r["label"].lower(): r for r in reqs}

    for m in LANG_GROUP.finditer(raw):
        names = []
        for n in re.findall(LANG, m.group(0)):
            if n not in names:
                names.append(n)
        if len(names) < 2:
            continue

        members = [by_label[n] for n in names if n in by_label]
        if len(members) < 2:
            continue

        merged_terms = []
        for r in members:
            merged_terms += r["resume_terms"]

        pos = min(r["pos"] for r in members)
        reqs = [r for r in reqs if r not in members]
        reqs.append({
            "label": " / ".join(r["label"] for r in members) + " (any one)",
            "pos": pos,
            "resume_terms": merged_terms,
        })

    reqs.sort(key=lambda r: r["pos"])
    return reqs


# ------------------------------------------------------------
# OPTIONAL AI PART (only for requirements NOT in the taxonomy)
# ------------------------------------------------------------

def ask_ai(prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options={"temperature": 0, "num_ctx": 8192},
    )
    return json.loads(response["message"]["content"])


SKIP_WORDS = re.compile(
    r"year|degree|bachelor|master|fresher|graduat|experience|eligib|salary|location"
)


def covered_by_taxonomy(text):
    pad = padded(text)
    for _, jd_terms, _ in TAXONOMY:
        if find_first(pad, jd_terms):
            return True
    return False


def ai_extra_requirements(job_description, known_labels):
    prompt = (
        "Read this job description and list extra SKILLS or KNOWLEDGE "
        "areas the candidate must have.\n\n"
        "Do NOT repeat anything from this list: "
        + json.dumps(known_labels)
        + "\nDo NOT include years of experience, degrees, salary or "
        "job duties. Maximum 6 items, each under 6 words. "
        "If there is nothing extra, return an empty list.\n\n"
        "JOB DESCRIPTION:\n" + job_description + "\n\n"
        'Return JSON only: {"requirements": ["<item>", "<item>"]}'
    )
    data = ask_ai(prompt)
    items = data.get("requirements", [])
    if not isinstance(items, list):
        return []

    out, seen = [], set()
    for item in items:
        if not isinstance(item, str) or not item.strip():
            continue
        key = normalize(item)
        if key in seen or SKIP_WORDS.search(key) or covered_by_taxonomy(key):
            continue
        seen.add(key)
        out.append(item.strip())
    return out[:6]


STOP = {"and", "or", "the", "of", "to", "in", "with", "for", "skills",
        "skill", "knowledge", "ability", "basic", "strong", "good", "using"}


def stems(text):
    return {w[:5] for w in normalize(text).split()
            if w not in STOP and len(w) > 2}


def ai_judge(resume_text, requirement):
    """Returns the evidence quote if the resume really proves it, else None."""
    prompt = (
        "RESUME:\n" + resume_text + "\n\n"
        "REQUIREMENT: " + requirement + "\n\n"
        "Does the resume clearly show this requirement? "
        "If yes, copy ONE short exact phrase from the resume as proof. "
        "If you are not sure, answer missing.\n"
        'Return JSON only: {"status": "matched" or "missing", '
        '"evidence_quote": "<exact phrase or empty>"}'
    )
    data = ask_ai(prompt)
    if str(data.get("status", "")).lower() != "matched":
        return None

    quote = data.get("evidence_quote", "")
    if not isinstance(quote, str):
        return None

    nq = normalize(quote)
    if len(nq.split()) < 2:
        return None
    if (" " + nq + " ") not in padded(resume_text):
        return None                      # quote is not really in the resume
    if not (stems(quote) & stems(requirement)):
        return None                      # quote is not related to requirement
    return quote.strip()


# ------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------

def compare_resume(resume_text, job_description, use_ai=True):
    if not resume_text.strip():
        raise ValueError("Resume text is empty.")
    if not job_description.strip():
        raise ValueError("Job description is empty.")

    resume_pad = padded(resume_text)

    matched, missing, evidence, ai_checked = [], [], {}, []
    ai_error = None

    # 1) Rule-based (exact, never guesses)
    reqs = rule_requirements(job_description)
    for r in reqs:
        hit = find_first(resume_pad, r["resume_terms"])
        if hit:
            matched.append(r["label"])
            evidence[r["label"]] = hit[1]
        else:
            missing.append(r["label"])

    # 2) AI only for extra requirements
    if use_ai and ollama is not None:
        try:
            extras = ai_extra_requirements(
                job_description, [r["label"] for r in reqs]
            )
            for item in extras:
                quote = ai_judge(resume_text, item)
                ai_checked.append(item)
                if quote:
                    matched.append(item)
                    evidence[item] = quote
                else:
                    missing.append(item)
        except Exception as e:
            ai_error = str(e)

    total = len(matched) + len(missing)
    if total == 0:
        raise ValueError(
            "No requirements found in the job description. "
            "Try pasting more of the description."
        )

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percentage": round(len(matched) / total * 100, 2),
        "evidence": evidence,
        "ai_checked": ai_checked,
        "ai_error": ai_error,
     }
