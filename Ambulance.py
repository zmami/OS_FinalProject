from random import randint

from Patient import Patient


class Ambulance:
    ambulance_counter = 1

    def __init__(self):
        self.ambulance_id = f"A{self.ambulance_counter}"
        Ambulance.ambulance_counter += 1
        self.patient = None
        self.patient_counter = 1  # Add counter for each ambulance's patients

    def pick_up_patient(self):
        age = randint(1, 100)
        # Create patient with ambulance-specific ID
        patient = Patient(age)
        patient.patient_id = f"{self.ambulance_id}-{self.patient_counter:03d}"
        self.patient_counter += 1
        self.patient = patient
        print(f"Ambulance {self.ambulance_id} picked up patient {patient.patient_id}")
        return patient
