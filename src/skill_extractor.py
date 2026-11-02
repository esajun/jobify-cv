"""
skill_extractor.py
-------------------
Mengekstrak skill/kata kunci dari teks CV maupun job description.

Prioritas sumber daftar skill:
1. `models/skill_vocab.json` — dihasilkan oleh `scripts/train_model.py` dari
   kolom `skills` di `data/jobs_processed.csv` (data asli, ribuan skill unik).
2. Jika file itu belum ada (belum pernah training), fallback ke daftar manual
   kecil (`FALLBACK_SKILL_KEYWORDS`) supaya aplikasi tetap bisa dipakai.
"""


import json
import os
import re

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
SKILL_VOCAB_PATH = os.path.join(MODEL_DIR, "skill_vocab.json")


FALLBACK_SKILL_KEYWORDS = [
    # ==================================================
    # 1. PROGRAMMING, SOFTWARE DEVELOPMENT & IT
    # ==================================================
    "python", "java", "javascript", "typescript", "c", "c++", "c#",
    "php", "ruby", "go", "golang", "rust", "kotlin", "swift",
    "dart", "r programming", "matlab", "bash", "powershell",
    "html", "css", "sass", "bootstrap", "tailwind css",
    "react", "react.js", "vue", "vue.js", "angular", "next.js",
    "node.js", "express.js", "django", "flask", "fastapi",
    "laravel", "spring boot", ".net", "asp.net",
    "rest api", "graphql", "api development", "microservices",
    "object oriented programming", "functional programming",
    "data structures", "algorithms", "debugging", "unit testing",
    "integration testing", "software testing", "software development",
    "web development", "frontend development", "backend development",
    "full stack development", "mobile app development",
    "android development", "ios development", "game development",
    "software architecture", "system design", "code review",
    "version control", "git", "github", "gitlab", "bitbucket",
    "linux", "windows server", "networking", "computer networking",
    "troubleshooting", "technical support", "it support",
    "cybersecurity", "penetration testing", "ethical hacking",
    "information security", "network security", "cloud security",
    "identity and access management", "incident response",
    "vulnerability assessment", "firewalls", "encryption",
    "devops", "devsecops", "ci/cd", "docker", "kubernetes",
    "jenkins", "terraform", "ansible", "aws", "microsoft azure",
    "google cloud platform", "cloud computing", "server management",
    "system administration", "database administration",
    "agile development", "scrum", "kanban",

    # ==================================================
    # 2. DATA, AI & MACHINE LEARNING
    # ==================================================
    "data analysis", "data analytics", "data science",
    "data engineering", "data visualization", "data cleaning",
    "data preprocessing", "exploratory data analysis",
    "statistical analysis", "descriptive statistics",
    "inferential statistics", "hypothesis testing",
    "probability", "linear regression", "logistic regression",
    "time series analysis", "predictive analytics",
    "business intelligence", "machine learning", "deep learning",
    "artificial intelligence", "natural language processing",
    "computer vision", "generative ai", "large language models",
    "prompt engineering", "retrieval augmented generation",
    "recommendation systems", "neural networks",
    "feature engineering", "feature selection", "model evaluation",
    "model deployment", "mlops", "tensorflow", "pytorch",
    "scikit-learn", "xgboost", "lightgbm", "keras",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn",
    "plotly", "jupyter notebook", "google colab",
    "sql", "mysql", "postgresql", "sqlite", "sql server",
    "oracle database", "mongodb", "redis", "elasticsearch",
    "firebase", "supabase", "data warehousing", "data modeling",
    "etl", "elt", "apache spark", "hadoop", "airflow",
    "kafka", "dbt", "snowflake", "databricks",
    "power bi", "tableau", "looker", "looker studio",
    "microsoft excel", "excel", "google sheets",
    "dashboard development", "reporting", "kpi monitoring",

    # ==================================================
    # 3. UI/UX, GRAPHIC DESIGN & CREATIVE
    # ==================================================
    "graphic design", "ui design", "ux design", "ui/ux design",
    "user interface design", "user experience design",
    "interaction design", "user research", "usability testing",
    "wireframing", "prototyping", "design thinking",
    "design systems", "information architecture",
    "figma", "adobe xd", "sketch", "invision", "framer",
    "web design", "mobile interface design", "responsive design",
    "visual design", "visual communication", "visual branding",
    "branding", "brand identity", "logo design", "layout design",
    "typography", "color theory", "illustration", "digital illustration",
    "digital art", "drawing", "storyboarding", "icon design",
    "infographic design", "poster design", "packaging design",
    "print design", "publication design", "editorial design",
    "social media design", "advertising design", "creative direction",
    "art direction", "adobe photoshop", "adobe illustrator",
    "adobe indesign", "indesign", "adobe after effects",
    "adobe premiere pro", "adobe lightroom", "coreldraw",
    "canva", "blender", "autodesk maya", "cinema 4d",
    "3d modeling", "3d animation", "motion graphics",
    "animation", "video editing", "photo editing",
    "photography", "videography", "color grading",
    "visual storytelling", "creative thinking", "artistic skills",
    "portfolio development",

    # ==================================================
    # 4. DIGITAL MARKETING, CONTENT & COMMUNICATION
    # ==================================================
    "digital marketing", "marketing strategy", "marketing research",
    "market research", "marketing analytics", "brand marketing",
    "content marketing", "social media marketing",
    "influencer marketing", "email marketing", "affiliate marketing",
    "performance marketing", "growth marketing", "product marketing",
    "search engine optimization", "seo", "search engine marketing",
    "sem", "pay per click", "ppc", "google ads", "meta ads",
    "google analytics", "google search console",
    "conversion rate optimization", "cro", "lead generation",
    "marketing automation", "campaign management",
    "advertising campaign", "media planning", "media buying",
    "copywriting", "content writing", "technical writing",
    "creative writing", "blog writing", "article writing",
    "scriptwriting", "editing", "proofreading",
    "content creation", "content strategy", "content planning",
    "social media management", "community management",
    "public relations", "pr", "corporate communication",
    "press release writing", "communication strategy",
    "storytelling", "public speaking", "presentation skills",
    "brand awareness", "customer engagement", "market segmentation",
    "competitor analysis", "consumer behavior", "public speaking",

    # ==================================================
    # 5. BUSINESS, PRODUCT & PROJECT MANAGEMENT
    # ==================================================
    "business analysis", "business development", "business strategy",
    "business planning", "strategic planning", "business operations",
    "business process improvement", "process optimization",
    "requirements gathering", "requirements analysis",
    "stakeholder management", "product management",
    "product development", "product strategy", "product roadmap",
    "product lifecycle management", "product discovery",
    "project management", "project planning", "project coordination",
    "project scheduling", "project budgeting", "risk management",
    "change management", "resource management", "quality management",
    "quality assurance", "quality control", "performance management",
    "operational management", "operations management",
    "workflow management", "documentation", "report writing",
    "business process modeling", "business process mapping",
    "feasibility analysis", "strategic analysis",
    "swot analysis", "gap analysis", "decision making",
    "problem solving", "critical thinking", "analytical thinking",
    "microsoft project", "jira", "trello", "asana", "clickup",
    "notion", "monday.com", "confluence", "slack",

    # ==================================================
    # 6. FINANCE, ACCOUNTING & AUDIT
    # ==================================================
    "accounting", "financial accounting", "management accounting",
    "cost accounting", "financial analysis", "financial modeling",
    "financial reporting", "financial planning",
    "financial forecasting", "financial management",
    "budgeting", "budget management", "cash flow management",
    "bookkeeping", "tax accounting", "tax preparation",
    "tax compliance", "tax reporting", "tax planning",
    "auditing", "internal audit", "external audit",
    "risk assessment", "financial risk management",
    "investment analysis", "investment management",
    "portfolio management", "corporate finance",
    "capital budgeting", "valuation", "reconciliation",
    "accounts payable", "accounts receivable", "payroll accounting",
    "bank reconciliation", "invoicing", "general ledger",
    "financial statements", "ifrs", "psak", "gaap",
    "quickbooks", "accurate accounting", "myob",
    "sap finance", "erp systems", "fraud detection",
    "compliance", "anti money laundering", "aml",

    # ==================================================
    # 7. HUMAN RESOURCES & RECRUITMENT
    # ==================================================
    "human resources", "human resource management", "hr management",
    "talent acquisition", "recruitment", "candidate screening",
    "cv screening", "resume screening", "interviewing",
    "behavioral interviewing", "employee onboarding",
    "employee engagement", "employee relations",
    "employee development", "performance appraisal",
    "performance review", "training and development",
    "learning and development", "workforce planning",
    "succession planning", "talent management",
    "compensation and benefits", "payroll management",
    "job analysis", "job evaluation", "organizational development",
    "organizational behavior", "labor relations",
    "employment law", "hr analytics", "human resource information system",
    "hris", "applicant tracking system", "ats",
    "people analytics", "conflict resolution",
    "employee retention", "workforce management",

    # ==================================================
    # 8. ADMINISTRATION & OFFICE OPERATIONS
    # ==================================================
    "administration", "administrative support",
    "office administration", "office management",
    "data entry", "document management", "records management",
    "filing", "calendar management", "schedule management",
    "meeting coordination", "travel arrangements",
    "correspondence management", "email management",
    "minutes of meeting", "meeting minutes",
    "inventory administration", "database management",
    "microsoft word", "microsoft powerpoint", "microsoft office",
    "google docs", "google slides", "google workspace",
    "typing", "transcription", "secretarial skills",
    "virtual assistance", "executive assistance",
    "attention to detail", "accuracy", "organization skills",

    # ==================================================
    # 9. SALES, CUSTOMER SERVICE & RETAIL
    # ==================================================
    "sales", "sales management", "sales strategy",
    "sales operations", "sales forecasting", "sales reporting",
    "business to business sales", "business to consumer sales",
    "b2b sales", "b2c sales", "inside sales", "field sales",
    "account management", "key account management",
    "client relationship management", "customer relationship management",
    "crm", "salesforce", "hubspot", "lead qualification",
    "negotiation", "persuasion", "closing sales",
    "customer service", "customer support", "technical customer support",
    "customer experience", "customer satisfaction",
    "complaint handling", "conflict management",
    "call center", "help desk", "ticket management",
    "zendesk", "freshdesk", "retail operations",
    "merchandising", "point of sale", "pos systems",
    "cash handling", "product knowledge", "upselling", "cross selling",

    # ==================================================
    # 10. EDUCATION, TRAINING & RESEARCH
    # ==================================================
    "teaching", "instructional design", "curriculum development",
    "lesson planning", "classroom management",
    "educational assessment", "student assessment",
    "educational technology", "e-learning", "online teaching",
    "tutoring", "training delivery", "facilitation",
    "learning management system", "lms",
    "academic writing", "research methodology",
    "qualitative research", "quantitative research",
    "literature review", "survey design", "questionnaire design",
    "interview research", "data collection", "data interpretation",
    "scientific writing", "research reporting",

    # ==================================================
    # 11. HEALTHCARE & LABORATORY
    # ==================================================
    "patient care", "patient assessment", "clinical assessment",
    "clinical documentation", "medical terminology",
    "medical records management", "electronic health records",
    "nursing", "midwifery", "phlebotomy", "first aid",
    "basic life support", "bls", "cpr", "infection control",
    "patient safety", "health education", "public health",
    "health promotion", "medical laboratory", "laboratory testing",
    "sample collection", "microscopy", "quality control laboratory",
    "clinical research", "medical coding", "medical billing",
    "pharmacy", "pharmacology", "occupational health",
    "occupational safety", "kesehatan dan keselamatan kerja",
    "k3", "food safety", "nutrition",

    # ==================================================
    # 12. ENGINEERING, MANUFACTURING & CONSTRUCTION
    # ==================================================
    "mechanical engineering", "electrical engineering",
    "civil engineering", "industrial engineering",
    "chemical engineering", "environmental engineering",
    "mechatronics", "automation engineering",
    "control systems", "plc programming", "robotics",
    "cad", "computer aided design", "autocad", "solidworks",
    "revit", "sketchup", "building information modeling",
    "bim", "technical drawing", "engineering design",
    "structural analysis", "site supervision",
    "construction management", "project estimation",
    "quantity surveying", "cost estimation",
    "procurement engineering", "manufacturing processes",
    "lean manufacturing", "six sigma", "5s",
    "continuous improvement", "preventive maintenance",
    "corrective maintenance", "equipment maintenance",
    "quality inspection", "production planning",
    "production scheduling", "supply chain management",
    "occupational safety", "hazard identification",
    "environmental management", "energy management",

    # ==================================================
    # 13. LOGISTICS, PROCUREMENT & SUPPLY CHAIN
    # ==================================================
    "logistics", "logistics management", "supply chain",
    "supply chain planning", "inventory management",
    "warehouse management", "warehouse operations",
    "distribution management", "fleet management",
    "transportation management", "shipping coordination",
    "freight forwarding", "customs clearance",
    "procurement", "purchasing", "vendor management",
    "supplier relationship management", "sourcing",
    "purchase order management", "demand forecasting",
    "materials planning", "mrp", "order fulfillment",
    "stock control", "stock opname", "warehouse optimization",
    "export import", "import export documentation",

    # ==================================================
    # 14. HOSPITALITY, FOOD & TOURISM
    # ==================================================
    "hospitality", "hotel management", "front office",
    "front desk operations", "housekeeping", "guest relations",
    "reservation management", "event management",
    "event planning", "tourism management", "travel planning",
    "tour guiding", "customer hospitality", "food preparation",
    "food and beverage service", "food service",
    "culinary arts", "menu planning", "food hygiene",
    "food quality assurance", "barista skills",
    "restaurant management", "catering management",

    # ==================================================
    # 15. AGRICULTURE & ENVIRONMENT
    # ==================================================
    "agriculture", "agribusiness", "crop management",
    "soil analysis", "plant pathology", "horticulture",
    "aquaculture", "animal husbandry", "livestock management",
    "pest management", "irrigation management",
    "agricultural research", "sustainable agriculture",
    "environmental monitoring", "environmental impact assessment",
    "waste management", "water quality testing",
    "conservation", "renewable energy", "sustainability",

    # ==================================================
    # 16. GENERAL PROFESSIONAL SKILLS
    # ==================================================
    "communication", "komunikasi", "written communication",
    "verbal communication", "interpersonal communication",
    "interpersonal skills", "teamwork", "team work",
    "collaboration", "leadership", "time management",
    "manajemen waktu", "organization", "organizational skills",
    "adaptability", "flexibility", "initiative",
    "self management", "self motivation", "work ethic",
    "creativity", "creative thinking", "critical thinking",
    "analytical skills", "attention to detail",
    "decision making", "problem solving", "negotiation skills",
    "conflict resolution", "emotional intelligence",
    "multitasking", "prioritization", "planning",
    "presentation skills", "interpersonal relationship",
    "customer focus", "learning agility", "resilience",
    "professional ethics", "integrity", "reliability",

    # ==================================================
    # 17. INDONESIAN TERMS & COMMON VARIATIONS
    # ==================================================
    "desain grafis", "desain komunikasi visual",
    "komunikasi visual", "desain logo", "desain poster",
    "desain kemasan", "desain publikasi", "desain web",
    "desain antarmuka", "pengalaman pengguna",
    "riset pengguna", "pengujian kegunaan",
    "pengolahan data", "analisis data", "visualisasi data",
    "pembelajaran mesin", "kecerdasan buatan",
    "pengembangan perangkat lunak", "pengembangan web",
    "pengembangan aplikasi", "pengujian perangkat lunak",
    "keamanan siber", "komputasi awan", "basis data",
    "manajemen proyek", "analisis bisnis",
    "pengembangan bisnis", "strategi pemasaran",
    "pemasaran digital", "pemasaran media sosial",
    "optimasi mesin pencari", "penulisan konten",
    "pembuatan konten", "manajemen media sosial",
    "layanan pelanggan", "dukungan pelanggan",
    "hubungan pelanggan", "penjualan", "negosiasi",
    "akuntansi", "analisis keuangan", "laporan keuangan",
    "perpajakan", "audit", "penganggaran",
    "sumber daya manusia", "rekrutmen", "seleksi kandidat",
    "pelatihan karyawan", "administrasi perkantoran",
    "entri data", "pengarsipan", "pengelolaan dokumen",
    "pengadaan barang", "manajemen persediaan",
    "manajemen gudang", "rantai pasok",
    "perencanaan produksi", "pemeliharaan mesin",
    "pengawasan proyek", "keselamatan kerja",
    "pengajaran", "pengembangan kurikulum",
    "penelitian kualitatif", "penelitian kuantitatif",
    "perawatan pasien", "pelayanan kesehatan",
    "pelayanan medis", "pengelolaan laboratorium",
    "perhotelan", "layanan makanan", "perencanaan acara",
]


