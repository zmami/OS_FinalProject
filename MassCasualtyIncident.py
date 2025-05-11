from random import randint, sample, choice, random
from threading import Thread
from time import time, sleep

from Patient import Patient


class MassCasualtyIncident:
    def __init__(self, hospital):
        self.hospital = hospital
        self.mci_patients = []
        self.is_active = True
        self.death_rate = 0.3  # 30% chance of death during MCI (higher than normal)

    def generate_mci_patient(self):
        """Generate a patient with high severity during MCI"""
        patient = Patient.create_emergency(randint(1, 100), "MCI")  # Use emergency creation
        patient.assign_random_disease()
        # Override severity to be very high (8-10)
        patient.severity = randint(8, 10)
        return patient

    def start_mci(self):
        print("\n🚨 MASS CASUALTY INCIDENT DECLARED! All available medical personnel responding! 🚨\n")

        # Get all available ER doctors
        er_doctors = [d for d in self.hospital.emergency_dept.doctors if d.is_available]

        # Get some regular doctors to help (30% of each department)
        regular_doctors = []
        for dept in self.hospital.departments.values():
            doctors_to_help = sample(dept['doctors'], k=max(1, len(dept['doctors']) // 3))
            regular_doctors.extend(doctors_to_help)

        all_available_doctors = er_doctors + regular_doctors
        print(
            f"Total doctors responding to MCI: {len(all_available_doctors)} ({len(er_doctors)} ER, {len(regular_doctors)} regular)")

        # Start MCI patient arrivals
        thread = Thread(target=self.mci_patient_arrival_loop, args=(all_available_doctors,))
        thread.daemon = True  # Set daemon before starting
        thread.start()
        return thread

    def mci_patient_arrival_loop(self, available_doctors):
        """Generate MCI patients throughout the day"""
        start_time = time()
        day_duration = 60  # 1 minute for MCI day

        while self.is_active and (time() - start_time < day_duration):
            # Generate 3-7 patients every 5-10 seconds during MCI
            batch_size = randint(3, 7)
            for _ in range(batch_size):
                patient = self.generate_mci_patient()
                self.mci_patients.append(patient)
                print(f"MCI Patient {patient.patient_id} arrived with severity {patient.severity}")

                # Assign to available doctor
                if available_doctors:
                    doctor = choice(available_doctors)
                    Thread(target=self.treat_mci_patient, args=(doctor, patient)).start()
                else:
                    print(f"⚠️ No doctors available for MCI patient {patient.patient_id}! Patient waiting...")

            sleep(randint(5, 10))  # 5-10 seconds between batches

    def treat_mci_patient(self, doctor, patient):
        """Use thread pool instead of creating new threads"""

        def process_mci():
            try:
                print(f"Doctor {doctor.doctor_id} treating MCI patient {patient.patient_id}")
                sleep(randint(5, 10))

                needs_blood_work = random() < 0.7
                needs_xray = random() < 0.7
                needs_surgery = random() < 0.5

                if needs_blood_work:
                    doctor.perform_blood_work(patient)
                if needs_xray:
                    doctor.perform_xray(patient)

                if needs_surgery:
                    print(f"MCI Patient {patient.patient_id} requires emergency surgery")
                    sleep(randint(10, 15))

                    if random() < self.death_rate:
                        with self.hospital.stats_lock:
                            self.hospital.stats.add_death(is_mci=True)
                        print(f"⚠️ MCI Patient {patient.patient_id} did not survive surgery")
                        return

                    with self.hospital.stats_lock:
                        self.hospital.stats.add_survival(is_mci=True)
                    print(f"MCI Patient {patient.patient_id} survived surgery")
                    sleep(5)

                print(f"MCI Patient {patient.patient_id} treatment complete")
            except Exception as e:
                print(f"Error treating MCI patient: {e}")

        # Use hospital's thread pool instead of creating new thread
        self.hospital.thread_pool.submit(process_mci)
