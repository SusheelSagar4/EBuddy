import os
import yaml
import importlib.util
from typing import Dict, Any, List, Optional
from app.contracts.persona import PersonaSpec
from app.personas.policy import PersonaPolicy

class PersonaPackage:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.spec: Optional[PersonaSpec] = None
        self.requirements: List[Dict[str, Any]] = []
        self.mastery: Dict[str, Any] = {}
        self.milestones: List[Dict[str, Any]] = []
        self.diagnostic: Dict[str, Any] = {}
        self.policy: PersonaPolicy = None
        self._load()

    def _load(self):
        # 1. persona.yaml
        pyaml = os.path.join(self.folder_path, "persona.yaml")
        if os.path.exists(pyaml):
            with open(pyaml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self.spec = PersonaSpec(**data)

        # 2. requirements.yaml
        ryaml = os.path.join(self.folder_path, "requirements.yaml")
        if os.path.exists(ryaml):
            with open(ryaml, "r", encoding="utf-8") as f:
                self.requirements = yaml.safe_load(f) or []

        # 3. mastery.yaml
        myaml = os.path.join(self.folder_path, "mastery.yaml")
        if os.path.exists(myaml):
            with open(myaml, "r", encoding="utf-8") as f:
                self.mastery = yaml.safe_load(f) or {}

        # 4. milestones.yaml
        milyaml = os.path.join(self.folder_path, "milestones.yaml")
        if os.path.exists(milyaml):
            with open(milyaml, "r", encoding="utf-8") as f:
                self.milestones = yaml.safe_load(f) or []

        # 5. diagnostic.yaml
        dyaml = os.path.join(self.folder_path, "diagnostic.yaml")
        if os.path.exists(dyaml):
            with open(dyaml, "r", encoding="utf-8") as f:
                self.diagnostic = yaml.safe_load(f) or {}

        # 6. policy.py (optional custom hook)
        pol_file = os.path.join(self.folder_path, "policy.py")
        if os.path.exists(pol_file):
            spec_module = importlib.util.spec_from_file_location("custom_policy", pol_file)
            mod = importlib.util.module_from_spec(spec_module)
            spec_module.loader.exec_module(mod)
            if hasattr(mod, "CustomPersonaPolicy"):
                self.policy = mod.CustomPersonaPolicy(self.spec.model_dump() if self.spec else {})
            else:
                self.policy = PersonaPolicy(self.spec.model_dump() if self.spec else {})
        else:
            self.policy = PersonaPolicy(self.spec.model_dump() if self.spec else {})

class PersonaRegistry:
    def __init__(self, base_dir: str = "app/personas"):
        self.base_dir = base_dir
        self._personas: Dict[str, PersonaPackage] = {}
        self.discover()

    def discover(self):
        self._personas.clear()
        if not os.path.exists(self.base_dir):
            return

        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "persona.yaml")):
                try:
                    pkg = PersonaPackage(item_path)
                    if pkg.spec:
                        self._personas[pkg.spec.persona_id] = pkg
                except Exception as e:
                    print(f"Error loading persona plugin {item}: {e}")

    def get(self, persona_id: str) -> Optional[PersonaPackage]:
        return self._personas.get(persona_id)

    def list_all(self) -> List[PersonaPackage]:
        return list(self._personas.values())

# Global singleton registry
persona_registry = PersonaRegistry()

