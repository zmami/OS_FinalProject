from random import random, choice, randint
from time import time


class Patient:
    patient_counter = 1
    severity_levels = {
        "Common Cold": (1, 3),
        "Influenza": (2, 5),
        "Hypertension": (3, 7),
        "Diabetes": (4, 8),
        "Asthma": (3, 7),
        "Migraine": (2, 6),
        "Arthritis": (3, 6),
        "Pneumonia": (5, 9),
        "Gastritis": (2, 5),
        "Bronchitis": (3, 6),
        "Sepsis": (8, 10),
        "Acute Myocardial Infarction": (8, 10),
        "Cerebral Hemorrhage": (9, 10),
        "Multiple Organ Failure": (9, 10),
        "Severe Trauma": (8, 10),
        "Heart Failure": (7, 9),
        "Cardiac Arrhythmia": (6, 8),
        "Epilepsy": (5, 8),
        "Multiple Sclerosis": (6, 9),
        "Food Poisoning": (3, 6),
        "Spinal Disc Herniation": (5, 8),
        "Bone Fracture": (4, 7),
    }

    def __init__(self, age: int):
        self.patient_id = None  # Will be set by receptionist
        self.age = age
        self.disease = None
        self.severity = None
        self.arrival_time = time()

    @classmethod
    def create_emergency(cls, age: int, source: str):
        """Create patient for ambulance or MCI without going through reception"""
        patient = cls(age)
        patient.patient_id = f"{source}-{int(time())}"  # Use timestamp for emergency cases
        return patient

    def __lt__(self, other):
        """Implement less than comparison for priority queue"""
        if not isinstance(other, Patient):
            return NotImplemented
        # Compare by severity first, then by arrival time
        if self.severity == other.severity:
            return self.arrival_time < other.arrival_time
        return self.severity < other.severity

    def assign_random_disease(self):
        diseases = list(self.severity_levels.keys())
        # Increase probability of severe conditions
        severe_diseases = ["Sepsis", "Acute Myocardial Infarction", "Cerebral Hemorrhage",
                           "Multiple Organ Failure", "Severe Trauma"]
        if random() < 0.4:  # 40% chance of severe disease
            self.disease = choice(severe_diseases)
        else:
            self.disease = choice(diseases)

        min_severity, max_severity = self.severity_levels[self.disease]
        # Bias towards higher severity within the range
        self.severity = randint(min_severity, max_severity)
        if random() < 0.3:  # 30% chance of maximum severity
            self.severity = max_severity
