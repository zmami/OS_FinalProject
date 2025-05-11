from enum import Enum


class Specialty(Enum):
    CARDIOLOGY = "Cardiology"
    NEUROLOGY = "Neurology"
    PEDIATRICS = "Pediatrics"
    ORTHOPEDICS = "Orthopedics"
    GENERAL = "General Medicine"
    SURGERY = "Surgery"
    DIAGNOSTICS = "Diagnostics"

    @classmethod
    def get_specialty_for_disease(cls, disease: str) -> 'Specialty':
        specialty_mapping = {
            "Hypertension": cls.CARDIOLOGY,
            "Acute Myocardial Infarction": cls.CARDIOLOGY,
            "Heart Failure": cls.CARDIOLOGY,
            "Cardiac Arrhythmia": cls.CARDIOLOGY,
            "Cerebral Hemorrhage": cls.NEUROLOGY,
            "Migraine": cls.NEUROLOGY,
            "Epilepsy": cls.NEUROLOGY,
            "Multiple Sclerosis": cls.NEUROLOGY,
            "Multiple Organ Failure": cls.GENERAL,
            "Common Cold": cls.GENERAL,
            "Influenza": cls.GENERAL,
            "Pneumonia": cls.GENERAL,
            "Bronchitis": cls.GENERAL,
            "Sepsis": cls.GENERAL,
            "Gastritis": cls.GENERAL,
            "Diabetes": cls.GENERAL,
            "Food Poisoning": cls.GENERAL,
            "Arthritis": cls.ORTHOPEDICS,
            "Severe Trauma": cls.ORTHOPEDICS,
            "Spinal Disc Herniation": cls.ORTHOPEDICS,
            "Bone Fracture": cls.ORTHOPEDICS,
        }
        return specialty_mapping.get(disease, cls.GENERAL)
