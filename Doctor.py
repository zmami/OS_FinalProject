from queue import PriorityQueue, Empty
from threading import Thread

from Specialty import Specialty


class Doctor:
    def __init__(self, doctor_id: int, specialty: Specialty):
        self.doctor_id = doctor_id
        self.specialty = specialty
        self.patient_queue = PriorityQueue()  # Change all doctors to use PriorityQueue
        self.assigned_nurse = None
        self.is_busy = False
        self.is_active = True
        self.thread = None

    def start_shift(self):
        """Start doctor's work loop"""
        self.thread = Thread(target=self._work_loop, name=f"Doctor-{self.doctor_id}")
        self.thread.daemon = True
        self.thread.start()

    def _work_loop(self):
        """Continuous loop to process patients"""
        while self.is_active:
            try:
                # Priority queue returns (priority, arrival_time, patient) tuple
                priority_tuple = self.patient_queue.get(timeout=1)
                patient = priority_tuple[2]  # Get patient from tuple
                self.is_busy = True
                self.treat_patient(patient)
                self.is_busy = False
                self.patient_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"Error in doctor {self.doctor_id} work loop: {e}")
                self.is_busy = False

    def stop_shift(self):
        """Stop the doctor's work loop"""
        self.is_active = False
        if self.thread:
            self.thread.join(timeout=2)

    def perform_blood_work(self, patient: Patient):
        """Request blood work from diagnostics department"""
        print(f"Requesting blood work for patient {patient.patient_id}")
        self.hospital.diagnostics_dept.schedule_blood_work(patient)
        self.hospital.diagnostics_dept.perform_blood_work(patient, self.hospital.stats)

    def perform_xray(self, patient: Patient):
        """Request X-ray from diagnostics department"""
        print(f"Requesting X-ray for patient {patient.patient_id}")
        self.hospital.diagnostics_dept.schedule_xray(patient)
        self.hospital.diagnostics_dept.perform_xray(patient, self.hospital.stats)

    def perform_surgery(self, patient: Patient):
        """Request surgery from surgery department"""
        print(f"Requesting surgery for patient {patient.patient_id}")
        self.hospital.surgery_dept.schedule_surgery(patient, self)
        return self.hospital.surgery_dept.perform_surgery(patient, self.hospital.stats)

    def treat_patient(self, patient: Patient):
        try:
            time.sleep(random.uniform(0.5, 1.0))  # Reduced from 2-4 seconds to 0.5-1 second

            with self.hospital.stats_lock:  # Ensure thread-safe statistics
                # Track procedures
                if random.random() < 0.8:  # 80% chance
                    self.perform_blood_work(patient)
                    self.hospital.stats.add_procedure('blood_work')
                if random.random() < 0.8:  # 80% chance
                    self.perform_xray(patient)
                    self.hospital.stats.add_procedure('xrays')

                # Track surgeries and outcomes
                if random.random() < 0.6 or patient.severity >= 8:  # More surgeries
                    success = self.perform_surgery(patient)
                    if success:
                        self.hospital.stats.add_survival()
                    else:
                        self.hospital.stats.add_death()
                    return success

                # Track deaths and survivals
                if patient.severity >= 8 and random.random() < 0.3:
                    self.hospital.stats.add_death()
                    return False

                self.hospital.stats.add_survival()
                return True

        except Exception as e:
            print(f"Error in treat_patient: {e}")
            return False
