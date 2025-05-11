from queue import Queue, Empty
from random import uniform
from threading import Thread
from time import sleep

from Patient import Patient


class Nurse:
    def __init__(self, nurse_id):
        self.nurse_id = nurse_id
        self.assigned_doctor = None
        self.assessment_queue = Queue()
        self.is_active = True
        self.thread = None

    def start_shift(self):
        """Start nurse's work loop"""
        self.thread = Thread(target=self._work_loop, name=f"Nurse-{self.nurse_id}")
        self.thread.daemon = True
        self.thread.start()

    def _work_loop(self):
        """Continuous loop to assess patients"""
        while self.is_active:
            try:
                patient = self.assessment_queue.get(timeout=1)
                self.assess_patient(patient)
                self.assessment_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"Error in nurse {self.nurse_id} work loop: {e}")

    def stop_shift(self):
        """Stop the nurse's work loop"""
        self.is_active = False
        if self.thread:
            self.thread.join(timeout=2)

    def assess_patient(self, patient: Patient):
        print(f"Nurse {self.nurse_id} assessing patient {patient.patient_id}...")
        sleep(uniform(0.5, 1.0))  # Reduced from 5-10 seconds to 0.5-1 second
        patient.assign_random_disease()
        print(
            f"Patient {patient.patient_id} diagnosed with {patient.disease}, Severity: {patient.severity} by Nurse {self.nurse_id}")

    def post_surgery_check(self, patient: Patient):
        print(f"Nurse {self.nurse_id} performing post-surgery check on patient {patient.patient_id}")
        sleep(0.5)  # Reduced from 2 seconds to 0.5 seconds
