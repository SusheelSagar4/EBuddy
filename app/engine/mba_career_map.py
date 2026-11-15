import os
from typing import List, Dict, Optional, Any
from app.contracts.core_to_mba import CareerPath
from app.kb.core_to_mba_repo import core_to_mba_repo

class MBACareerMapEngine:
    """
    Core-to-Management Career Map Engine (§1.2 & §7.2).
    Maps undergraduate engineering branches (EE, MM) to verified management career pathways.
    
    Non-negotiable rule (§4):
    Zero salary figures, compensation promises, or placement claims unless directly sourced
    from verified institutional rows. All career paths are presented strictly as informational
    guidance curated by faculty reviewers.
    """
    def __init__(self, repo=None):
        self.repo = repo or core_to_mba_repo

    def _normalize_branch(self, branch: str) -> str:
        b = branch.upper().strip()
        if "EE" in b:
            return "EE"
        if "MM" in b or "META" in b:
            return "MM"
        return b

    def get_career_paths(self, branch: str, include_general: bool = True) -> List[CareerPath]:
        """
        Retrieves curated and reviewed career paths for the given branch.
        """
        norm_branch = self._normalize_branch(branch)
        paths: List[CareerPath] = []
        for path in self.repo.career_paths.values():
            # Only include reviewed paths
            if not path.reviewed:
                continue
            path_b = path.branch.upper().strip()
            if path_b == norm_branch:
                paths.append(path)
            elif include_general and path_b in ["ANY", "ALL"]:
                paths.append(path)
        
        # Sort branch-specific paths first, then general
        paths.sort(key=lambda p: (0 if p.branch.upper() == norm_branch else 1, p.id))
        return paths

    def get_career_path(self, path_id: str) -> Optional[CareerPath]:
        """
        Retrieves a single career path by ID, verifying reviewed status.
        """
        path = self.repo.career_paths.get(path_id)
        if path and path.reviewed:
            return path
        return None

    def search_career_paths(self, query: str, branch: Optional[str] = None) -> List[CareerPath]:
        """
        Fuzzy/substring search across name, description, typical_roles, and sectors.
        """
        q = query.lower().strip()
        norm_b = self._normalize_branch(branch) if branch else None
        results: List[CareerPath] = []

        for path in self.repo.career_paths.values():
            if not path.reviewed:
                continue
            if norm_b and path.branch.upper() != norm_b and path.branch.upper() not in ["ANY", "ALL"]:
                continue
            
            searchable = f"{path.name} {path.description} {path.typical_roles} {path.skills_valued} {path.sectors}".lower()
            if q in searchable:
                results.append(path)

        return results

    def get_engineering_advantage(self, branch: str) -> Dict[str, Any]:
        """
        Returns structured engineering advantage analysis for the student's branch.
        """
        norm_branch = self._normalize_branch(branch)
        if norm_branch == "EE":
            return {
                "branch": "Electrical Engineering",
                "core_strengths": [
                    "Complex systems modeling and abstract block-diagram intuition",
                    "Advanced mathematical and statistical rigor (Signals, Controls, Probability)",
                    "Direct alignment with clean-tech, renewable energy, and semiconductor industries"
                ],
                "management_translation": (
                    "EE graduates understand both the physics of energy/silicon and the economics of capital deployment. "
                    "In techno-commercial roles like hardware product management or energy grid operations, they bridge "
                    "the gap between R&D engineers and executive leadership."
                ),
                "typical_growth_areas": [
                    "Verbal communication and synthesis of open-ended business cases",
                    "Synthesizing qualitative arguments without single closed-form numerical answers"
                ]
            }
        elif norm_branch == "MM":
            return {
                "branch": "Metallurgical and Materials Engineering",
                "core_strengths": [
                    "End-to-end understanding of primary extraction, supply chains, and manufacturing plants",
                    "Thermodynamics, process optimization, and materials yield economics",
                    "Strategic importance in global mineral supply chains, EV battery raw materials, and green steel"
                ],
                "management_translation": (
                    "MM graduates possess deep intuition for manufacturing shop-floors, raw material bottlenecks, and vendor quality. "
                    "In operations, procurement, and industrial consulting, they can immediately audit factory operations "
                    "and optimize multi-crore procurement budgets."
                ),
                "typical_growth_areas": [
                    "Speed-oriented quantitative aptitude (data interpretation under tight time constraints)",
                    "Reading speed and dense comprehension across abstract humanities and social science texts"
                ]
            }
        else:
            return {
                "branch": branch,
                "core_strengths": [
                    "Analytical problem-solving and structured algorithmic thinking",
                    "Data interpretation and quantitative comfort"
                ],
                "management_translation": "Engineers bring rigor and quantitative discipline to unstructured business problems.",
                "typical_growth_areas": ["Verbal ability and qualitative essay articulation"]
            }

# Global Singleton
mba_career_map_engine = MBACareerMapEngine()
