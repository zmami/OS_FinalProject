from queue import Queue, PriorityQueue, Empty
from random import choice, randint, uniform, random
from threading import Event, Lock, Semaphore, Thread
from time import sleep, time

from Patient import Patient
from Statistics import Statistics


class HospitalSimulation:
    def __init__(self, days=7, simulation_speed=1.0):
        # Configurable parameters
        self.days = days
        self.simulation_speed = simulation_speed  # Higher values = faster simulation
        self.current_day = 0
        self.is_mci_day = False
        self.mci_in_progress = False

        # Patient generation settings
        self.patients_per_day = 100
        self.ambulances_per_day = 50
        self.mci_patients = 150

        # Department settings
        self.departments = {
            "Cardiology": ["heart attack", "arrhythmia", "heart failure"],
            "Neurology": ["stroke", "concussion", "seizure"],
            "Orthopedics": ["broken arm", "broken leg", "sprained ankle", "fracture"],
            "Pulmonology": ["pneumonia", "asthma", "bronchitis"],
            "Gastroenterology": ["appendicitis", "ulcer", "food poisoning"],
            "General Surgery": ["hernia", "gallstones"],
            "Internal Medicine": ["high fever", "flu", "diabetes", "hypertension"]
        }

        # Staff settings
        self.doctors_per_department = 8
        self.er_doctors = 60
        self.receptionists = 5
        self.nurses_per_doctor = 2

        # Generate realistic patient names
        self.first_names = ["John", "Emma", "Michael", "Olivia", "William", "James", "Ava", "Benjamin"]
        self.last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

        # Initialize statistics
        self.stats = Statistics()

        # Initialize queues and resources
        self.initialize_queues_and_resources()

        # Thread lock
        self.lock = Lock()
        self.mci_lock = Lock()

        # Event to signal simulation completion
        self.simulation_complete = Event()

        # Current simulation time
        self.current_time = 0

        # Special events tracking
        self.code_blue_in_progress = False
        self.code_blue_lock = Lock()

        # Available staff tracking
        self.available_er_doctors = Semaphore(self.er_doctors)
        self.available_er_nurses = Semaphore(self.er_doctors * self.nurses_per_doctor)
        self.available_regular_doctors = {dept: Semaphore(self.doctors_per_department) for dept in
                                          self.departments}
        self.available_regular_nurses = {dept: Semaphore(self.doctors_per_department * self.nurses_per_doctor)
                                         for dept in self.departments}
        self.available_receptionists = Semaphore(self.receptionists)

        # Regular doctor pool for MCI assistance
        self.regular_doctors_helping_mci = Semaphore(0)  # Initially no regular doctors helping
        self.mci_assistance_needed = Event()  # Signal for regular doctors to help

    def initialize_queues_and_resources(self):
        # Reception queue
        self.reception_queue = Queue()

        # Nurse assessment queues
        self.assessment_queue = Queue()

        # Department doctor queues (FIFO)
        self.department_queues = {dept: Queue() for dept in self.departments}

        # ER doctor queues (priority)
        self.er_queues = [PriorityQueue() for _ in range(self.er_doctors)]

        # Testing queues
        self.blood_work_queue = Queue()
        self.xray_queue = Queue()

        # Surgery queues
        self.surgery_queue = Queue()

        # Ambulance queue
        self.ambulance_queue = Queue()

        # Code blue queue
        self.code_blue_queue = Queue()

        # MCI queue - for handling mass casualty incidents
        self.mci_queue = PriorityQueue()

    def simulate_time(self, seconds):
        """Simulate the passage of time adjusted by simulation speed."""
        scaled_time = seconds / self.simulation_speed

        # Add a minimum time cap to avoid excessive sleeping
        scaled_time = min(scaled_time, 0.5)

        if scaled_time > 0:
            sleep(scaled_time)

        # Always advance the simulation clock by the actual seconds
        self.current_time += seconds
        return seconds

    def generate_patient_name(self):
        """Generate a random patient name."""
        first_name = choice(self.first_names)
        last_name = choice(self.last_names)
        return f"{first_name} {last_name}"

    def assign_condition_and_severity(self, patient, is_mci=False):
        """Assign a random condition and severity to a patient."""
        # Flatten the conditions from all departments
        all_conditions = []
        for conditions in self.departments.values():
            all_conditions.extend(conditions)

        if is_mci:
            # MCI patients get trauma conditions
            trauma_conditions = ["multiple trauma", "severe bleeding", "crush injury",
                                 "head injury", "penetrating trauma", "blast injury"]
            patient.condition = choice(trauma_conditions)
            patient.severity = randint(8, 10)  # High severity for MCI patients
            patient.is_mci_patient = True
        else:
            # Regular patient gets random condition
            patient.condition = choice(all_conditions)

            # Assign severity (1-10 scale, with 10 being most severe)
            if self.is_mci_day and not self.mci_in_progress:
                # During MCI day but not MCI event, normal distribution of severity
                patient.severity = randint(1, 10)
            elif self.is_mci_day and self.mci_in_progress:
                # During MCI event, non-MCI patients less likely to have high severity
                patient.severity = randint(1, 8)
            else:
                # Normal day
                patient.severity = randint(1, 10)

        # Assign department based on condition
        for dept, conditions in self.departments.items():
            if patient.condition in conditions:
                patient.department = dept
                break

        # If no matching department found (e.g., for MCI trauma conditions)
        if patient.department is None:
            # Trauma cases go to orthopedics or ER depending on severity
            if "trauma" in patient.condition or "injury" in patient.condition:
                if patient.severity >= 8:
                    # Handled in ER
                    patient.department = "ER"
                else:
                    patient.department = "Orthopedics"
            else:
                # Default to Internal Medicine
                patient.department = "Internal Medicine"

    def receptionist_thread(self):
        """Handle patient registration."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient_data = self.reception_queue.get(timeout=0.5)

                # Skip if we only got day info (no patient object)
                if len(patient_data) < 2:
                    self.reception_queue.task_done()
                    continue

                day, patient = patient_data

                # Acquire a receptionist
                if not self.available_receptionists.acquire(blocking=False):
                    # If no receptionist available, put back in queue and try again later
                    self.reception_queue.put(patient_data)
                    self.reception_queue.task_done()
                    continue

                # Simulate registration time
                registration_time = uniform(3, 6)
                self.simulate_time(registration_time)

                # Update patient record
                patient.registration_time = time()

                # Display registration message
                print(f"📋 ({self.format_time()}) Patient {patient.name} registered")

                # Send to nurse assessment
                self.assessment_queue.put(patient)

                # Release the receptionist
                self.available_receptionists.release()

                # Mark task as complete
                self.reception_queue.task_done()
            except Empty:
                continue

    def nurse_assessment_thread(self):
        """Handle nurse assessment of patients."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.assessment_queue.get(timeout=0.5)

                # Simulate assessment time 
                assessment_time = uniform(30, 60)
                self.simulate_time(assessment_time)

                # Assign condition and severity if not already set (ambulance patients already have them)
                if patient.condition is None:
                    self.assign_condition_and_severity(patient)

                # Update patient record
                patient.assessment_time = time()

                # Display assessment message
                print(
                    f"🩺 ({self.format_time()}) Nurse assessed {patient.name}: {patient.condition}, severity {patient.severity}")

                # Route patient based on severity
                if patient.severity >= 8:
                    # ER patient - send to a random ER doctor queue
                    er_queue_idx = randint(0, self.er_doctors - 1)
                    self.er_queues[er_queue_idx].put(patient)
                    print(f"🚨 ({self.format_time()}) Patient {patient.name} sent to ER")
                else:
                    # Regular patient - find appropriate department
                    routed = False
                    for dept, conditions in self.departments.items():
                        if patient.condition in conditions:
                            self.department_queues[dept].put(patient)
                            print(f"🏥 ({self.format_time()}) Patient {patient.name} routed to {dept}")
                            routed = True
                            break

                    # Default to Internal Medicine if no matching department
                    if not routed:
                        self.department_queues["Internal Medicine"].put(patient)
                        print(f"🏥 ({self.format_time()}) Patient {patient.name} routed to Internal Medicine (default)")

                # Mark task as complete
                self.assessment_queue.task_done()
            except Empty:
                continue

    def blood_work_thread(self):
        """Handle blood work tests."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.blood_work_queue.get(timeout=0.5)

                # Simulate blood work time
                blood_work_time = uniform(5, 10)
                self.simulate_time(blood_work_time)

                # Update patient record
                patient.had_blood_work = True

                # Display blood work message
                print(f"🩸 ({self.format_time()}) Blood work completed for {patient.name}")

                # Check if patient also needed an X-ray
                if hasattr(patient, 'needs_xray') and patient.needs_xray:
                    self.xray_queue.put(patient)
                else:
                    # Continue to doctor
                    if patient.severity >= 8:
                        # Send back to ER
                        er_queue_idx = randint(0, self.er_doctors - 1)
                        self.er_queues[er_queue_idx].put(patient)
                    else:
                        # Send back to department
                        self.department_queues[patient.department].put(patient)

                # Mark task as complete
                self.blood_work_queue.task_done()
            except Empty:
                continue

    def xray_thread(self):
        """Handle X-ray tests."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.xray_queue.get(timeout=0.5)

                # Simulate X-ray time
                xray_time = uniform(5, 10)
                self.simulate_time(xray_time)

                # Update patient record
                patient.had_xray = True

                # Display X-ray message
                print(f"📷 ({self.format_time()}) X-ray completed for {patient.name}")

                # Continue to doctor
                if patient.severity >= 8:
                    # Send back to ER
                    er_queue_idx = randint(0, self.er_doctors - 1)
                    self.er_queues[er_queue_idx].put(patient)
                else:
                    # Send back to department
                    self.department_queues[patient.department].put(patient)

                # Mark task as complete
                self.xray_queue.task_done()
            except Empty:
                continue

    def surgery_thread(self):
        """Handle surgeries."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.surgery_queue.get(timeout=0.5)

                # Simulate surgery time
                surgery_time = uniform(10, 15)
                self.simulate_time(surgery_time)

                # Update patient record
                patient.had_surgery = True

                # Determine surgery outcome
                death_chance = 0.25

                # Increased death chance during MCI
                if self.is_mci_day and self.mci_in_progress:
                    death_chance = 0.40

                    # Even higher chance for MCI patients
                    if patient.is_mci_patient:
                        death_chance = 0.50

                if random() < death_chance:
                    patient.dead = True
                    patient.surgery_success = False
                    print(f"💀 ({self.format_time()}) Surgery for {patient.name} failed. Patient died.")
                else:
                    patient.surgery_success = True
                    print(f"✅ ({self.format_time()}) Surgery for {patient.name} successful.")

                    # If successful, patient stays for recovery
                    recovery_time = 5
                    self.simulate_time(recovery_time)
                    print(f"🛌 ({self.format_time()}) {patient.name} in post-surgery recovery.")

                    # Nurse checks on patient
                    self.simulate_time(2)
                    print(f"👩‍⚕️ ({self.format_time()}) Nurse checked on {patient.name} after surgery.")

                    # Discharge patient
                    patient.discharge_time = time()
                    print(f"🚶 ({self.format_time()}) {patient.name} discharged after surgery.")

                # Record statistics for the current day
                self.stats.record_visit(self.current_day, patient)

                # If patient was an MCI patient, also record those stats
                if patient.is_mci_patient:
                    self.stats.record_mci_patient(patient)

                # Mark task as complete
                self.surgery_queue.task_done()
            except Empty:
                continue

    def code_blue_thread(self):
        """Handle Code Blue emergencies."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.code_blue_queue.get(timeout=0.5)

                with self.code_blue_lock:
                    self.code_blue_in_progress = True
                    print(f"⚠️ ({self.format_time()}) CODE BLUE initiated for {patient.name}")

                    # Acquire 2 ER doctors and 1 nurse
                    for _ in range(2):
                        self.available_er_doctors.acquire(timeout=1)
                    self.available_er_nurses.acquire(timeout=1)

                    # Handle Code Blue event
                    self.simulate_time(8)  # Code Blue response time

                    # Determine outcome 
                    if random() < 0.20:  # 20% survival rate 
                        patient.code_blue_success = True
                        print(f"✅ ({self.format_time()}) CODE BLUE successful for {patient.name}. Patient stabilized.")
                    else:
                        patient.code_blue_success = False
                        patient.dead = True
                        print(f"💀 ({self.format_time()}) CODE BLUE unsuccessful for {patient.name}. Patient died.")

                    # Update patient record
                    patient.had_code_blue = True

                    # Release the doctors and nurse
                    for _ in range(2):
                        try:
                            self.available_er_doctors.release()
                        except:
                            pass
                    try:
                        self.available_er_nurses.release()
                    except:
                        pass

                    self.code_blue_in_progress = False

                # If patient survived, continue treatment
                if not patient.dead:
                    er_queue_idx = randint(0, self.er_doctors - 1)
                    self.er_queues[er_queue_idx].put(patient)
                else:
                    # Record statistics for the dead patient
                    self.stats.record_visit(self.current_day, patient)

                    # If patient was an MCI patient, also record those stats
                    if patient.is_mci_patient:
                        self.stats.record_mci_patient(patient)

                # Mark task as complete
                self.code_blue_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                # Ensure the code blue in progress flag is reset if an error occurs
                self.code_blue_in_progress = False
                continue

    def ambulance_thread(self):
        """Handle ambulance arrivals."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get an ambulance from the queue
                ambulance_data = self.ambulance_queue.get(timeout=0.5)
                day, _ = ambulance_data

                # Create a new patient
                patient = Patient(self.generate_patient_name(), time())
                patient.came_by_ambulance = True

                # Try to acquire an ER doctor and nurse
                doctor_acquired = self.available_er_doctors.acquire(timeout=1)
                nurse_acquired = self.available_er_nurses.acquire(timeout=1)

                # Simulate ambulance handling time
                self.simulate_time(uniform(3, 6))

                # Assign condition and severity
                self.assign_condition_and_severity(patient)

                # Force severity to be high for ambulance patients
                if patient.severity < 7:
                    patient.severity = randint(7, 10)

                print(
                    f"🚑 ({self.format_time()}) Ambulance arrived with {patient.name}: {patient.condition}, severity {patient.severity}")

                # Release the doctor and nurse if acquired
                if doctor_acquired:
                    try:
                        self.available_er_doctors.release()
                    except:
                        pass
                if nurse_acquired:
                    try:
                        self.available_er_nurses.release()
                    except:
                        pass

                # Send to appropriate ER queue
                er_queue_idx = randint(0, self.er_doctors - 1)
                self.er_queues[er_queue_idx].put(patient)

                # Mark ambulance task as complete
                self.ambulance_queue.task_done()
            except Empty:
                continue
            except Exception:
                # Continue even if there's an error
                continue

    def mci_assistant_thread(self, department):
        """Thread for regular department doctors helping during MCI."""
        while not self.simulation_complete.is_set():
            # Wait for signal that MCI assistance is needed
            if not self.mci_assistance_needed.is_set():
                sleep(0.1)
                continue

            # Try to acquire a regular doctor from this department
            if self.available_regular_doctors[department].acquire(blocking=False):
                # Signal that this doctor is now helping with MCI
                try:
                    self.regular_doctors_helping_mci.release()
                except:
                    pass

                # Keep doctor occupied with MCI until it's over
                while self.mci_in_progress and not self.simulation_complete.is_set():
                    try:
                        # Try to get a patient from MCI queue
                        patient = self.mci_queue.get(timeout=0.5)

                        # Mark the time doctor starts seeing patient
                        patient.doctor_start_time = time()

                        # Calculate waiting time
                        patient.waiting_time = patient.doctor_start_time - patient.arrival_time

                        # Simulate doctor examination time
                        examination_time = uniform(5, 10)
                        self.simulate_time(examination_time)

                        print(
                            f"👨‍⚕️ ({self.format_time()}) Doctor from {department} examined MCI patient {patient.name}")

                        # Higher chance for surgery for MCI patients
                        surgery_needed = random() < 0.50  # 50% chance for surgery

                        if surgery_needed:
                            print(f"🔪 ({self.format_time()}) MCI patient {patient.name} needs surgery")
                            self.surgery_queue.put(patient)
                        else:
                            # No surgery needed
                            patient.doctor_end_time = time()

                            # Determine if patient survives (higher death chance during MCI)
                            if random() < 0.30:  # 30% chance of death without surgery 
                                patient.dead = True
                                print(f"💀 ({self.format_time()}) MCI patient {patient.name} died during treatment")
                            else:
                                patient.discharge_time = time()
                                print(f"🚶 ({self.format_time()}) MCI patient {patient.name} discharged after treatment")

                            # Record visit statistics
                            self.stats.record_visit(self.current_day, patient)
                            self.stats.record_mci_patient(patient)

                        # Mark task as done
                        self.mci_queue.task_done()
                    except Empty:
                        # No MCI patients right now, wait a bit
                        sleep(0.1)

                # MCI is over, return doctor to regular duties
                try:
                    self.available_regular_doctors[department].release()
                    print(f"👨‍⚕️ ({self.format_time()}) Doctor from {department} returned to regular duties after MCI")
                except:
                    pass

    def regular_doctor_thread(self, department):
        """Thread for regular department doctors."""
        while not self.simulation_complete.is_set():
            try:
                # Acquire a doctor from the department
                if not self.available_regular_doctors[department].acquire(timeout=0.5):
                    continue

                # If MCI is in progress and assistance is needed, this doctor might be reassigned
                if self.is_mci_day and self.mci_in_progress and self.mci_assistance_needed.is_set():
                    # 30% chance for regular doctors to be reassigned to MCI
                    if random() < 0.30:
                        # Release the doctor slot to be handled by mci_assistant_thread
                        try:
                            self.available_regular_doctors[department].release()
                        except:
                            pass
                        sleep(0.1)  # Wait a bit before trying again
                        continue

                # Try to get a patient from the department queue
                try:
                    patient = self.department_queues[department].get(timeout=0.5)
                except Empty:
                    # If no patients, release the doctor
                    try:
                        self.available_regular_doctors[department].release()
                    except:
                        pass
                    continue

                # Mark the time doctor starts seeing patient
                patient.doctor_start_time = time()

                # Calculate waiting time
                patient.waiting_time = patient.doctor_start_time - patient.arrival_time

                # Simulate doctor examination time 
                examination_time = uniform(20, 40)
                self.simulate_time(examination_time)

                print(f"👨‍⚕️ ({self.format_time()}) Doctor in {department} examined {patient.name}")

                # Check if surgery is needed 
                surgery_needed = random() < 0.30

                if surgery_needed:
                    print(f"🔪 ({self.format_time()}) {patient.name} needs surgery")
                    self.surgery_queue.put(patient)
                else:
                    # No surgery needed, patient can be discharged
                    patient.doctor_end_time = time()
                    patient.discharge_time = time()
                    print(f"🚶 ({self.format_time()}) {patient.name} discharged from {department}")

                    # Record visit statistics
                    self.stats.record_visit(self.current_day, patient)

                # Release the doctor
                try:
                    self.available_regular_doctors[department].release()
                except:
                    pass

                # Mark task as done
                self.department_queues[department].task_done()
            except Exception:
                # If there's an error, make sure to release the doctor
                try:
                    self.available_regular_doctors[department].release()
                except:
                    pass
                continue

    def er_doctor_thread(self, queue_idx):
        """Thread for ER doctors."""
        while not self.simulation_complete.is_set():
            try:
                # Acquire an ER doctor
                if not self.available_er_doctors.acquire(timeout=0.5):
                    continue

                # Check if there's an MCI patient with priority
                mci_patient = None
                if self.is_mci_day and self.mci_in_progress:
                    try:
                        # Try to get an MCI patient without blocking
                        mci_patient = self.mci_queue.get(block=False)
                    except Empty:
                        pass

                if mci_patient:
                    # We got an MCI patient, treat them
                    patient = mci_patient
                else:
                    # No MCI patient, get next from regular ER queue
                    try:
                        patient = self.er_queues[queue_idx].get(timeout=0.5)
                    except Empty:
                        # No patients in queue, release doctor and continue
                        try:
                            self.available_er_doctors.release()
                        except:
                            pass
                        continue

                # Mark the time doctor starts seeing patient
                patient.doctor_start_time = time()

                # Calculate waiting time
                patient.waiting_time = patient.doctor_start_time - patient.arrival_time

                # Check for Code Blue event 
                code_blue = random() < 0.15

                if code_blue and not self.code_blue_in_progress:
                    print(f"⚠️ ({self.format_time()}) Code Blue initiated for {patient.name}")
                    self.code_blue_queue.put(patient)

                    # Release the doctor for now
                    try:
                        self.available_er_doctors.release()
                    except:
                        pass

                    # Mark task as done
                    if mci_patient:
                        self.mci_queue.task_done()
                    else:
                        self.er_queues[queue_idx].task_done()
                    continue

                # Check if patient needs tests before seeing doctor (50% chance)
                tests_needed = random() < 0.50

                if tests_needed:
                    # Needs blood work, x-ray, or both
                    needs_blood_work = choice([True, False])
                    needs_xray = choice([True, False])

                    if not needs_blood_work and not needs_xray:
                        needs_blood_work = True  # Ensure at least one test is needed

                    patient.needs_blood_work = needs_blood_work
                    patient.needs_xray = needs_xray

                    if needs_blood_work and needs_xray:
                        print(f"🔬 ({self.format_time()}) ER patient {patient.name} needs both blood work and X-ray")
                        patient.needs_xray = True  # Flag for blood work thread to send to X-ray after
                        self.blood_work_queue.put(patient)
                    elif needs_blood_work:
                        print(f"🔬 ({self.format_time()}) ER patient {patient.name} needs blood work")
                        self.blood_work_queue.put(patient)
                    elif needs_xray:
                        print(f"🔬 ({self.format_time()}) ER patient {patient.name} needs X-ray")
                        self.xray_queue.put(patient)

                    # Release the doctor while patient gets tests
                    try:
                        self.available_er_doctors.release()
                    except:
                        pass

                    # Mark task as done
                    if mci_patient:
                        self.mci_queue.task_done()
                    else:
                        self.er_queues[queue_idx].task_done()
                    continue

                # Simulate doctor examination time
                examination_time = uniform(5, 10)
                self.simulate_time(examination_time)

                print(f"👨‍⚕️ ({self.format_time()}) ER Doctor examined {patient.name}")

                # Check if surgery is needed
                # For MCI patients, higher chance of surgery
                if patient.is_mci_patient:
                    surgery_needed = random() < 0.50
                else:
                    surgery_needed = random() < 0.30

                if surgery_needed:
                    print(f"🔪 ({self.format_time()}) ER patient {patient.name} needs surgery")
                    self.surgery_queue.put(patient)
                else:
                    # No surgery needed, patient can be discharged
                    patient.doctor_end_time = time()
                    patient.discharge_time = time()

                    # For MCI patients, higher chance of death even without surgery
                    if patient.is_mci_patient and random() < 0.30:
                        patient.dead = True
                        print(f"💀 ({self.format_time()}) MCI patient {patient.name} died during treatment")
                    else:
                        print(f"🚶 ({self.format_time()}) ER patient {patient.name} discharged")

                    # Record visit statistics
                    self.stats.record_visit(self.current_day, patient)

                    # If patient was an MCI patient, also record those stats
                    if patient.is_mci_patient:
                        self.stats.record_mci_patient(patient)

                # Release the doctor
                try:
                    self.available_er_doctors.release()
                except:
                    pass

                # Mark task as done
                if mci_patient:
                    self.mci_queue.task_done()
                else:
                    self.er_queues[queue_idx].task_done()
            except Exception:
                # If there's an error, make sure to release the doctor
                try:
                    self.available_er_doctors.release()
                except:
                    pass
                continue

    def generate_regular_patients(self, day):
        """Generate regular patients throughout the day."""
        # Get interval between patient arrivals (scaled by simulation speed)
        interval = 5

        # Number of patients depends on MCI status
        num_patients = self.patients_per_day
        if self.is_mci_day and self.mci_in_progress:
            # Fewer regular patients during MCI (people avoid hospital during disasters)
            num_patients = int(self.patients_per_day * 0.5)

        for i in range(num_patients):
            if self.simulation_complete.is_set():
                break

            # Create a new patient
            patient = Patient(self.generate_patient_name(), time())

            # Send to reception
            self.reception_queue.put((day, patient))

            # Wait for next patient
            self.simulate_time(interval)

    def generate_ambulance_arrivals(self, day):
        """Generate ambulance arrivals throughout the day."""
        # Get interval between ambulance arrivals (scaled by simulation speed)
        interval = 15

        # Number of ambulances depends on MCI status
        num_ambulances = self.ambulances_per_day
        if self.is_mci_day and self.mci_in_progress:
            # More ambulances during MCI
            num_ambulances = int(self.ambulances_per_day * 2)

        for i in range(num_ambulances):
            if self.simulation_complete.is_set():
                break

            # Send ambulance to queue
            self.ambulance_queue.put((day, i))

            # Wait for next ambulance
            self.simulate_time(interval)

    def generate_mci_patients(self):
        """Generate a surge of patients during Mass Casualty Incident."""
        with self.mci_lock:
            self.mci_in_progress = True
            print(f"\n🚨 MASS CASUALTY INCIDENT DECLARED on Day {self.current_day + 1} 🚨")

            # Signal that regular doctors should help with MCI
            self.mci_assistance_needed.set()

            # Wait for some regular doctors to be available for help
            self.simulate_time(5)  # Give time for doctors to respond

            # Generate MCI patients (faster than normal for simulation speed)
            batch_size = 5  # Process in batches for speed
            for i in range(0, self.mci_patients, batch_size):
                if self.simulation_complete.is_set():
                    break

                # Create a batch of patients
                for j in range(min(batch_size, self.mci_patients - i)):
                    # Create a new patient with high severity
                    patient = Patient(self.generate_patient_name(), time())

                    # Assign as MCI patient with trauma condition
                    self.assign_condition_and_severity(patient, is_mci=True)

                    # Send directly to MCI queue
                    self.mci_queue.put(patient)

                # Brief interval between batches
                self.simulate_time(2)

            print(f"🚨 MCI patient surge complete. Total: {self.mci_patients} patients")

            # Wait for most MCI queue to be processed (with timeout to prevent hanging)
            start_time = time()
            timeout = 10  # Seconds to wait for MCI queue processing

            while not self.mci_queue.empty() and time() - start_time < timeout:
                self.simulate_time(1)

            # Force completion even if not all patients were processed
            while not self.mci_queue.empty():
                try:
                    patient = self.mci_queue.get_nowait()
                    # Mark as dead for statistics
                    patient.dead = True
                    self.stats.record_visit(self.current_day, patient)
                    self.stats.record_mci_patient(patient)
                    self.mci_queue.task_done()
                except:
                    break

            # MCI is over
            print(f"🚨 Mass Casualty Incident has been resolved on Day {self.current_day + 1}.")
            self.mci_in_progress = False
            self.mci_assistance_needed.clear()

    def format_time(self):
        """Format the current simulation time as Day/Hour:Minute."""
        day = self.current_day + 1
        seconds_in_day = self.current_time % (24 * 60 * 60)
        hours = int(seconds_in_day / 3600)
        minutes = int((seconds_in_day % 3600) / 60)
        return f"Day {day} {hours:02d}:{minutes:02d}"

    def simulate_day(self, day):
        """Simulate a full day in the hospital."""
        self.current_day = day
        self.current_time = day * 24 * 60 * 60  # Day start time in seconds

        # Check if this is the MCI day
        self.is_mci_day = (day == self.stats.mci_day)
        self.mci_in_progress = False

        print(f"\n🏥 === Day {day + 1} Starting === 🏥")
        if self.is_mci_day:
            print(f"⚠️ This is the Mass Casualty Incident day!")

        # Start threads for the day
        threads = []

        # Start receptionist threads
        for i in range(self.receptionists):
            thread = Thread(target=self.receptionist_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Start nurse assessment threads
        for i in range(self.receptionists):
            thread = Thread(target=self.nurse_assessment_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Start blood work and X-ray threads
        for i in range(3):
            thread = Thread(target=self.blood_work_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        for i in range(2):
            thread = Thread(target=self.xray_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Start surgery threads
        for i in range(5):
            thread = Thread(target=self.surgery_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Start code blue thread
        code_blue_thread = Thread(target=self.code_blue_thread)
        code_blue_thread.daemon = True
        code_blue_thread.start()
        threads.append(code_blue_thread)

        # Start ambulance thread
        ambulance_thread = Thread(target=self.ambulance_thread)
        ambulance_thread.daemon = True
        ambulance_thread.start()
        threads.append(ambulance_thread)

        # Start MCI assistant threads for each department
        if self.is_mci_day:
            for dept in self.departments:
                thread = Thread(target=self.mci_assistant_thread, args=(dept,))
                thread.daemon = True
                thread.start()
                threads.append(thread)

        # Start regular doctor threads for each department
        for dept in self.departments:
            for i in range(self.doctors_per_department):
                thread = Thread(target=self.regular_doctor_thread, args=(dept,))
                thread.daemon = True
                thread.start()
                threads.append(thread)

        # Start ER doctor threads
        for i in range(self.er_doctors):
            thread = Thread(target=self.er_doctor_thread, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Start patient and ambulance generation
        patient_thread = Thread(target=self.generate_regular_patients, args=(day,))
        patient_thread.daemon = True
        patient_thread.start()

        ambulance_gen_thread = Thread(target=self.generate_ambulance_arrivals, args=(day,))
        ambulance_gen_thread.daemon = True
        ambulance_gen_thread.start()

        # Start MCI if this is the MCI day (after a delay)
        if self.is_mci_day:
            # MCI starts after a short delay
            self.simulate_time(20)  # Very short delay for fast simulation

            # Generate MCI patients
            mci_thread = Thread(target=self.generate_mci_patients)
            mci_thread.daemon = True
            mci_thread.start()

            # Wait for MCI thread but with timeout to prevent hanging
            mci_thread.join(timeout=10)

        # Short wait for patient generation
        try:
            patient_thread.join(timeout=5)
            ambulance_gen_thread.join(timeout=5)
        except:
            pass

        # Wait for all queues to be empty or timeout
        all_queues = [
            self.reception_queue,
            self.assessment_queue,
            self.blood_work_queue,
            self.xray_queue,
            self.surgery_queue,
            self.ambulance_queue,
            self.code_blue_queue,
            self.mci_queue
        ]
        all_queues.extend(self.department_queues.values())
        all_queues.extend(self.er_queues)

        # Wait until all queues are empty (with timeout)
        max_wait_time = 30
        start_wait_time = time()

        while any(not q.empty() for q in all_queues):
            self.simulate_time(1)  # Check every 1 simulated seconds

            # Add a timeout mechanism to prevent infinite waiting
            if time() - start_wait_time > max_wait_time:
                print(f"⚠️ Timeout reached for day {day + 1}, forcing day completion")
                # Force-empty any remaining queues
                for q in all_queues:
                    try:
                        while not q.empty():
                            q.get_nowait()
                            q.task_done()
                    except:
                        pass
                break

        print(f"\n✅ Day {day + 1} complete!")

    def run_simulation(self):
        """Run the full hospital simulation for multiple days."""
        print("🏥 Multi-Day Hospital Simulation Started 🏥")

        # Set a timeout for the entire simulation
        simulation_start = time()
        timeout = 300

        for day in range(self.days):
            # Check for timeout
            if time() - simulation_start > timeout:
                print("⚠️ Simulation timeout reached, generating final statistics...")
                break

            # Run simulation for this day
            self.simulate_day(day)

            # Add a small delay between days to ensure proper completion
            sleep(1)

        # Signal simulation completion
        self.simulation_complete.set()

        # Give threads more time to terminate
        sleep(2)

        # Visualize the data
        self.stats.visualize_data()

        print("\n🏥 Hospital Simulation Complete 🏥")