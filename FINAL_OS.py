import time
import random
import queue
import threading
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

class Patient:
    def __init__(self, name, arrival_time):
        self.name = name
        self.arrival_time = arrival_time
        self.severity = None
        self.condition = None
        self.department = None
        self.registration_time = None
        self.assessment_time = None
        self.doctor_start_time = None
        self.doctor_end_time = None
        self.discharge_time = None
        self.dead = False
        self.had_surgery = False
        self.surgery_success = None
        self.had_blood_work = False
        self.had_xray = False
        self.had_code_blue = False
        self.code_blue_success = None
        self.came_by_ambulance = False
        self.waiting_time = 0
        self.is_mci_patient = False
        
    def __lt__(self, other):
        # For ER priority queue - higher severity patients come first
        if hasattr(self, 'severity') and hasattr(other, 'severity'):
            if self.severity != other.severity:
                return self.severity > other.severity
        return self.arrival_time < other.arrival_time
    
    def __str__(self):
        status = "DEAD" if self.dead else "alive"
        severity_str = f"severity {self.severity}" if self.severity is not None else "unassessed"
        return f"{self.name} ({self.condition}, {severity_str}, {status})"

class Statistics:
    def __init__(self):
        self.days = 7
        self.total_visits_per_day = [0] * self.days
        self.waiting_times_per_day = [[] for _ in range(self.days)]
        self.ambulance_arrivals_per_day = [0] * self.days
        self.deaths_per_day = [0] * self.days
        self.conditions_per_day = [defaultdict(int) for _ in range(self.days)]
        self.surgeries_per_day = [0] * self.days
        self.surgery_success_per_day = [0] * self.days
        self.er_patients_per_day = [0] * self.days
        self.xrays_per_day = [0] * self.days
        self.blood_works_per_day = [0] * self.days
        self.code_blues_per_day = [0] * self.days
        self.code_blue_success_per_day = [0] * self.days
        self.survivals_per_day = [0] * self.days
        self.patients_per_department = [defaultdict(int) for _ in range(self.days)]
        
        # MCI day stats
        self.mci_day = random.randint(0, 6)  # Random day for MCI
        self.mci_deaths = 0
        self.mci_survivals = 0
        self.mci_patients = 0
        self.mci_waiting_times = []
        
        self.lock = threading.Lock()
    
    def record_visit(self, day, patient):
        with self.lock:
            if day >= len(self.total_visits_per_day):
                return  # Ignore out-of-range days
                
            self.total_visits_per_day[day] += 1
            if patient.condition:
                self.conditions_per_day[day][patient.condition] += 1
            
            if patient.severity is not None and patient.severity >= 8:
                self.er_patients_per_day[day] += 1
            
            if patient.department:
                self.patients_per_department[day][patient.department] += 1
            
            if patient.had_surgery:
                self.surgeries_per_day[day] += 1
                if patient.surgery_success:
                    self.surgery_success_per_day[day] += 1
            
            if patient.had_blood_work:
                self.blood_works_per_day[day] += 1
            
            if patient.had_xray:
                self.xrays_per_day[day] += 1
            
            if patient.had_code_blue:
                self.code_blues_per_day[day] += 1
                if patient.code_blue_success:
                    self.code_blue_success_per_day[day] += 1
            
            if patient.came_by_ambulance:
                self.ambulance_arrivals_per_day[day] += 1
            
            if patient.dead:
                self.deaths_per_day[day] += 1
            else:
                self.survivals_per_day[day] += 1
            
            # Record waiting time (time from arrival to doctor start)
            if patient.doctor_start_time and patient.arrival_time:
                wait_time = (patient.doctor_start_time - patient.arrival_time) * 1800 / 60
                self.waiting_times_per_day[day].append(wait_time)
                
                # Check if this happened during MCI
                if day == self.mci_day and patient.is_mci_patient:
                    self.mci_waiting_times.append(wait_time)
    
    def record_mci_patient(self, patient):
        with self.lock:
            self.mci_patients += 1
            if patient.dead:
                self.mci_deaths += 1
            else:
                self.mci_survivals += 1
    
    def visualize_data(self):
        print("\n📊 Hospital Simulation Statistics 📊")
        
        # Calculate average waiting times
        avg_waiting_times = []
        for day_waiting_times in self.waiting_times_per_day:
            if day_waiting_times:
                avg_waiting_times.append(int(sum(day_waiting_times) / len(day_waiting_times)))
            else:
                avg_waiting_times.append(0)
        
        # Create figure with multiple subplots
        fig, axs = plt.subplots(4, 3, figsize=(16, 14))
        fig.suptitle('Hospital Simulation: 7-Day Statistics', fontsize=16)
        
        # Total visits per day
        axs[0, 0].bar(range(1, 8), self.total_visits_per_day)
        axs[0, 0].set_title('Total Visits per Day')
        axs[0, 0].set_xlabel('Day')
        axs[0, 0].set_ylabel('Number of Visits')
        
        # Average waiting time
        axs[0, 1].bar(range(1, 8), avg_waiting_times)
        axs[0, 1].set_title('Average Waiting Time per Day')
        axs[0, 1].set_xlabel('Day')
        axs[0, 1].set_ylabel('Time (minutes)')
        # Set y-axis to show specific ticks: 0, 10, 20, etc.
        max_wait = max(avg_waiting_times)
        y_ticks = list(range(0, max_wait + 20, 10))  # Create ticks from 0 to max+20 in steps of 10
        axs[0, 1].set_yticks(y_ticks)
        axs[0, 1].set_ylim(bottom=0)  # Start from 0
        
        # Ambulance arrivals
        axs[0, 2].bar(range(1, 8), self.ambulance_arrivals_per_day)
        axs[0, 2].set_title('Ambulance Arrivals per Day')
        axs[0, 2].set_xlabel('Day')
        axs[0, 2].set_ylabel('Number of Ambulances')
        
        # Deaths per day
        axs[1, 0].bar(range(1, 8), self.deaths_per_day)
        axs[1, 0].set_title('Deaths per Day')
        axs[1, 0].set_xlabel('Day')
        axs[1, 0].set_ylabel('Number of Deaths')
        
        # Number of surgeries and outcomes
        axs[1, 1].bar(range(1, 8), self.surgeries_per_day, label='Total Surgeries')
        axs[1, 1].bar(range(1, 8), self.surgery_success_per_day, label='Successful')
        axs[1, 1].set_title('Surgeries per Day and Outcomes')
        axs[1, 1].set_xlabel('Day')
        axs[1, 1].set_ylabel('Number of Surgeries')
        axs[1, 1].legend()
        
        # Number of ER patients
        axs[1, 2].bar(range(1, 8), self.er_patients_per_day)
        axs[1, 2].set_title('ER Patients per Day')
        axs[1, 2].set_xlabel('Day')
        axs[1, 2].set_ylabel('Number of Patients')
        
        # Number of X-rays and blood works
        axs[2, 0].bar(range(1, 8), self.xrays_per_day, label='X-rays')
        axs[2, 0].bar(range(1, 8), self.blood_works_per_day, bottom=self.xrays_per_day, label='Blood Works')
        axs[2, 0].set_title('X-rays and Blood Works per Day')
        axs[2, 0].set_xlabel('Day')
        axs[2, 0].set_ylabel('Number of Tests')
        axs[2, 0].legend()
        
        # Number of code blues and outcomes
        axs[2, 1].bar(range(1, 8), self.code_blues_per_day, label='Total Code Blues')
        axs[2, 1].bar(range(1, 8), self.code_blue_success_per_day, label='Successful')
        axs[2, 1].set_title('Code Blues per Day and Outcomes')
        axs[2, 1].set_xlabel('Day')
        axs[2, 1].set_ylabel('Number of Code Blues')
        axs[2, 1].legend()
        
        # Survivals per day
        axs[2, 2].bar(range(1, 8), self.survivals_per_day)
        axs[2, 2].set_title('Survivals per Day')
        axs[2, 2].set_xlabel('Day')
        axs[2, 2].set_ylabel('Number of Survivals')
        
        # Plot conditions for Day 1 as an example
        day_to_show = 0
        conditions = list(self.conditions_per_day[day_to_show].keys())
        condition_counts = [self.conditions_per_day[day_to_show][c] for c in conditions]
        axs[3, 0].bar(conditions, condition_counts)
        axs[3, 0].set_title(f'Conditions on Day 1')
        axs[3, 0].set_xlabel('Condition')
        axs[3, 0].set_ylabel('Number of Patients')
        axs[3, 0].tick_params(axis='x', rotation=45)
        
        # Plot departments for Day 1 as an example
        departments = list(self.patients_per_department[day_to_show].keys())
        department_counts = [self.patients_per_department[day_to_show][d] for d in departments]
        axs[3, 1].bar(departments, department_counts)
        axs[3, 1].set_title(f'Departments on Day 1')
        axs[3, 1].set_xlabel('Department')
        axs[3, 1].set_ylabel('Number of Patients')
        axs[3, 1].tick_params(axis='x', rotation=45)
        
        # MCI day statistics
        mci_labels = ['Patients', 'Survivals', 'Deaths']
        mci_values = [self.mci_patients, self.mci_survivals, self.mci_deaths]
        axs[3, 2].bar(mci_labels, mci_values)
        axs[3, 2].set_title(f'MCI Day (Day {self.mci_day + 1}) Statistics')
        axs[3, 2].set_xlabel('Category')
        axs[3, 2].set_ylabel('Count')
        
        plt.tight_layout()
        plt.savefig('hospital_statistics.png')
        print(f"Statistics visualization saved as 'hospital_statistics.png'")
        
        # Print textual summary
        print("\n=== 7-Day Hospital Simulation Summary ===")
        total_patients = sum(self.total_visits_per_day)
        total_deaths = sum(self.deaths_per_day)
        death_rate = (total_deaths / total_patients) * 100 if total_patients > 0 else 0
        
        print(f"Total Patients: {total_patients}")
        print(f"Total Deaths: {total_deaths} ({death_rate:.2f}%)")
        print(f"Total Surgeries: {sum(self.surgeries_per_day)}")
        print(f"Successful Surgeries: {sum(self.surgery_success_per_day)}")
        print(f"Total Code Blues: {sum(self.code_blues_per_day)}")
        print(f"Successful Code Blues: {sum(self.code_blue_success_per_day)}")
        
        # Average waiting time overall
        all_waiting_times = [time for day_times in self.waiting_times_per_day for time in day_times]
        if all_waiting_times:
            avg_wait = sum(all_waiting_times) / len(all_waiting_times)
            print(f"Average Waiting Time: {int(avg_wait)} minutes")
        
        # MCI day statistics
        print(f"\n=== Mass Casualty Incident (Day {self.mci_day + 1}) ===")
        print(f"Total MCI Patients: {self.mci_patients}")
        print(f"MCI Survivals: {self.mci_survivals}")
        print(f"MCI Deaths: {self.mci_deaths}")
        
        if self.mci_waiting_times:
            avg_mci_wait = sum(self.mci_waiting_times) / len(self.mci_waiting_times)
            print(f"Average Waiting Time during MCI: {int(avg_mci_wait)} minutes")


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
        self.lock = threading.Lock()
        self.mci_lock = threading.Lock()
        
        # Event to signal simulation completion
        self.simulation_complete = threading.Event()
        
        # Current simulation time
        self.current_time = 0
        
        # Special events tracking
        self.code_blue_in_progress = False
        self.code_blue_lock = threading.Lock()
        
        # Available staff tracking
        self.available_er_doctors = threading.Semaphore(self.er_doctors)
        self.available_er_nurses = threading.Semaphore(self.er_doctors * self.nurses_per_doctor)
        self.available_regular_doctors = {dept: threading.Semaphore(self.doctors_per_department) for dept in self.departments}
        self.available_regular_nurses = {dept: threading.Semaphore(self.doctors_per_department * self.nurses_per_doctor) for dept in self.departments}
        self.available_receptionists = threading.Semaphore(self.receptionists)
        
        # Regular doctor pool for MCI assistance
        self.regular_doctors_helping_mci = threading.Semaphore(0)  # Initially no regular doctors helping
        self.mci_assistance_needed = threading.Event()  # Signal for regular doctors to help
        
    def initialize_queues_and_resources(self):
        # Reception queue
        self.reception_queue = queue.Queue()
        
        # Nurse assessment queues
        self.assessment_queue = queue.Queue()
        
        # Department doctor queues (FIFO)
        self.department_queues = {dept: queue.Queue() for dept in self.departments}
        
        # ER doctor queues (priority)
        self.er_queues = [queue.PriorityQueue() for _ in range(self.er_doctors)]
        
        # Testing queues
        self.blood_work_queue = queue.Queue()
        self.xray_queue = queue.Queue()
        
        # Surgery queues
        self.surgery_queue = queue.Queue()
        
        # Ambulance queue
        self.ambulance_queue = queue.Queue()
        
        # Code blue queue
        self.code_blue_queue = queue.Queue()
        
        # MCI queue - for handling mass casualty incidents
        self.mci_queue = queue.PriorityQueue()
        
    def simulate_time(self, seconds):
        """Simulate the passage of time adjusted by simulation speed."""
        scaled_time = seconds / self.simulation_speed
        
        # Add a minimum time cap to avoid excessive sleeping
        scaled_time = min(scaled_time, 0.5)  
        
        if scaled_time > 0:
            time.sleep(scaled_time)
            
        # Always advance the simulation clock by the actual seconds
        self.current_time += seconds
        return seconds
    
    def generate_patient_name(self):
        """Generate a random patient name."""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
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
            patient.condition = random.choice(trauma_conditions)
            patient.severity = random.randint(8, 10)  # High severity for MCI patients
            patient.is_mci_patient = True
        else:
            # Regular patient gets random condition
            patient.condition = random.choice(all_conditions)
            
            # Assign severity (1-10 scale, with 10 being most severe)
            if self.is_mci_day and not self.mci_in_progress:
                # During MCI day but not MCI event, normal distribution of severity
                patient.severity = random.randint(1, 10)
            elif self.is_mci_day and self.mci_in_progress:
                # During MCI event, non-MCI patients less likely to have high severity
                patient.severity = random.randint(1, 8)
            else:
                # Normal day
                patient.severity = random.randint(1, 10)
        
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
                registration_time = random.uniform(3, 6)
                self.simulate_time(registration_time)
                
                # Update patient record
                patient.registration_time = time.time()
                
                # Display registration message
                print(f"📋 ({self.format_time()}) Patient {patient.name} registered")
                
                # Send to nurse assessment
                self.assessment_queue.put(patient)
                
                # Release the receptionist
                self.available_receptionists.release()
                
                # Mark task as complete
                self.reception_queue.task_done()
            except queue.Empty:
                continue
    
    def nurse_assessment_thread(self):
        """Handle nurse assessment of patients."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.assessment_queue.get(timeout=0.5)
                
                # Simulate assessment time 
                assessment_time = random.uniform(30, 60)
                self.simulate_time(assessment_time)
                
                # Assign condition and severity if not already set (ambulance patients already have them)
                if patient.condition is None:
                    self.assign_condition_and_severity(patient)
                
                # Update patient record
                patient.assessment_time = time.time()
                
                # Display assessment message
                print(f"🩺 ({self.format_time()}) Nurse assessed {patient.name}: {patient.condition}, severity {patient.severity}")
                
                # Route patient based on severity
                if patient.severity >= 8:
                    # ER patient - send to a random ER doctor queue
                    er_queue_idx = random.randint(0, self.er_doctors - 1)
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
            except queue.Empty:
                continue
    
    def blood_work_thread(self):
        """Handle blood work tests."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.blood_work_queue.get(timeout=0.5)
                
                # Simulate blood work time
                blood_work_time = random.uniform(5, 10)
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
                        er_queue_idx = random.randint(0, self.er_doctors - 1)
                        self.er_queues[er_queue_idx].put(patient)
                    else:
                        # Send back to department
                        self.department_queues[patient.department].put(patient)
                
                # Mark task as complete
                self.blood_work_queue.task_done()
            except queue.Empty:
                continue
    
    def xray_thread(self):
        """Handle X-ray tests."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.xray_queue.get(timeout=0.5)
                
                # Simulate X-ray time
                xray_time = random.uniform(5, 10)
                self.simulate_time(xray_time)
                
                # Update patient record
                patient.had_xray = True
                
                # Display X-ray message
                print(f"📷 ({self.format_time()}) X-ray completed for {patient.name}")
                
                # Continue to doctor
                if patient.severity >= 8:
                    # Send back to ER
                    er_queue_idx = random.randint(0, self.er_doctors - 1)
                    self.er_queues[er_queue_idx].put(patient)
                else:
                    # Send back to department
                    self.department_queues[patient.department].put(patient)
                
                # Mark task as complete
                self.xray_queue.task_done()
            except queue.Empty:
                continue
    
    def surgery_thread(self):
        """Handle surgeries."""
        while not self.simulation_complete.is_set():
            try:
                # Try to get a patient from the queue
                patient = self.surgery_queue.get(timeout=0.5)
                
                # Simulate surgery time
                surgery_time = random.uniform(10, 15)
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
                
                if random.random() < death_chance:
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
                    patient.discharge_time = time.time()
                    print(f"🚶 ({self.format_time()}) {patient.name} discharged after surgery.")
                
                # Record statistics for the current day
                self.stats.record_visit(self.current_day, patient)
                
                # If patient was an MCI patient, also record those stats
                if patient.is_mci_patient:
                    self.stats.record_mci_patient(patient)
                
                # Mark task as complete
                self.surgery_queue.task_done()
            except queue.Empty:
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
                    if random.random() < 0.20:  # 20% survival rate 
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
                    er_queue_idx = random.randint(0, self.er_doctors - 1)
                    self.er_queues[er_queue_idx].put(patient)
                else:
                    # Record statistics for the dead patient
                    self.stats.record_visit(self.current_day, patient)
                    
                    # If patient was an MCI patient, also record those stats
                    if patient.is_mci_patient:
                        self.stats.record_mci_patient(patient)
                
                # Mark task as complete
                self.code_blue_queue.task_done()
            except queue.Empty:
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
                patient = Patient(self.generate_patient_name(), time.time())
                patient.came_by_ambulance = True
                
                # Try to acquire an ER doctor and nurse
                doctor_acquired = self.available_er_doctors.acquire(timeout=1)
                nurse_acquired = self.available_er_nurses.acquire(timeout=1)
                
                # Simulate ambulance handling time
                self.simulate_time(random.uniform(3, 6))
                
                # Assign condition and severity
                self.assign_condition_and_severity(patient)
                
                # Force severity to be high for ambulance patients
                if patient.severity < 7:
                    patient.severity = random.randint(7, 10)
                
                print(f"🚑 ({self.format_time()}) Ambulance arrived with {patient.name}: {patient.condition}, severity {patient.severity}")
                
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
                er_queue_idx = random.randint(0, self.er_doctors - 1)
                self.er_queues[er_queue_idx].put(patient)
                
                # Mark ambulance task as complete
                self.ambulance_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                # Continue even if there's an error
                continue
    
    def mci_assistant_thread(self, department):
        """Thread for regular department doctors helping during MCI."""
        while not self.simulation_complete.is_set():
            # Wait for signal that MCI assistance is needed
            if not self.mci_assistance_needed.is_set():
                time.sleep(0.1)
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
                        patient.doctor_start_time = time.time()
                        
                        # Calculate waiting time
                        patient.waiting_time = patient.doctor_start_time - patient.arrival_time
                        
                        # Simulate doctor examination time
                        examination_time = random.uniform(5, 10)
                        self.simulate_time(examination_time)
                        
                        print(f"👨‍⚕️ ({self.format_time()}) Doctor from {department} examined MCI patient {patient.name}")
                        
                        # Higher chance for surgery for MCI patients
                        surgery_needed = random.random() < 0.50  # 50% chance for surgery
                        
                        if surgery_needed:
                            print(f"🔪 ({self.format_time()}) MCI patient {patient.name} needs surgery")
                            self.surgery_queue.put(patient)
                        else:
                            # No surgery needed
                            patient.doctor_end_time = time.time()
                            
                            # Determine if patient survives (higher death chance during MCI)
                            if random.random() < 0.30:  # 30% chance of death without surgery 
                                patient.dead = True
                                print(f"💀 ({self.format_time()}) MCI patient {patient.name} died during treatment")
                            else:
                                patient.discharge_time = time.time()
                                print(f"🚶 ({self.format_time()}) MCI patient {patient.name} discharged after treatment")
                            
                            # Record visit statistics
                            self.stats.record_visit(self.current_day, patient)
                            self.stats.record_mci_patient(patient)
                        
                        # Mark task as done
                        self.mci_queue.task_done()
                    except queue.Empty:
                        # No MCI patients right now, wait a bit
                        time.sleep(0.1)
                
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
                    if random.random() < 0.30:
                        # Release the doctor slot to be handled by mci_assistant_thread
                        try:
                            self.available_regular_doctors[department].release()
                        except:
                            pass
                        time.sleep(0.1)  # Wait a bit before trying again
                        continue
                
                # Try to get a patient from the department queue
                try:
                    patient = self.department_queues[department].get(timeout=0.5)
                except queue.Empty:
                    # If no patients, release the doctor
                    try:
                        self.available_regular_doctors[department].release()
                    except:
                        pass
                    continue
                
                # Mark the time doctor starts seeing patient
                patient.doctor_start_time = time.time()
                
                # Calculate waiting time
                patient.waiting_time = patient.doctor_start_time - patient.arrival_time
                
                # Simulate doctor examination time 
                examination_time = random.uniform(20, 40)
                self.simulate_time(examination_time)
                
                print(f"👨‍⚕️ ({self.format_time()}) Doctor in {department} examined {patient.name}")
                
                # Check if surgery is needed 
                surgery_needed = random.random() < 0.30
                
                if surgery_needed:
                    print(f"🔪 ({self.format_time()}) {patient.name} needs surgery")
                    self.surgery_queue.put(patient)
                else:
                    # No surgery needed, patient can be discharged
                    patient.doctor_end_time = time.time()
                    patient.discharge_time = time.time()
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
                    except queue.Empty:
                        pass
                
                if mci_patient:
                    # We got an MCI patient, treat them
                    patient = mci_patient
                else:
                    # No MCI patient, get next from regular ER queue
                    try:
                        patient = self.er_queues[queue_idx].get(timeout=0.5)
                    except queue.Empty:
                        # No patients in queue, release doctor and continue
                        try:
                            self.available_er_doctors.release()
                        except:
                            pass
                        continue
                
                # Mark the time doctor starts seeing patient
                patient.doctor_start_time = time.time()
                
                # Calculate waiting time
                patient.waiting_time = patient.doctor_start_time - patient.arrival_time
                
                # Check for Code Blue event 
                code_blue = random.random() < 0.15
                
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
                tests_needed = random.random() < 0.50
                
                if tests_needed:
                    # Needs blood work, x-ray, or both
                    needs_blood_work = random.choice([True, False])
                    needs_xray = random.choice([True, False])
                    
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
                examination_time = random.uniform(5, 10)
                self.simulate_time(examination_time)
                
                print(f"👨‍⚕️ ({self.format_time()}) ER Doctor examined {patient.name}")
                
                # Check if surgery is needed
                # For MCI patients, higher chance of surgery
                if patient.is_mci_patient:
                    surgery_needed = random.random() < 0.50  
                else:
                    surgery_needed = random.random() < 0.30  
                
                if surgery_needed:
                    print(f"🔪 ({self.format_time()}) ER patient {patient.name} needs surgery")
                    self.surgery_queue.put(patient)
                else:
                    # No surgery needed, patient can be discharged
                    patient.doctor_end_time = time.time()
                    patient.discharge_time = time.time()
                    
                    # For MCI patients, higher chance of death even without surgery
                    if patient.is_mci_patient and random.random() < 0.30:  
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
            patient = Patient(self.generate_patient_name(), time.time())
            
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
                    patient = Patient(self.generate_patient_name(), time.time())
                    
                    # Assign as MCI patient with trauma condition
                    self.assign_condition_and_severity(patient, is_mci=True)
                    
                    # Send directly to MCI queue
                    self.mci_queue.put(patient)
                
                # Brief interval between batches
                self.simulate_time(2)
            
            print(f"🚨 MCI patient surge complete. Total: {self.mci_patients} patients")
            
            # Wait for most MCI queue to be processed (with timeout to prevent hanging)
            start_time = time.time()
            timeout = 10  # Seconds to wait for MCI queue processing
            
            while not self.mci_queue.empty() and time.time() - start_time < timeout:
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
            thread = threading.Thread(target=self.receptionist_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start nurse assessment threads
        for i in range(self.receptionists):
            thread = threading.Thread(target=self.nurse_assessment_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start blood work and X-ray threads
        for i in range(3):
            thread = threading.Thread(target=self.blood_work_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        for i in range(2):
            thread = threading.Thread(target=self.xray_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start surgery threads
        for i in range(5):
            thread = threading.Thread(target=self.surgery_thread)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start code blue thread
        code_blue_thread = threading.Thread(target=self.code_blue_thread)
        code_blue_thread.daemon = True
        code_blue_thread.start()
        threads.append(code_blue_thread)
        
        # Start ambulance thread
        ambulance_thread = threading.Thread(target=self.ambulance_thread)
        ambulance_thread.daemon = True
        ambulance_thread.start()
        threads.append(ambulance_thread)
        
        # Start MCI assistant threads for each department
        if self.is_mci_day:
            for dept in self.departments:
                thread = threading.Thread(target=self.mci_assistant_thread, args=(dept,))
                thread.daemon = True
                thread.start()
                threads.append(thread)
        
        # Start regular doctor threads for each department
        for dept in self.departments:
            for i in range(self.doctors_per_department):
                thread = threading.Thread(target=self.regular_doctor_thread, args=(dept,))
                thread.daemon = True
                thread.start()
                threads.append(thread)
        
        # Start ER doctor threads
        for i in range(self.er_doctors):
            thread = threading.Thread(target=self.er_doctor_thread, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start patient and ambulance generation
        patient_thread = threading.Thread(target=self.generate_regular_patients, args=(day,))
        patient_thread.daemon = True
        patient_thread.start()
        
        ambulance_gen_thread = threading.Thread(target=self.generate_ambulance_arrivals, args=(day,))
        ambulance_gen_thread.daemon = True
        ambulance_gen_thread.start()
        
        # Start MCI if this is the MCI day (after a delay)
        if self.is_mci_day:
            # MCI starts after a short delay
            self.simulate_time(20)  # Very short delay for fast simulation
            
            # Generate MCI patients
            mci_thread = threading.Thread(target=self.generate_mci_patients)
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
        start_wait_time = time.time()
        
        while any(not q.empty() for q in all_queues):
            self.simulate_time(1)  # Check every 1 simulated seconds
            
            # Add a timeout mechanism to prevent infinite waiting
            if time.time() - start_wait_time > max_wait_time:
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
        simulation_start = time.time()
        timeout = 300  
        
        for day in range(self.days):
            # Check for timeout
            if time.time() - simulation_start > timeout:
                print("⚠️ Simulation timeout reached, generating final statistics...")
                break
                
            # Run simulation for this day
            self.simulate_day(day)
            
            # Add a small delay between days to ensure proper completion
            time.sleep(1)
        
        # Signal simulation completion
        self.simulation_complete.set()
        
        # Give threads more time to terminate
        time.sleep(2)  
        
        # Visualize the data
        self.stats.visualize_data()
        
        print("\n🏥 Hospital Simulation Complete 🏥")

def main():
    # Create simulation with configurable parameters
    simulation = HospitalSimulation(
        days=7,                   # Simulate for 7 days
        simulation_speed=100.0    
    )
    
    # Reduce the number of patients to speed up simulation but still see plenty of events
    simulation.patients_per_day = 100   
    simulation.ambulances_per_day = 50  
    simulation.mci_patients = 150        
    
    # Run the simulation
    simulation.run_simulation()

if __name__ == "__main__":
    main()