# Kata umum atau potongan kata yang bukan skill mandiri.
INVALID_SKILLS = {
    "skill", "skills", "type", "to detail", "detail",
}

# Penyamaan istilah agar variasi penulisan tidak dihitung berbeda.

SKILL_ALIASES = {
    # Desain
    "photoshop": "adobe photoshop",
    "illustrator": "adobe illustrator",
    "indesign": "adobe indesign",
    "komunikasi visual": "visual communication",
    "desain komunikasi visual": "visual communication",
    "desain grafis": "graphic design",
    "desain logo": "logo design",
    "desain poster": "poster design",
    "desain web": "web design",
    "desain kemasan": "packaging design",
    "desain antarmuka": "user interface design",
    "pengalaman pengguna": "user experience design",

    # Data dan teknologi
    "analisis data": "data analysis",
    "pengolahan data": "data processing",
    "visualisasi data": "data visualization",
    "pembelajaran mesin": "machine learning",
    "kecerdasan buatan": "artificial intelligence",
    "basis data": "database management",
    "pengembangan web": "web development",
    "pengembangan aplikasi": "application development",
    "keamanan siber": "cybersecurity",
    "komputasi awan": "cloud computing",

    # Bisnis dan marketing
    "pemasaran digital": "digital marketing",
    "strategi pemasaran": "marketing strategy",
    "pemasaran media sosial": "social media marketing",
    "manajemen media sosial": "social media management",
    "optimasi mesin pencari": "search engine optimization",
    "penulisan konten": "content writing",
    "pembuatan konten": "content creation",
    "analisis bisnis": "business analysis",
    "pengembangan bisnis": "business development",
    "manajemen proyek": "project management",
    "layanan pelanggan": "customer service",
    "dukungan pelanggan": "customer support",
    "hubungan pelanggan": "customer relationship management",

    # Finance, HR, dan administrasi
    "analisis keuangan": "financial analysis",
    "laporan keuangan": "financial reporting",
    "penganggaran": "budgeting",
    "sumber daya manusia": "human resources",
    "seleksi kandidat": "candidate screening",
    "pelatihan karyawan": "employee training",
    "administrasi perkantoran": "office administration",
    "entri data": "data entry",
    "pengelolaan dokumen": "document management",

    # Operasional dan profesional
    "manajemen waktu": "time management",
    "kerja tim": "teamwork",
    "kerja sama tim": "teamwork",
    "komunikasi": "communication",
    "pemecahan masalah": "problem solving",
    "berpikir kritis": "critical thinking",
    "pengadaan barang": "procurement",
    "manajemen persediaan": "inventory management",
    "manajemen gudang": "warehouse management",
    "rantai pasok": "supply chain management",
    "keselamatan kerja": "occupational safety",
}


