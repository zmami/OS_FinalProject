from random import sample, uniform
from threading import Thread
from time import sleep

from Ambulance import Ambulance
from ERDoctor import ERDoctor
from Nurse import Nurse


class EmergencyDepartment:
    def __init__(self, num_doctors=50, num_nurses=50):
        self.doctors = [ERDoctor(f"ER{i + 1}") for i in range(num_doctors)]
        self.nurses = [Nurse(f"ERN{i + 1}") for i in range(num_nurses)]

        # Assign nurses to doctors (1:1 ratio now)
        for doctor, nurse in zip(self.doctors, self.nurses):
            doctor.assigned_nurse = nurse
            nurse.assigned_doctor = doctor

        self.ambulance_arrivals = True

    def set_hospital(self, hospital):
        """Set hospital reference for all doctors"""
        for doctor in self.doctors:
            doctor.hospital = hospital

    def get_available_doctors(self, count=1):
        available = [d for d in self.doctors if d.is_available]
        return sample(available, min(count, len(available)))

    def handle_ambulance_arrival(self, ambulance: Ambulance):
        # Get available doctor and nurse for ambulance
        available_doctors = self.get_available_doctors(1)
        if not available_doctors:
            print(f"No doctors available for ambulance {ambulance.ambulance_id}! Patient waiting...")
            return None

        doctor = available_doctors[0]
        nurse = doctor.assigned_nurse

        print(f"Ambulance {ambulance.ambulance_id} attended by Doctor {doctor.doctor_id} and Nurse {nurse.nurse_id}")

        # Assess patient immediately
        patient = ambulance.patient
        nurse.assess_patient(patient)

        if patient.severity is not None:
            # Create proper priority tuple (negative severity, arrival_time, patient)
            priority = (-patient.severity, patient.arrival_time, patient)
            doctor.patient_queue.put(priority)

        return doctor

    def start_ambulance_arrivals(self, hospital):
        """Start a thread for ambulance arrivals"""
        thread = Thread(target=self.ambulance_arrival_loop, args=(hospital,))
        thread.daemon = True  # Set daemon before starting
        thread.start()
        return thread

    def ambulance_arrival_loop(self, hospital):
        """Modify ambulance frequency"""
        while hospital.running:
            if not self.ambulance_arrivals:
                break

            try:
                # Create new ambulance every 10-15 seconds
                ambulance = Ambulance()
                patient = ambulance.pick_up_patient()

                with hospital.stats_lock:
                    hospital.stats.add_ambulance_arrival()
                    hospital.stats.add_er_patient()

                doctor = self.handle_ambulance_arrival(ambulance)
                if doctor and patient.severity is not None:
                    if doctor.treat_patient(patient):
                        hospital.stats.add_survival()
                    else:
                        hospital.stats.add_death()

            except Exception as e:
                print(f"Error in ambulance arrival loop: {e}")

            sleep(uniform(10, 15))  # More consistent ambulance arrivals
