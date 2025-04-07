import time
import random
import threading
from collections import deque
from enum import Enum
from queue import PriorityQueue
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import queue
import numpy as np


class Specialty(Enum):
    CARDIOLOGY = "Cardiology"
    NEUROLOGY = "Neurology"
    PEDIATRICS = "Pediatrics"
    ORTHOPEDICS = "Orthopedics"
    GENERAL = "General Medicine"
    SURGERY = "Surgery"
    DIAGNOSTICS = "Diagnostics"

    @classmethod
    def get_specialty_for_disease(cls, disease: str) -> 'Specialty':
        specialty_mapping = {
            "Hypertension": cls.CARDIOLOGY,
            "Acute Myocardial Infarction": cls.CARDIOLOGY,
            "Heart Failure": cls.CARDIOLOGY,
            "Cardiac Arrhythmia": cls.CARDIOLOGY,
            "Cerebral Hemorrhage": cls.NEUROLOGY,
            "Migraine": cls.NEUROLOGY,
            "Epilepsy": cls.NEUROLOGY,
            "Multiple Sclerosis": cls.NEUROLOGY,
            "Multiple Organ Failure": cls.GENERAL,
            "Common Cold": cls.GENERAL,
            "Influenza": cls.GENERAL,
            "Pneumonia": cls.GENERAL,
            "Bronchitis": cls.GENERAL,
            "Sepsis": cls.GENERAL,
            "Gastritis": cls.GENERAL,
            "Diabetes": cls.GENERAL,
            "Food Poisoning": cls.GENERAL,
            "Arthritis": cls.ORTHOPEDICS,
            "Severe Trauma": cls.ORTHOPEDICS,
            "Spinal Disc Herniation": cls.ORTHOPEDICS,
            "Bone Fracture": cls.ORTHOPEDICS,
        }
        return specialty_mapping.get(disease, cls.GENERAL)


class Patient:
    patient_counter = 1
    severity_levels = {
        "Common Cold": (1, 3),
        "Influenza": (2, 5),
        "Hypertension": (3, 7),
        "Diabetes": (4, 8),
        "Asthma": (3, 7),
        "Migraine": (2, 6),
        "Arthritis": (3, 6),
        "Pneumonia": (5, 9),
        "Gastritis": (2, 5),
        "Bronchitis": (3, 6),
        "Sepsis": (8, 10),
        "Acute Myocardial Infarction": (8, 10),
        "Cerebral Hemorrhage": (9, 10),
        "Multiple Organ Failure": (9, 10),
        "Severe Trauma": (8, 10),
        "Heart Failure": (7, 9),
        "Cardiac Arrhythmia": (6, 8),
        "Epilepsy": (5, 8),
        "Multiple Sclerosis": (6, 9),
        "Food Poisoning": (3, 6),
        "Spinal Disc Herniation": (5, 8),
        "Bone Fracture": (4, 7),
    }

    def __init__(self, age: int):
        self.patient_id = None  # Will be set by receptionist
        self.age = age
        self.disease = None
        self.severity = None
        self.arrival_time = time.time()

    @classmethod
    def create_emergency(cls, age: int, source: str):
        """Create patient for ambulance or MCI without going through reception"""
        patient = cls(age)
        patient.patient_id = f"{source}-{int(time.time())}"  # Use timestamp for emergency cases
        return patient

    def __lt__(self, other):
        """Implement less than comparison for priority queue"""
        if not isinstance(other, Patient):
            return NotImplemented
        # Compare by severity first, then by arrival time
        if self.severity == other.severity:
            return self.arrival_time < other.arrival_time
        return self.severity < other.severity

    def assign_random_disease(self):
        diseases = list(self.severity_levels.keys())
        # Increase probability of severe conditions
        severe_diseases = ["Sepsis", "Acute Myocardial Infarction", "Cerebral Hemorrhage", 
                         "Multiple Organ Failure", "Severe Trauma"]
        if random.random() < 0.4:  # 40% chance of severe disease
            self.disease = random.choice(severe_diseases)
        else:
            self.disease = random.choice(diseases)
        
        min_severity, max_severity = self.severity_levels[self.disease]
        # Bias towards higher severity within the range
        self.severity = random.randint(min_severity, max_severity)
        if random.random() < 0.3:  # 30% chance of maximum severity
            self.severity = max_severity


