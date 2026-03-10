"""Constants: job role mappings, skill categories, and other reference data."""

from __future__ import annotations

# Proficiency levels for technical skills
TECHNICAL_PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]

# Proficiency levels for languages
LANGUAGE_PROFICIENCY_LEVELS = ["Native", "Fluent", "Intermediate", "Basic"]

# Employment types
EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Freelance"]

# Work mode options
WORK_MODES = ["Remote", "Hybrid", "On-site"]

# ─── Job Role Knowledge Base ────────────────────────────────────────────────
# Maps job role -> required/preferred skills and keywords
JOB_ROLE_SKILLS: dict[str, dict] = {
    "Software Engineer": {
        "skills": ["python", "java", "javascript", "typescript", "c++", "go", "rust",
                   "algorithms", "data structures", "git", "sql", "api", "rest",
                   "oop", "testing", "agile", "scrum"],
        "experience_keywords": ["developed", "built", "implemented", "engineered",
                                "designed", "architected", "optimized"],
        "industries": ["Technology", "Finance", "Healthcare", "E-commerce"],
    },
    "Senior Software Engineer": {
        "skills": ["python", "java", "javascript", "typescript", "microservices",
                   "system design", "architecture", "ci/cd", "docker", "kubernetes",
                   "aws", "azure", "gcp", "leadership", "mentoring"],
        "experience_keywords": ["led", "architected", "mentored", "scaled", "designed"],
        "industries": ["Technology", "Finance", "Healthcare"],
    },
    "Frontend Developer": {
        "skills": ["javascript", "typescript", "react", "vue", "angular", "html",
                   "css", "tailwind", "webpack", "jest", "figma", "responsive design"],
        "experience_keywords": ["built", "designed", "created", "implemented", "developed"],
        "industries": ["Technology", "Media", "E-commerce", "Marketing"],
    },
    "Backend Developer": {
        "skills": ["python", "java", "node.js", "go", "rust", "sql", "postgresql",
                   "mongodb", "redis", "rest api", "graphql", "microservices",
                   "docker", "kubernetes", "aws"],
        "experience_keywords": ["developed", "built", "optimized", "designed", "scaled"],
        "industries": ["Technology", "Finance", "Healthcare", "Logistics"],
    },
    "Full Stack Developer": {
        "skills": ["javascript", "typescript", "react", "node.js", "python",
                   "sql", "mongodb", "docker", "git", "rest api", "html", "css"],
        "experience_keywords": ["built", "developed", "designed", "implemented"],
        "industries": ["Technology", "Startups", "E-commerce"],
    },
    "DevOps Engineer": {
        "skills": ["docker", "kubernetes", "aws", "azure", "gcp", "terraform",
                   "ansible", "ci/cd", "jenkins", "github actions", "linux",
                   "bash", "python", "monitoring", "prometheus", "grafana"],
        "experience_keywords": ["automated", "deployed", "managed", "configured",
                                "maintained", "optimized"],
        "industries": ["Technology", "Finance", "Healthcare"],
    },
    "Cloud Engineer": {
        "skills": ["aws", "azure", "gcp", "terraform", "kubernetes", "docker",
                   "networking", "security", "iam", "serverless", "lambda"],
        "experience_keywords": ["migrated", "deployed", "managed", "architected"],
        "industries": ["Technology", "Finance", "Healthcare", "Government"],
    },
    "Data Scientist": {
        "skills": ["python", "r", "machine learning", "deep learning", "tensorflow",
                   "pytorch", "scikit-learn", "pandas", "numpy", "sql", "statistics",
                   "data analysis", "visualization", "jupyter"],
        "experience_keywords": ["analyzed", "modeled", "predicted", "built", "developed"],
        "industries": ["Technology", "Finance", "Healthcare", "Research"],
    },
    "Data Engineer": {
        "skills": ["python", "sql", "spark", "hadoop", "airflow", "kafka",
                   "aws", "gcp", "azure", "etl", "data pipelines", "dbt",
                   "postgresql", "bigquery", "snowflake"],
        "experience_keywords": ["built", "developed", "designed", "optimized", "managed"],
        "industries": ["Technology", "Finance", "Healthcare", "Retail"],
    },
    "Machine Learning Engineer": {
        "skills": ["python", "tensorflow", "pytorch", "scikit-learn", "mlops",
                   "docker", "kubernetes", "aws sagemaker", "feature engineering",
                   "model deployment", "statistics", "mathematics"],
        "experience_keywords": ["developed", "deployed", "trained", "optimized", "built"],
        "industries": ["Technology", "Healthcare", "Finance", "Research"],
    },
    "Product Manager": {
        "skills": ["product strategy", "roadmap", "user research", "analytics",
                   "agile", "scrum", "stakeholder management", "sql", "jira",
                   "communication", "leadership"],
        "experience_keywords": ["managed", "led", "launched", "drove", "defined"],
        "industries": ["Technology", "Finance", "Healthcare", "E-commerce"],
    },
    "UX/UI Designer": {
        "skills": ["figma", "sketch", "adobe xd", "user research", "wireframing",
                   "prototyping", "usability testing", "css", "html",
                   "design systems", "accessibility"],
        "experience_keywords": ["designed", "created", "improved", "researched"],
        "industries": ["Technology", "Media", "E-commerce", "Healthcare"],
    },
    "Cybersecurity Analyst": {
        "skills": ["network security", "siem", "penetration testing", "vulnerability assessment",
                   "linux", "python", "firewalls", "ids/ips", "soc", "incident response",
                   "compliance", "splunk", "wireshark"],
        "experience_keywords": ["monitored", "analyzed", "secured", "investigated", "mitigated"],
        "industries": ["Technology", "Finance", "Government", "Healthcare"],
    },
    "Project Manager": {
        "skills": ["project management", "pmp", "agile", "scrum", "risk management",
                   "budgeting", "stakeholder management", "ms project", "jira",
                   "communication", "leadership"],
        "experience_keywords": ["managed", "led", "delivered", "coordinated", "planned"],
        "industries": ["Technology", "Construction", "Finance", "Healthcare"],
    },
    "Business Analyst": {
        "skills": ["requirements gathering", "sql", "data analysis", "process mapping",
                   "stakeholder management", "excel", "tableau", "power bi",
                   "agile", "documentation"],
        "experience_keywords": ["analyzed", "documented", "improved", "identified", "defined"],
        "industries": ["Technology", "Finance", "Healthcare", "Consulting"],
    },
    "Data Analyst": {
        "skills": ["sql", "python", "excel", "tableau", "power bi", "statistics",
                   "data visualization", "r", "pandas", "reporting"],
        "experience_keywords": ["analyzed", "reported", "visualized", "identified", "developed"],
        "industries": ["Technology", "Finance", "Healthcare", "Retail", "Marketing"],
    },
    "Mobile Developer": {
        "skills": ["swift", "kotlin", "react native", "flutter", "ios", "android",
                   "xcode", "android studio", "firebase", "rest api"],
        "experience_keywords": ["built", "developed", "published", "implemented"],
        "industries": ["Technology", "Healthcare", "Finance", "E-commerce"],
    },
    "Site Reliability Engineer": {
        "skills": ["linux", "python", "go", "kubernetes", "docker", "aws",
                   "monitoring", "prometheus", "grafana", "incident management",
                   "sre", "slo", "sla", "chaos engineering"],
        "experience_keywords": ["maintained", "improved", "automated", "monitored"],
        "industries": ["Technology", "Finance"],
    },
    "Solutions Architect": {
        "skills": ["aws", "azure", "gcp", "system design", "microservices",
                   "cloud architecture", "networking", "security", "terraform",
                   "docker", "kubernetes", "enterprise architecture"],
        "experience_keywords": ["designed", "architected", "led", "proposed", "implemented"],
        "industries": ["Technology", "Finance", "Healthcare", "Government"],
    },
    "QA Engineer": {
        "skills": ["testing", "selenium", "pytest", "junit", "api testing",
                   "test automation", "performance testing", "ci/cd", "jira",
                   "agile", "bug tracking"],
        "experience_keywords": ["tested", "automated", "identified", "verified", "improved"],
        "industries": ["Technology", "Finance", "Healthcare"],
    },
}

