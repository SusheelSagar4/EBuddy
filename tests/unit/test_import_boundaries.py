import os
import ast
import pytest

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))

def get_python_files(directory):
    py_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files

def extract_imports(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def test_litellm_isolation():
    """Verify that ONLY app/llm/client.py imports litellm."""
    all_files = get_python_files(APP_DIR)
    allowed_file = os.path.normpath(os.path.join(APP_DIR, "llm", "client.py"))
    
    violators = []
    for f in all_files:
        norm = os.path.normpath(f)
        if norm == allowed_file:
            continue
        imports = extract_imports(f)
        if any(imp == "litellm" or imp.startswith("litellm.") for imp in imports):
            violators.append(f)
            
    assert not violators, f"Unauthorized litellm imports found in: {violators}. litellm may ONLY be imported in app/llm/client.py"

def test_engine_import_boundaries():
    """Verify that app/engine/ never imports app/llm/ or app/api/."""
    engine_dir = os.path.join(APP_DIR, "engine")
    if not os.path.exists(engine_dir):
        pytest.skip("engine directory not found")
        
    engine_files = get_python_files(engine_dir)
    violators = []
    for f in engine_files:
        imports = extract_imports(f)
        for imp in imports:
            if imp.startswith("app.llm") or imp.startswith("app.api") or imp == "litellm":
                violators.append((f, imp))
                
    assert not violators, f"Engine modules violated clean boundaries by importing: {violators}"

def test_kb_import_boundaries():
    """Verify that app/kb/ never imports app/llm/ or app/api/."""
    kb_dir = os.path.join(APP_DIR, "kb")
    if not os.path.exists(kb_dir):
        pytest.skip("kb directory not found")
        
    kb_files = get_python_files(kb_dir)
    violators = []
    for f in kb_files:
        imports = extract_imports(f)
        for imp in imports:
            if imp.startswith("app.llm") or imp.startswith("app.api") or imp == "litellm":
                violators.append((f, imp))
                
    assert not violators, f"KB repositories violated clean boundaries by importing: {violators}"

def test_contracts_isolation():
    """Verify that app/contracts/ is pure data models and never imports engine, kb, llm, services, or api."""
    contracts_dir = os.path.join(APP_DIR, "contracts")
    if not os.path.exists(contracts_dir):
        pytest.skip("contracts directory not found")
        
    contract_files = get_python_files(contracts_dir)
    forbidden_prefixes = ["app.engine", "app.kb", "app.llm", "app.services", "app.api", "litellm"]
    violators = []
    for f in contract_files:
        imports = extract_imports(f)
        for imp in imports:
            if any(imp.startswith(prefix) for prefix in forbidden_prefixes):
                violators.append((f, imp))
                
    assert not violators, f"Contracts must be pure data definitions without business logic: {violators}"

def test_agents_import_boundaries():
    """Verify that app/agents/ never imports litellm directly or app/api/."""
    agents_dir = os.path.join(APP_DIR, "agents")
    if not os.path.exists(agents_dir):
        pytest.skip("agents directory not found")
        
    agents_files = get_python_files(agents_dir)
    violators = []
    for f in agents_files:
        imports = extract_imports(f)
        for imp in imports:
            if imp == "litellm" or imp.startswith("litellm.") or imp.startswith("app.api"):
                violators.append((f, imp))
                
    assert not violators, f"Agent modules violated clean boundaries by importing: {violators}"