class Receptionist:
    def __init__(self, receptionist_id):
        self.receptionist_id = f"R{receptionist_id}"
        self.patient_counter = 1
        self.hospital = None  # Add reference to hospital

    def register_patient(self, age: int):
        print(f"Receptionist {self.receptionist_id} registering patient...")
        time.sleep(0.5)
        patient = Patient(age)
        patient.patient_id = f"{self.receptionist_id}-{self.patient_counter:04d}"
        self.patient_counter += 1
        
        # Update statistics
        if self.hospital and self.hospital.stats:
            with self.hospital.stats_lock:
                self.hospital.stats.add_receptionist_patient(self.receptionist_id)
        
        return patient


class Nurse:
    def __init__(self, nurse_id):
        self.nurse_id = nurse_id
        self.assigned_doctor = None
        self.assessment_queue = queue.Queue()
        self.is_active = True
        self.thread = None

    def start_shift(self):
        """Start nurse's work loop"""
        self.thread = threading.Thread(target=self._work_loop, name=f"Nurse-{self.nurse_id}")
        self.thread.daemon = True
        self.thread.start()

    def _work_loop(self):
        """Continuous loop to assess patients"""
        while self.is_active:
            try:
                patient = self.assessment_queue.get(timeout=1)
                self.assess_patient(patient)
                self.assessment_queue.task_done()
            except queue.Empty:
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
        time.sleep(random.uniform(0.5, 1.0))  # Reduced from 5-10 seconds to 0.5-1 second
        patient.assign_random_disease()
        print(
            f"Patient {patient.patient_id} diagnosed with {patient.disease}, Severity: {patient.severity} by Nurse {self.nurse_id}")

    def post_surgery_check(self, patient: Patient):
        print(f"Nurse {self.nurse_id} performing post-surgery check on patient {patient.patient_id}")
        time.sleep(0.5)  # Reduced from 2 seconds to 0.5 seconds


class Doctor:
    def __init__(self, doctor_id: int, specialty: Specialty):
        self.doctor_id = doctor_id
        self.specialty = specialty
        self.patient_queue = queue.PriorityQueue()  # Change all doctors to use PriorityQueue
        self.assigned_nurse = None
        self.is_busy = False
        self.is_active = True
        self.thread = None

    def start_shift(self):
        """Start doctor's work loop"""
        self.thread = threading.Thread(target=self._work_loop, name=f"Doctor-{self.doctor_id}")
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
            except queue.Empty:
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


class ERDoctor(Doctor):
    def __init__(self, doctor_id):
        super().__init__(doctor_id, Specialty.GENERAL)
        self.patient_queue = queue.PriorityQueue()  # Priority queue for ER doctors
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
            time.sleep(random.randint(5, 10))
            
            # Increase Code Blue frequency
            code_blue = random.random() < 0.15  # 15% chance of Code Blue
            if code_blue:
                return self.handle_code_blue(patient)
            
            # Regular emergency treatment with higher mortality
            needs_blood_work = random.random() < 0.8  # 80% chance
            needs_xray = random.random() < 0.8  # 80% chance
            needs_surgery = random.random() < 0.6  # 60% chance
            
            if needs_blood_work:
                self.perform_blood_work(patient)
            if needs_xray:
                self.perform_xray(patient)
            
            if needs_surgery:
                success = self.perform_surgery(patient)
                self.is_available = True
                return success
            
            # Add chance of death even without surgery
            if patient.severity >= 7 and random.random() < 0.25:  # 25% death chance for severe cases
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
        time.sleep(random.randint(5, 10))
        
        # Increase Code Blue mortality
        patient_survived = random.random() < 0.2  # Only 20% survival rate
        if patient_survived:
            print(f"Patient {patient.patient_id} survived Code Blue!")
            self.hospital.stats.add_code_blue(True)
            return True
        else:
            print(f"Patient {patient.patient_id} did not survive Code Blue.")
            self.hospital.stats.add_code_blue(False)
            return False


class Ambulance:
    ambulance_counter = 1

    def __init__(self):
        self.ambulance_id = f"A{self.ambulance_counter}"
        Ambulance.ambulance_counter += 1
        self.patient = None
        self.patient_counter = 1  # Add counter for each ambulance's patients

    def pick_up_patient(self):
        age = random.randint(1, 100)
        # Create patient with ambulance-specific ID
        patient = Patient(age)
        patient.patient_id = f"{self.ambulance_id}-{self.patient_counter:03d}"
        self.patient_counter += 1
        self.patient = patient
        print(f"Ambulance {self.ambulance_id} picked up patient {patient.patient_id}")
        return patient


