from typing import List, Set, Tuple
from dataclasses import dataclass, field

@dataclass
class Student:
    """Data model representing a student."""
    name: str
    course: str
    time_slots: Set[str] = field(default_factory=set)
    objectives: Set[str] = field(default_factory=set)

class MatchingEngine:
    """
    A backend engine to calculate compatibility scores between students for study groups.
    """
    def __init__(self, time_weight: float = 0.7, objective_weight: float = 0.3):
        """
        Initializes the engine with configurable weights.
        Schedule overlap is weighted heavily by default because groups must be able to meet.
        """
        self.time_weight = time_weight
        self.objective_weight = objective_weight

    def calculate_overlap_ratio(self, set_a: Set[str], set_b: Set[str]) -> float:
        """
        Calculates how much two sets overlap. 
        Uses the size of the smaller set as the denominator so users with limited availability 
        aren't unfairly penalized if they match completely with someone who has wide availability.
        """
        if not set_a or not set_b:
            return 0.0
        overlap_count = len(set_a.intersection(set_b))
        smaller_set_len = min(len(set_a), len(set_b))
        return overlap_count / smaller_set_len if smaller_set_len > 0 else 0.0

    def get_compatibility_score(self, student_a: Student, student_b: Student) -> float:
        """
        Calculates the total compatibility score between two students.
        Returns 0.0 immediately if courses do not match (hard filter).
        """
        if student_a.course != student_b.course:
            return 0.0

        time_score = self.calculate_overlap_ratio(student_a.time_slots, student_b.time_slots)
        
        # If there is absolutely no time overlap, they cannot meet. Score is 0.
        if time_score == 0.0:
            return 0.0

        obj_score = self.calculate_overlap_ratio(student_a.objectives, student_b.objectives)

        total_score = (time_score * self.time_weight) + (obj_score * self.objective_weight)
        return round(total_score, 2)

    def find_best_matches(self, target_student: Student, candidate_pool: List[Student], top_n: int = 3) -> List[Tuple[Student, float]]:
        """
        Finds the top N best matches for a given student from a pool of candidates.
        """
        scored_candidates = []
        for candidate in candidate_pool:
            if candidate.name == target_student.name:
                continue 

            score = self.get_compatibility_score(target_student, candidate)
            if score > 0: 
                scored_candidates.append((candidate, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_n]

