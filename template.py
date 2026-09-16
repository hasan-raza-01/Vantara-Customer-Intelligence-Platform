from pathlib import Path 

obj_paths = [
    "data/raw/",
    "data/interim/",
    "data/processed/", 
    "notebooks/01_eda.ipynb", 
    "notebooks/02_feature_engineering.ipynb", 
    "notebooks/03_model_experiments.ipynb", 
    "src/__init__.py",
    "src/data/__init__.py", 
    "src/features/__init__.py", 
    "src/models/__init__.py", 
    "src/segmentation/__init__.py", 
    "src/explainability/__init__.py", 
    "src/utils/__init__.py",  
    "api/main.py", 
    "api/routers/", 
    "api/schemas/", 
    "frontend/dashboard.py", 
    "models_artifacts/", 
    "config/config.yaml", 
    "tests/test_features.py", 
    "tests/test_api.py", 
    "docs/architecture_diagram.png", 
    "docs/er_diagram.png", 
    "docs/final_report.pdf", 
    "docker-compose.yml", 
    "Dockerfile", 
    "requirements.txt", 
    "README.md"
]

for p in obj_paths: 
    p = Path(p) 
    if p.suffix or p.as_posix()=="Dockerfile": 
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()
    else:
        p.mkdir(parents=True, exist_ok=True)
    