class EmergencyDepartment:
    def __init__(self, num_doctors=50, num_nurses=50):
        self.doctors = [ERDoctor(f"ER{i+1}") for i in range(num_doctors)]
        self.nurses = [Nurse(f"ERN{i+1}") for i in range(num_nurses)]
        
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
        return random.sample(available, min(count, len(available)))

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
        thread = threading.Thread(target=self.ambulance_arrival_loop, args=(hospital,))
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
            
            time.sleep(random.uniform(10, 15))  # More consistent ambulance arrivals


class MassCasualtyIncident:
    def __init__(self, hospital):
        self.hospital = hospital
        self.mci_patients = []
        self.is_active = True
        self.death_rate = 0.3  # 30% chance of death during MCI (higher than normal)
        
    def generate_mci_patient(self):
        """Generate a patient with high severity during MCI"""
        patient = Patient.create_emergency(random.randint(1, 100), "MCI")  # Use emergency creation
        patient.assign_random_disease()
        # Override severity to be very high (8-10)
        patient.severity = random.randint(8, 10)
        return patient
        
    def start_mci(self):
        print("\n🚨 MASS CASUALTY INCIDENT DECLARED! All available medical personnel responding! 🚨\n")
        
        # Get all available ER doctors
        er_doctors = [d for d in self.hospital.emergency_dept.doctors if d.is_available]
        
        # Get some regular doctors to help (30% of each department)
        regular_doctors = []
        for dept in self.hospital.departments.values():
            doctors_to_help = random.sample(dept['doctors'], k=max(1, len(dept['doctors']) // 3))
            regular_doctors.extend(doctors_to_help)
            
        all_available_doctors = er_doctors + regular_doctors
        print(f"Total doctors responding to MCI: {len(all_available_doctors)} ({len(er_doctors)} ER, {len(regular_doctors)} regular)")
        
        # Start MCI patient arrivals
        thread = threading.Thread(target=self.mci_patient_arrival_loop, args=(all_available_doctors,))
        thread.daemon = True  # Set daemon before starting
        thread.start()
        return thread
        
    def mci_patient_arrival_loop(self, available_doctors):
        """Generate MCI patients throughout the day"""
        start_time = time.time()
        day_duration = 60  # 1 minute for MCI day
        
        while self.is_active and (time.time() - start_time < day_duration):
            # Generate 3-7 patients every 5-10 seconds during MCI
            batch_size = random.randint(3, 7)
            for _ in range(batch_size):
                patient = self.generate_mci_patient()
                self.mci_patients.append(patient)
                print(f"MCI Patient {patient.patient_id} arrived with severity {patient.severity}")
                
                # Assign to available doctor
                if available_doctors:
                    doctor = random.choice(available_doctors)
                    threading.Thread(target=self.treat_mci_patient, args=(doctor, patient)).start()
                else:
                    print(f"⚠️ No doctors available for MCI patient {patient.patient_id}! Patient waiting...")
            
            time.sleep(random.randint(5, 10))  # 5-10 seconds between batches

    def treat_mci_patient(self, doctor, patient):
        """Use thread pool instead of creating new threads"""
        def process_mci():
            try:
                print(f"Doctor {doctor.doctor_id} treating MCI patient {patient.patient_id}")
                time.sleep(random.randint(5, 10))
                
                needs_blood_work = random.random() < 0.7
                needs_xray = random.random() < 0.7
                needs_surgery = random.random() < 0.5
                
                if needs_blood_work:
                    doctor.perform_blood_work(patient)
                if needs_xray:
                    doctor.perform_xray(patient)
                    
                if needs_surgery:
                    print(f"MCI Patient {patient.patient_id} requires emergency surgery")
                    time.sleep(random.randint(10, 15))
                    
                    if random.random() < self.death_rate:
                        with self.hospital.stats_lock:
                            self.hospital.stats.add_death(is_mci=True)
                        print(f"⚠️ MCI Patient {patient.patient_id} did not survive surgery")
                        return
                        
                    with self.hospital.stats_lock:
                        self.hospital.stats.add_survival(is_mci=True)
                    print(f"MCI Patient {patient.patient_id} survived surgery")
                    time.sleep(5)
                    
                print(f"MCI Patient {patient.patient_id} treatment complete")
            except Exception as e:
                print(f"Error treating MCI patient: {e}")

        # Use hospital's thread pool instead of creating new thread
        self.hospital.thread_pool.submit(process_mci)


class HospitalStatistics:
    def __init__(self):
        self.stats = {
            'visits': [0] * 7,  # Per day
            'waiting_times': [[] for _ in range(7)],  # List of waiting times per day
            'ambulance_arrivals': [0] * 7,
            'deaths': [0] * 7,
            'conditions': {disease: [0] * 7 for disease in Patient.severity_levels.keys()},
            'surgeries': {'total': [0] * 7, 'successful': [0] * 7, 'deaths': [0] * 7},
            'er_patients': [0] * 7,
            'procedures': {'xrays': [0] * 7, 'blood_work': [0] * 7},
            'code_blue': {'total': [0] * 7, 'successful': [0] * 7, 'deaths': [0] * 7},
            'survivals': [0] * 7,
            'department_visits': {dept.value: [0] * 7 for dept in Specialty},
            'mci_stats': {
                'patients': 0,
                'deaths': 0,
                'survivals': 0,
                'waiting_times': []
            },
            'receptionist_patients': {
                f'R{i+1}': [0] * 7 for i in range(6)  # Track each receptionist's patients per day
            }
        }
        self.start_time = time.time()

    def get_current_day(self):
        """Fix day calculation for compressed time"""
        elapsed_time = time.time() - self.start_time
        # Each day is 60 seconds in simulation time
        return min(int(elapsed_time / 60), 6)  # 0-6 for 7 days

    def add_visit(self, patient: Patient):
        day = self.get_current_day()
        self.stats['visits'][day] += 1

    def add_waiting_time(self, waiting_time: float, is_mci=False):
        if is_mci:
            self.stats['mci_stats']['waiting_times'].append(waiting_time)
        else:
            day = self.get_current_day()
            self.stats['waiting_times'][day].append(waiting_time)

    def add_ambulance_arrival(self):
        day = self.get_current_day()
        self.stats['ambulance_arrivals'][day] += 1

    def add_death(self, is_mci=False):
        day = self.get_current_day()
        self.stats['deaths'][day] += 1
        if is_mci:
            self.stats['mci_stats']['deaths'] += 1

    def add_condition(self, disease: str):
        day = self.get_current_day()
        self.stats['conditions'][disease][day] += 1

    def add_surgery(self, successful: bool, is_mci=False):
        day = self.get_current_day()
        self.stats['surgeries']['total'][day] += 1
        if successful:
            self.stats['surgeries']['successful'][day] += 1
            if is_mci:
                self.stats['mci_stats']['survivals'] += 1
        else:
            self.stats['surgeries']['deaths'][day] += 1

    def add_er_patient(self, is_mci=False):
        day = self.get_current_day()
        self.stats['er_patients'][day] += 1
        if is_mci:
            self.stats['mci_stats']['patients'] += 1

    def add_procedure(self, procedure_type: str):
        day = self.get_current_day()
        self.stats['procedures'][procedure_type][day] += 1

    def add_code_blue(self, successful: bool):
        day = self.get_current_day()
        self.stats['code_blue']['total'][day] += 1
        if successful:
            self.stats['code_blue']['successful'][day] += 1
        else:
            self.stats['code_blue']['deaths'][day] += 1

    def add_survival(self, is_mci=False):
        day = self.get_current_day()
        self.stats['survivals'][day] += 1
        if is_mci:
            self.stats['mci_stats']['survivals'] += 1

    def add_department_visit(self, department: Specialty):
        day = self.get_current_day()
        self.stats['department_visits'][department.value][day] += 1

    def add_receptionist_patient(self, receptionist_id: str):
        """Track patient registration by receptionist"""
        day = self.get_current_day()
        self.stats['receptionist_patients'][receptionist_id][day] += 1

    def visualize_statistics(self):
        plt.ioff()  # Turn off interactive mode
        try:
            days = [f"Day {i+1}" for i in range(7)]
            mci_day = self.get_current_day()  # Assuming MCI occurred today

            # Create figure with subplots
            plt.style.use('ggplot')  # Use ggplot style for better visualization
            fig = plt.figure(figsize=(20, 30))  # Increase figure size
            
            # 1. Total visits per day
            plt.subplot(5, 3, 1)
            plt.bar(days, self.stats['visits'], color='blue')
            plt.title('Total Visits per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Patients')

            # 2. Average waiting time per day
            plt.subplot(5, 3, 2)
            avg_waiting_times = [
                sum(times)/len(times) if times else 0 
                for times in self.stats['waiting_times']
            ]
            plt.bar(days, avg_waiting_times, color='green')
            plt.title('Average Waiting Time per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Minutes')

            # 3. Ambulance arrivals per day
            plt.subplot(5, 3, 3)
            plt.bar(days, self.stats['ambulance_arrivals'], color='red')
            plt.title('Ambulance Arrivals per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Arrivals')

            # 4. Deaths per day
            plt.subplot(5, 3, 4)
            plt.bar(days, self.stats['deaths'], color='black')
            plt.title('Deaths per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Deaths')

            # 5. Conditions per day (stacked bar)
            plt.subplot(5, 3, 5)
            conditions_df = pd.DataFrame(self.stats['conditions'], index=days)
            conditions_df.plot(kind='bar', stacked=True, ax=plt.gca())
            plt.title('Conditions per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Patients')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')

            # 6. Surgeries and outcomes
            plt.subplot(5, 3, 6)
            width = 0.35
            plt.bar(days, self.stats['surgeries']['successful'], width, label='Successful', color='green')
            plt.bar(days, self.stats['surgeries']['deaths'], width, 
                    bottom=self.stats['surgeries']['successful'], label='Deaths', color='red')
            plt.title('Surgery Outcomes per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Surgeries')
            plt.legend()

            # 7. ER Patients
            plt.subplot(5, 3, 7)
            plt.bar(days, self.stats['er_patients'], color='purple')
            plt.title('ER Patients per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Patients')

            # 8. Procedures
            plt.subplot(5, 3, 8)
            width = 0.35
            x = np.arange(len(days))
            plt.bar(x - width/2, self.stats['procedures']['xrays'], width, label='X-rays', color='blue')
            plt.bar(x + width/2, self.stats['procedures']['blood_work'], width, label='Blood Work', color='red')
            plt.title('Procedures per Day')
            plt.xticks(x, days, rotation=45)
            plt.ylabel('Number of Procedures')
            plt.legend()

            # 9. Code Blue Outcomes
            plt.subplot(5, 3, 9)
            plt.bar(days, self.stats['code_blue']['successful'], width, label='Successful', color='green')
            plt.bar(days, self.stats['code_blue']['deaths'], width, 
                    bottom=self.stats['code_blue']['successful'], label='Deaths', color='red')
            plt.title('Code Blue Outcomes per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Cases')
            plt.legend()

            # 10. Survivals per day
            plt.subplot(5, 3, 10)
            plt.bar(days, self.stats['survivals'], color='green')
            plt.title('Survivals per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Survivals')

            # 11. Department Visits
            plt.subplot(5, 3, 11)
            dept_df = pd.DataFrame(self.stats['department_visits'], index=days)
            dept_df.plot(kind='bar', stacked=True, ax=plt.gca())
            plt.title('Department Visits per Day')
            plt.xticks(rotation=45)
            plt.ylabel('Number of Visits')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')

            # 12. MCI Statistics
            plt.subplot(5, 3, 12)
            mci_stats = [
                self.stats['mci_stats']['patients'],
                self.stats['mci_stats']['survivals'],
                self.stats['mci_stats']['deaths']
            ]
            plt.bar(['Total Patients', 'Survivals', 'Deaths'], mci_stats, 
                    color=['blue', 'green', 'red'])
            plt.title(f'MCI Statistics (Day {mci_day + 1})')
            plt.ylabel('Number of Patients')

            # Move Receptionist Statistics to subplot 13 (previously 14)
            plt.subplot(5, 3, 13)  # Changed from 14 to 13
            receptionist_df = pd.DataFrame(self.stats['receptionist_patients'], index=days)
            
            # Create stacked bar chart for receptionists
            ax = receptionist_df.plot(kind='bar', stacked=False, ax=plt.gca(), 
                                    width=0.8, 
                                    color=['blue', 'green', 'red', 'purple', 'orange', 'cyan'])
            
            plt.title('Patients Registered by Each Receptionist per Day')
            plt.xlabel('Day')
            plt.ylabel('Number of Patients')
            plt.legend(title='Receptionist', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            
            # Add value labels on the bars
            for container in ax.containers:
                ax.bar_label(container, padding=3)

            # Adjust layout and save
            plt.tight_layout()
            plt.savefig('hospital_statistics.png', dpi=300, bbox_inches='tight')
            
        finally:
            plt.close('all')  # Ensure all figures are closed
            plt.ion()  # Restore interactive mode

        # Modify the statistics summary printing
        print("\nDetailed Hospital Statistics Summary:")
        total_patients = sum(self.stats['visits'])
        expected_patients = 7 * 150  # Calculate expected patients
        print(f"Total patients: {total_patients} (Expected: {expected_patients})")
        print(f"Total deaths: {sum(self.stats['deaths'])}")
        print(f"Total surgeries: {sum(self.stats['surgeries']['total'])}")
        print(f"Successful surgeries: {sum(self.stats['surgeries']['successful'])}")
        print(f"Total ER patients: {sum(self.stats['er_patients'])}")
        print(f"Total Code Blue cases: {sum(self.stats['code_blue']['total'])}")
        print(f"Code Blue survivals: {sum(self.stats['code_blue']['successful'])}")
        
        # Calculate and print average waiting times per day
        print("\nAverage Waiting Times per Day:")
        for day, times in enumerate(self.stats['waiting_times']):
            if times:
                avg = sum(times) / len(times)
                print(f"Day {day + 1}: {avg:.2f} seconds")

        # Print MCI statistics without waiting times
        print("\nMCI Day Statistics:")
        print(f"Total MCI patients: {self.stats['mci_stats']['patients']}")
        print(f"MCI survivals: {self.stats['mci_stats']['survivals']}")
        print(f"MCI deaths: {self.stats['mci_stats']['deaths']}")

        # Print receptionist statistics with percentages
        print("\nReceptionist Statistics:")
        total_registered = sum(sum(counts) for counts in self.stats['receptionist_patients'].values())
        for receptionist_id, daily_counts in self.stats['receptionist_patients'].items():
            total_patients = sum(daily_counts)
            percentage = (total_patients / total_registered * 100) if total_registered > 0 else 0
            print(f"{receptionist_id}: Total patients: {total_patients}, "
                  f"Daily average: {total_patients/7:.1f}, "
                  f"Percentage: {percentage:.1f}%")


class SurgeryDepartment:
    def __init__(self, num_surgeons=10, num_nurses=15):
        self.surgeons = [Doctor(f"SUR{i+1}", Specialty.SURGERY) for i in range(num_surgeons)]
        self.nurses = [Nurse(f"SN{i+1}") for i in range(num_nurses)]
        
        # Assign nurses to surgeons (some surgeons get 2 nurses)
        for i, surgeon in enumerate(self.surgeons):
            nurse1 = self.nurses[i]
            nurse2 = self.nurses[i + len(self.surgeons)] if i < len(self.nurses) - len(self.surgeons) else None
            
            surgeon.assigned_nurse = nurse1
            nurse1.assigned_doctor = surgeon
            if nurse2:
                nurse2.assigned_doctor = surgeon
            
        self.surgery_queue = PriorityQueue()
        self.surgery_lock = threading.Lock()  # Add lock

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
                
            surgeon = random.choice(available_surgeons)
            surgeon.is_busy = True
        
        try:
            print(f"Surgeon {surgeon.doctor_id} performing surgery on patient {patient.patient_id}")
            time.sleep(random.uniform(1.0, 2.0))  # Reduced from 10-15 seconds to 1-2 seconds
            
            # Increase surgery mortality based on severity
            death_chance = 0.1  # Base 10% chance
            if patient.severity >= 8:
                death_chance = 0.3  # 30% for severe cases
            if patient.severity >= 9:
                death_chance = 0.5  # 50% for critical cases
            
            success = random.random() > death_chance
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

class DiagnosticsDepartment:
    def __init__(self, num_technicians=10, num_nurses=10):
        self.technicians = [Doctor(f"DIAG{i+1}", Specialty.DIAGNOSTICS) for i in range(num_technicians)]
        self.nurses = [Nurse(f"DN{i+1}") for i in range(num_nurses)]
        
        # Assign nurses to technicians
        for tech, nurse in zip(self.technicians, self.nurses):
            tech.assigned_nurse = nurse
            nurse.assigned_doctor = tech
            
        self.blood_work_queue = queue.Queue()
        self.xray_queue = queue.Queue()
        self.tech_lock = threading.Lock()
        
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
                
            tech = random.choice(available_techs)
            tech.is_busy = True
            
        try:
            print(f"Technician {tech.doctor_id} performing blood work for patient {patient.patient_id}")
            time.sleep(random.uniform(0.5, 1.0))  # Reduced from 5-10 seconds to 0.5-1 second
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
                
            tech = random.choice(available_techs)
            tech.is_busy = True
        
        try:
            print(f"Technician {tech.doctor_id} performing X-ray for patient {patient.patient_id}")
            time.sleep(random.uniform(0.5, 1.0))  # Reduced from 5-10 seconds to 0.5-1 second
            hospital_stats.add_procedure('xrays')
        finally:
            tech.is_busy = False


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
            doctors = [Doctor(f"{specialty.value[0]}{i+1}", specialty) for i in range(10)]
            nurses = [Nurse(f"{specialty.value[0]}N{i+1}") for i in range(15)]  # 15 nurses per department
            
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
            
        self.assessment_nurses = [Nurse(f"AN{i+1}") for i in range(10)]  # More assessment nurses
        self.waiting_room = deque()
        self.running = True
        self.simulation_time = 7 * 60  # One week = 7 minutes in real time
        self.mci = None
        self.mci_day = random.randint(1, 7)  # Random day for MCI to occur
        self.stats = HospitalStatistics()
        self.stats_lock = threading.Lock()  # Add lock for statistics
        self.threads = []  # Track all threads
        
        # Add signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
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
        sys.exit(0)
        
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
        start_time = time.time()
        day = 0
        patients_today = 0
        current_receptionist = 0

        while self.running and (time.time() - start_time < self.simulation_time):
            current_day = int((time.time() - start_time) / 60)
            
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
                    age = random.randint(1, 100)
                    # Round-robin assignment
                    receptionist = self.receptionists[current_receptionist]
                    current_receptionist = (current_receptionist + 1) % len(self.receptionists)
                    patient = receptionist.register_patient(age)
                    self.process_patient(patient)
                
                # Wait 6 seconds between groups
                time.sleep(6)  # This ensures even distribution across the minute
            else:
                # Wait for next day
                time.sleep(0.1)

    def process_patient(self, patient):
        def process():
            try:
                nurse = random.choice(self.assessment_nurses)
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
                    
                    waiting_time = time.time() - patient.arrival_time
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
        arrival_time = time.time()
        print(f"Emergency case! Patient {patient.patient_id} directed to ER")
        
        try:
            # Ensure patient has severity set
            if patient.severity is None:
                # Get a nurse to assess the patient first
                nurse = random.choice(self.emergency_dept.nurses)
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
            waiting_time = time.time() - arrival_time
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
            
            start_time = time.time()
            end_time = start_time + self.simulation_time  # 7 minutes total
            
            # Start regular patient arrivals
            patient_thread = threading.Thread(target=self.patient_arrival, name="PatientArrival")
            patient_thread.daemon = True
            patient_thread.start()
            
            # Start ambulance arrivals
            ambulance_thread = self.emergency_dept.start_ambulance_arrivals(self)
            
            # Add threads to tracking list
            self.threads.extend([patient_thread, ambulance_thread])
            
            # Monitor for MCI day and show progress
            mci_thread = None
            while self.running and time.time() <= end_time:  # Changed < to <= to include full last day
                current_time = time.time() - start_time
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
                
                time.sleep(1)  # Check progress every second
            
            # Give extra time for day 7 to complete all processes
            print("\nFinalizing day 7 operations...")
            time.sleep(10)  # Allow time for final ambulances and treatments
            
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
            wait_start = time.time()
            while time.time() - wait_start < max_wait:
                queues_empty = all(doctor.patient_queue.empty() for doctor in all_doctors)
                doctors_free = all(not doctor.is_busy for doctor in all_doctors)
                
                if queues_empty and doctors_free:
                    print("All patients have been treated.")
                    break
                time.sleep(1)
            
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
                total_time = time.time() - start_time
                print(f"\nSimulation ran for {total_time/60:.1f} minutes of real time")
                print("Generating statistics...")
                self.stats.visualize_statistics()
                print("Statistics saved to 'hospital_statistics.png'")


if __name__ == "__main__":
    hospital = HospitalSimulation()
    hospital.run()
