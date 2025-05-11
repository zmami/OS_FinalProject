from queue import PriorityQueue
from random import randint, random
from time import sleep

from Doctor import Doctor
from Patient import Patient
from Specialty import Specialty


class ERDoctor(Doctor):
    def __init__(self, doctor_id):
        super().__init__(doctor_id, Specialty.GENERAL)
        self.patient_queue = PriorityQueue()  # Priority queue for ER doctors
        self.is_available = True

    def _work_loop(self):
        """Override work loop to handle priority queue tuples"""
        while self.is_active:
            try:
                # Get patient from queue with timeout
                priority_tuple = self.patient_queue.get(timeout=1)

                # Extract patient from tuple safely
                patient = None
                if isinstance(priority_tuple, tuple):
                    if len(priority_tuple) == 3:
                        # Handle (negative severity, arrival_time, patient) tuple
                        patient = priority_tuple[2]
                    elif len(priority_tuple) == 2:
                        # Handle (priority, patient) tuple
                        patient = priority_tuple[1]
                else:
                    # Handle direct patient object
                    patient = priority_tuple

                if patient is None:
                    print(f"Error: Invalid priority tuple format: {priority_tuple}")
                    continue

                self.is_busy = True
                self.treat_patient(patient)
                self.is_busy = False
                self.patient_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in ER doctor {self.doctor_id} work loop: {e}")
                self.is_busy = False

    def treat_patient(self, patient: Patient):
        try:
            self.is_available = False
            print(f"ER Doctor {self.doctor_id} treating emergency patient {patient.patient_id}...")
            sleep(randint(5, 10))

            # Increase Code Blue frequency
            code_blue = random() < 0.15  # 15% chance of Code Blue
            if code_blue:
                return self.handle_code_blue(patient)

            # Regular emergency treatment with higher mortality
            needs_blood_work = random() < 0.8  # 80% chance
            needs_xray = random() < 0.8  # 80% chance
            needs_surgery = random() < 0.6  # 60% chance

            if needs_blood_work:
                self.perform_blood_work(patient)
            if needs_xray:
                self.perform_xray(patient)

            if needs_surgery:
                success = self.perform_surgery(patient)
                self.is_available = True
                return success

            # Add chance of death even without surgery
            if patient.severity >= 7 and random() < 0.25:  # 25% death chance for severe cases
                self.is_available = True
                return False

            self.is_available = True
            return True
        except Exception as e:
            print(f"Error treating patient: {e}")
            self.is_available = True
            return False

    def handle_code_blue(self, patient: Patient):
        print(f"CODE BLUE for patient {patient.patient_id}!")
        sleep(randint(5, 10))

        # Increase Code Blue mortality
        patient_survived = random() < 0.2  # Only 20% survival rate
        if patient_survived:
            print(f"Patient {patient.patient_id} survived Code Blue!")
            self.hospital.stats.add_code_blue(True)
            return True
        else:
            print(f"Patient {patient.patient_id} did not survive Code Blue.")
            self.hospital.stats.add_code_blue(False)
            return False