_skill_vocab_cache = None


def _load_skill_vocab() -> list:
    global _skill_vocab_cache

    if _skill_vocab_cache is not None:
        return _skill_vocab_cache

    if os.path.exists(SKILL_VOCAB_PATH):
        with open(SKILL_VOCAB_PATH, "r", encoding="utf-8") as f:
            vocab = json.load(f)
    else:
        vocab = FALLBACK_SKILL_KEYWORDS

    # Gabungkan vocabulary hasil training dengan skill umum yang relevan.
    vocab = list(vocab) + FALLBACK_SKILL_KEYWORDS

    # Normalisasi, hapus duplikat, dan buang kata yang tidak valid.
    cleaned = set()
    for skill in vocab:
        skill = str(skill).lower().strip()
        skill = re.sub(r"\s+", " ", skill)

        if not skill or skill in INVALID_SKILLS:
            continue

        cleaned.add(skill)

    _skill_vocab_cache = sorted(cleaned, key=lambda x: (-len(x), x))
    return _skill_vocab_cache


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[-_/]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_key_phrases(text: str) -> list:
    if not text or not text.strip():
        return []

    text_normalized = _normalize_text(text)
    vocab = _load_skill_vocab()
    found = set()

    # Periksa skill terpanjang terlebih dahulu.
    for skill in vocab:
        normalized_skill = _normalize_text(skill)
        pattern = r"(?<!\w)" + re.escape(normalized_skill) + r"(?!\w)"

        if re.search(pattern, text_normalized):
            canonical = SKILL_ALIASES.get(skill, skill)
            found.add(canonical)

    # Jika ada skill yang lebih spesifik, hindari menghitung
    # nama pendeknya sebagai skill terpisah.
    for skill in list(found):
        for other in found:
            if skill != other and skill in SKILL_ALIASES.values():
                continue

            if skill != other and len(other) > len(skill):
                if re.search(
                    r"(?<!\w)" + re.escape(skill) + r"(?!\w)",
                    other,
                ):
                    found.discard(skill)
                    break

    return sorted(found)


def skill_vocab_size() -> int:
    return len(_load_skill_vocab())


def using_trained_vocab() -> bool:
    return os.path.exists(SKILL_VOCAB_PATH)
