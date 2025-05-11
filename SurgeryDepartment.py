from queue import PriorityQueue
from random import choice, uniform, random
from threading import Lock
from time import sleep

from Doctor import Doctor
from HospitalStatistics import HospitalStatistics
from Nurse import Nurse
from Patient import Patient
from Specialty import Specialty


class SurgeryDepartment:
    def __init__(self, num_surgeons=10, num_nurses=15):
        self.surgeons = [Doctor(f"SUR{i + 1}", Specialty.SURGERY) for i in range(num_surgeons)]
        self.nurses = [Nurse(f"SN{i + 1}") for i in range(num_nurses)]

        # Assign nurses to surgeons (some surgeons get 2 nurses)
        for i, surgeon in enumerate(self.surgeons):
            nurse1 = self.nurses[i]
            nurse2 = self.nurses[i + len(self.surgeons)] if i < len(self.nurses) - len(self.surgeons) else None

            surgeon.assigned_nurse = nurse1
            nurse1.assigned_doctor = surgeon
            if nurse2:
                nurse2.assigned_doctor = surgeon

        self.surgery_queue = PriorityQueue()
        self.surgery_lock = Lock()  # Add lock

    def schedule_surgery(self, patient: Patient, requesting_doctor: Doctor):
        """Schedule a surgery for a patient"""
        print(f"Scheduling surgery for patient {patient.patient_id}")
        # Add to queue with negative severity for priority
        self.surgery_queue.put((-patient.severity, patient, requesting_doctor))

    def perform_surgery(self, patient: Patient, hospital_stats: HospitalStatistics):
        with self.surgery_lock:
            available_surgeons = [s for s in self.surgeons if not s.is_busy]
            if not available_surgeons:
                print("No surgeons available! Surgery delayed...")
                return False

            surgeon = choice(available_surgeons)
            surgeon.is_busy = True

        try:
            print(f"Surgeon {surgeon.doctor_id} performing surgery on patient {patient.patient_id}")
            sleep(uniform(1.0, 2.0))  # Reduced from 10-15 seconds to 1-2 seconds

            # Increase surgery mortality based on severity
            death_chance = 0.1  # Base 10% chance
            if patient.severity >= 8:
                death_chance = 0.3  # 30% for severe cases
            if patient.severity >= 9:
                death_chance = 0.5  # 50% for critical cases

            success = random() > death_chance
            if success:
                print(f"Surgery successful for patient {patient.patient_id}")
                surgeon.assigned_nurse.post_surgery_check(patient)
                hospital_stats.add_surgery(True)
            else:
                print(f"Patient {patient.patient_id} did not survive surgery")
                hospital_stats.add_surgery(False)

            return success
        finally:
            surgeon.is_busy = False
