from sys import exit
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from random import randint, choice
from signal import signal, SIGINT, SIGTERM
from threading import Lock, Thread
from time import time, sleep

from DiagnosticsDepartment import DiagnosticsDepartment
from Doctor import Doctor
from EmergencyDepartment import EmergencyDepartment
from HospitalStatistics import HospitalStatistics
from Nurse import Nurse
from OS_FinalProject.MassCasualtyIncident import MassCasualtyIncident
from Receptionist import Receptionist
from Specialty import Specialty
from SurgeryDepartment import SurgeryDepartment


class HospitalSimulation:
    def __init__(self):
        print("Starting hospital simulation...")
        self.receptionists = [Receptionist(i + 1) for i in range(6)]

        # Set hospital reference for receptionists
        for receptionist in self.receptionists:
            receptionist.hospital = self

        # Create regular departments with 10 doctors each
        self.departments = {}
        for specialty in [s for s in Specialty if s not in [Specialty.SURGERY, Specialty.DIAGNOSTICS]]:
            doctors = [Doctor(f"{specialty.value[0]}{i + 1}", specialty) for i in range(10)]
            nurses = [Nurse(f"{specialty.value[0]}N{i + 1}") for i in range(15)]  # 15 nurses per department

            # Assign nurses to doctors (some doctors get 2 nurses)
            for i, doctor in enumerate(doctors):
                nurse1 = nurses[i]
                nurse2 = nurses[i + len(doctors)] if i < len(nurses) - len(doctors) else None

                doctor.assigned_nurse = nurse1
                nurse1.assigned_doctor = doctor
                if nurse2:
                    nurse2.assigned_doctor = doctor
                doctor.hospital = self

            self.departments[specialty] = {
                'doctors': doctors,
                'nurses': nurses
            }

        # Create specialized departments
        self.surgery_dept = SurgeryDepartment(num_surgeons=10, num_nurses=15)
        self.diagnostics_dept = DiagnosticsDepartment(num_technicians=10, num_nurses=10)

        # Set hospital reference for specialized departments
        for surgeon in self.surgery_dept.surgeons:
            surgeon.hospital = self
        for tech in self.diagnostics_dept.technicians:
            tech.hospital = self

        # Create Emergency Department with 50 nurses
        self.emergency_dept = EmergencyDepartment(num_doctors=50, num_nurses=50)
        self.emergency_dept.set_hospital(self)  # Set hospital reference for ER doctors

        self.assessment_nurses = [Nurse(f"AN{i + 1}") for i in range(10)]  # More assessment nurses
        self.waiting_room = deque()
        self.running = True
        self.simulation_time = 7 * 60  # One week = 7 minutes in real time
        self.mci = None
        self.mci_day = randint(1, 7)  # Random day for MCI to occur
        self.stats = HospitalStatistics()
        self.stats_lock = Lock()  # Add lock for statistics
        self.threads = []  # Track all threads

        # Add signal handling
        signal(SIGINT, self.signal_handler)
        signal(SIGTERM, self.signal_handler)

        # Add thread pool
        self.thread_pool = ThreadPoolExecutor(max_workers=50, thread_name_prefix="Hospital")

        # Start all medical staff threads
        self._start_medical_staff()

    def _start_medical_staff(self):
        """Start all doctor and nurse threads"""
        # Start regular department staff
        for dept in self.departments.values():
            for doctor in dept['doctors']:
                doctor.start_shift()
            for nurse in dept['nurses']:
                nurse.start_shift()

        # Start ER staff
        for doctor in self.emergency_dept.doctors:
            doctor.start_shift()
        for nurse in self.emergency_dept.nurses:
            nurse.start_shift()

        # Start specialized department staff
        for surgeon in self.surgery_dept.surgeons:
            surgeon.start_shift()
        for tech in self.diagnostics_dept.technicians:
            tech.start_shift()

        # Start assessment nurses
        for nurse in self.assessment_nurses:
            nurse.start_shift()

    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        print("\n\nReceived termination signal. Shutting down simulation...")
        self.cleanup()
        exit(0)

    def cleanup(self):
        """Enhanced cleanup with thread pool shutdown"""
        print("Stopping all hospital operations...")
        self.running = False

        # Stop ambulance arrivals
        if hasattr(self, 'emergency_dept'):
            self.emergency_dept.ambulance_arrivals = False

        # Stop MCI if active
        if self.mci:
            self.mci.is_active = False

        # Stop all medical staff
        for dept in self.departments.values():
            for doctor in dept['doctors']:
                doctor.stop_shift()
            for nurse in dept['nurses']:
                nurse.stop_shift()

        for doctor in self.emergency_dept.doctors:
            doctor.stop_shift()
        for nurse in self.emergency_dept.nurses:
            nurse.stop_shift()

        for surgeon in self.surgery_dept.surgeons:
            surgeon.stop_shift()
        for tech in self.diagnostics_dept.technicians:
            tech.stop_shift()

        for nurse in self.assessment_nurses:
            nurse.stop_shift()

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True, cancel_futures=True)

        # Wait for remaining threads
        for thread in self.threads:
            if thread and thread.is_alive():
                try:
                    thread.join(timeout=2)
                except TimeoutError:
                    print(f"Force terminating thread {thread.name}")

        print("All operations stopped. Simulation terminated.")

    def patient_arrival(self):
        start_time = time()
        day = 0
        patients_today = 0
        current_receptionist = 0

        while self.running and (time() - start_time < self.simulation_time):
            current_day = int((time() - start_time) / 60)

            # Reset counter for new day
            if current_day > day:
                day = current_day
                patients_today = 0
                print(f"\nStarting Day {current_day + 1}")

            # Process exactly 150 patients per day in smaller groups
            if patients_today < 150:
                # Process 15 patients every 6 seconds (10 groups of 15 = 150 per day)
                group_size = 15
                patients_today += group_size

                for _ in range(group_size):
                    age = randint(1, 100)
                    # Round-robin assignment
                    receptionist = self.receptionists[current_receptionist]
                    current_receptionist = (current_receptionist + 1) % len(self.receptionists)
                    patient = receptionist.register_patient(age)
                    self.process_patient(patient)

                # Wait 6 seconds between groups
                sleep(6)  # This ensures even distribution across the minute
            else:
                # Wait for next day
                sleep(0.1)

    def process_patient(self, patient):
        def process():
            try:
                nurse = choice(self.assessment_nurses)
                nurse.assess_patient(patient)

                if patient.severity is None:
                    return

                specialty = Specialty.get_specialty_for_disease(patient.disease)

                # Update statistics immediately
                with self.stats_lock:
                    self.stats.add_visit(patient)
                    self.stats.add_condition(patient.disease)
                    self.stats.add_department_visit(specialty)

                    # Increase ER cases for severe patients
                    if patient.severity >= 7:
                        self.stats.add_er_patient()

                    waiting_time = time() - patient.arrival_time
                    self.stats.add_waiting_time(waiting_time)

                # Route patients based on severity
                if patient.severity >= 8:
                    self.handle_emergency(patient)
                else:
                    department = self.departments[specialty]
                    doctor = min(department['doctors'], key=lambda d: d.patient_queue.qsize())
                    priority = (-patient.severity, patient.arrival_time, patient)
                    doctor.patient_queue.put(priority)

            except Exception as e:
                print(f"Error processing patient {patient.patient_id}: {e}")

        self.thread_pool.submit(process)

    def handle_emergency(self, patient):
        arrival_time = time()
        print(f"Emergency case! Patient {patient.patient_id} directed to ER")

        try:
            # Ensure patient has severity set
            if patient.severity is None:
                # Get a nurse to assess the patient first
                nurse = choice(self.emergency_dept.nurses)
                nurse.assess_patient(patient)

            if patient.severity is None:
                print(f"Error: Cannot process emergency patient {patient.patient_id} without severity!")
                return

            # Get available ER doctor with shortest queue
            available_doctors = [d for d in self.emergency_dept.doctors if d.is_available]
            if not available_doctors:
                print("No ER doctors available! Patient waiting...")
                return

            doctor = min(available_doctors, key=lambda d: d.patient_queue.qsize())

            # Add to priority queue with consistent tuple format
            priority_tuple = (-patient.severity, patient.arrival_time, patient)
            doctor.patient_queue.put(priority_tuple)

            # Update statistics
            waiting_time = time() - arrival_time
            with self.stats_lock:
                self.stats.add_waiting_time(waiting_time, is_mci=bool(self.mci))
                self.stats.add_er_patient(is_mci=bool(self.mci))

            # Treat patient
            if doctor.treat_patient(patient):
                self.stats.add_survival()
                print(f"Emergency patient {patient.patient_id} has been stabilized and discharged")
            else:
                self.stats.add_death()
                print(f"Emergency patient {patient.patient_id} treatment unsuccessful")

        except Exception as e:
            print(f"Error handling emergency patient {patient.patient_id}: {e}")

    def run(self):
        """Start the hospital simulation"""
        try:
            print("Starting simulation for one week...")
            print("Press Ctrl+C to stop the simulation at any time")

            start_time = time()
            end_time = start_time + self.simulation_time  # 7 minutes total

            # Start regular patient arrivals
            patient_thread = Thread(target=self.patient_arrival, name="PatientArrival")
            patient_thread.daemon = True
            patient_thread.start()

            # Start ambulance arrivals
            ambulance_thread = self.emergency_dept.start_ambulance_arrivals(self)

            # Add threads to tracking list
            self.threads.extend([patient_thread, ambulance_thread])

            # Monitor for MCI day and show progress
            mci_thread = None
            while self.running and time() <= end_time:  # Changed < to <= to include full last day
                current_time = time() - start_time
                current_day = int(current_time / 60) + 1  # Each day is 1 minute
                progress = (current_time / self.simulation_time) * 100

                # Clear line and show progress
                print(f"\rSimulation Progress: Day {current_day}/7 ({progress:.1f}%)", end="")

                # Start MCI on the designated day
                if current_day == self.mci_day and not self.mci:
                    print("\n")  # New line for MCI message
                    self.mci = MassCasualtyIncident(self)
                    mci_thread = self.mci.start_mci()
                    self.threads.append(mci_thread)

                # End MCI after the day is over
                elif current_day > self.mci_day and self.mci:
                    self.mci.is_active = False
                    if mci_thread:
                        mci_thread.join(timeout=2)
                    print("\n🏥 Mass Casualty Incident response completed")
                    self.mci = None

                # Only end after day 7 is fully complete
                if current_time >= self.simulation_time:  # Changed condition to ensure full 7 days
                    print("\nDay 7 completed. Ending simulation...")
                    self.running = False
                    break

                sleep(1)  # Check progress every second

            # Give extra time for day 7 to complete all processes
            print("\nFinalizing day 7 operations...")
            sleep(10)  # Allow time for final ambulances and treatments

            # Wait for all threads to complete
            print("\nWaiting for all ongoing treatments to complete...")

            # Check patient queues
            all_doctors = (
                    list(self.emergency_dept.doctors) +
                    list(self.surgery_dept.surgeons) +
                    list(self.diagnostics_dept.technicians)
            )
            for dept in self.departments.values():
                all_doctors.extend(dept['doctors'])

            # Wait for queues to empty and doctors to finish
            max_wait = 60  # Maximum 60 seconds to wait
            wait_start = time()
            while time() - wait_start < max_wait:
                queues_empty = all(doctor.patient_queue.empty() for doctor in all_doctors)
                doctors_free = all(not doctor.is_busy for doctor in all_doctors)

                if queues_empty and doctors_free:
                    print("All patients have been treated.")
                    break
                sleep(1)

            # Final check for any active threads
            active_threads = [t for t in self.threads if t and t.is_alive()]
            if active_threads:
                print(f"Waiting for {len(active_threads)} active threads to complete...")
                for thread in active_threads:
                    thread.join(timeout=2)

            print("Simulation ended. All operations completed.")

        except KeyboardInterrupt:
            print("\nSimulation interrupted by user...")
        except Exception as e:
            print(f"\nError during simulation: {e}")
        finally:
            # Ensure proper cleanup at the end
            self.running = False
            self.cleanup()

            if self.stats:
                total_time = time() - start_time
                print(f"\nSimulation ran for {total_time / 60:.1f} minutes of real time")
                print("Generating statistics...")
                self.stats.visualize_statistics()
                print("Statistics saved to 'hospital_statistics.png'")
