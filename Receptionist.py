from time import sleep

from Patient import Patient


class Receptionist:
    def __init__(self, receptionist_id):
        self.receptionist_id = f"R{receptionist_id}"
        self.patient_counter = 1
        self.hospital = None  # Add reference to hospital

    def register_patient(self, age: int):
        print(f"Receptionist {self.receptionist_id} registering patient...")
        sleep(0.5)
        patient = Patient(age)
        patient.patient_id = f"{self.receptionist_id}-{self.patient_counter:04d}"
        self.patient_counter += 1

        # Update statistics
        if self.hospital and self.hospital.stats:
            with self.hospital.stats_lock:
                self.hospital.stats.add_receptionist_patient(self.receptionist_id)

        return patient
