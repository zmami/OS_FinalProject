from queue import Queue
from random import choice, uniform
from threading import Lock
from time import sleep

from Doctor import Doctor
from HospitalStatistics import HospitalStatistics
from Nurse import Nurse
from Patient import Patient
from Specialty import Specialty


class DiagnosticsDepartment:
    def __init__(self, num_technicians=10, num_nurses=10):
        self.technicians = [Doctor(f"DIAG{i + 1}", Specialty.DIAGNOSTICS) for i in range(num_technicians)]
        self.nurses = [Nurse(f"DN{i + 1}") for i in range(num_nurses)]

        # Assign nurses to technicians
        for tech, nurse in zip(self.technicians, self.nurses):
            tech.assigned_nurse = nurse
            nurse.assigned_doctor = tech

        self.blood_work_queue = Queue()
        self.xray_queue = Queue()
        self.tech_lock = Lock()

    def schedule_blood_work(self, patient: Patient):
        """Schedule blood work for a patient"""
        self.blood_work_queue.put(patient)

    def schedule_xray(self, patient: Patient):
        """Schedule X-ray for a patient"""
        self.xray_queue.put(patient)

    def perform_blood_work(self, patient: Patient, hospital_stats: HospitalStatistics):
        with self.tech_lock:
            available_techs = [t for t in self.technicians if not t.is_busy]
            if not available_techs:
                print("No technicians available! Blood work delayed...")
                return

            tech = choice(available_techs)
            tech.is_busy = True

        try:
            print(f"Technician {tech.doctor_id} performing blood work for patient {patient.patient_id}")
            sleep(uniform(0.5, 1.0))  # Reduced from 5-10 seconds to 0.5-1 second
            hospital_stats.add_procedure('blood_work')
        finally:
            tech.is_busy = False

    def perform_xray(self, patient: Patient, hospital_stats: HospitalStatistics):
        """Perform X-ray with proper thread safety"""
        with self.tech_lock:
            available_techs = [t for t in self.technicians if not t.is_busy]
            if not available_techs:
                print("No technicians available! X-ray delayed...")
                return

            tech = choice(available_techs)
            tech.is_busy = True

        try:
            print(f"Technician {tech.doctor_id} performing X-ray for patient {patient.patient_id}")
            sleep(uniform(0.5, 1.0))  # Reduced from 5-10 seconds to 0.5-1 second
            hospital_stats.add_procedure('xrays')
        finally:
            tech.is_busy = False