# Industry suggestions based on skill sets
INDUSTRY_SKILL_MAP: dict[str, list] = {
    "Technology": ["python", "java", "javascript", "aws", "docker", "kubernetes",
                   "machine learning", "sql", "git", "api"],
    "Finance": ["sql", "python", "excel", "risk management", "compliance",
                "bloomberg", "quantitative analysis", "statistics"],
    "Healthcare": ["python", "healthcare", "hl7", "fhir", "data analysis",
                   "sql", "compliance", "research"],
    "E-commerce": ["python", "javascript", "react", "aws", "sql", "analytics",
                   "marketing", "seo"],
    "Consulting": ["communication", "analysis", "project management", "excel",
                   "powerpoint", "stakeholder management"],
    "Research": ["statistics", "python", "r", "machine learning", "publications",
                 "data analysis", "matlab"],
    "Marketing": ["analytics", "seo", "content", "social media", "excel",
                  "google analytics", "hubspot"],
    "Government": ["security clearance", "compliance", "documentation",
                   "project management", "policy"],
}

# Skill gap recommendations per role
SKILL_GAPS: dict[str, list] = {
    "Software Engineer": [
        "System design patterns",
        "Cloud fundamentals (AWS/GCP/Azure)",
        "CI/CD pipelines",
    ],
    "Senior Software Engineer": [
        "System design at scale",
        "Technical leadership skills",
        "Advanced distributed systems",
    ],
    "DevOps Engineer": [
        "Terraform for Infrastructure as Code",
        "Advanced Kubernetes (Helm, Operators)",
        "SRE practices and SLO/SLA management",
    ],
    "Data Scientist": [
        "MLOps and model deployment",
        "Advanced statistics",
        "Big data processing (Spark)",
    ],
    "Machine Learning Engineer": [
        "MLOps best practices",
        "Distributed training",
        "Model monitoring and drift detection",
    ],
    "Cloud Engineer": [
        "Multi-cloud architecture",
        "Cloud security best practices",
        "FinOps / cost optimization",
    ],
    "Product Manager": [
        "Data-driven product decisions",
        "OKR framework",
        "Go-to-market strategy",
    ],
    "Frontend Developer": [
        "Web performance optimization",
        "Accessibility (WCAG 2.1)",
        "Advanced state management",
    ],
    "Backend Developer": [
        "Distributed systems design",
        "Event-driven architecture",
        "Database performance tuning",
    ],
    "Cybersecurity Analyst": [
        "Cloud security (AWS/Azure)",
        "Threat hunting",
        "Security automation scripting",
    ],
}
