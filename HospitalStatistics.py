from time import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from Patient import Patient
from Specialty import Specialty


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
                f'R{i + 1}': [0] * 7 for i in range(6)  # Track each receptionist's patients per day
            }
        }
        self.start_time = time()

    def get_current_day(self):
        """Fix day calculation for compressed time"""
        elapsed_time = time() - self.start_time
        # Each day is 60 seconds in simulation time
        return min(int(elapsed_time / 60), 6)  # 0-6 for 7 days

    def add_visit(self, patient: Patient):gO
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
            days = [f"Day {i + 1}" for i in range(7)]
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
                sum(times) / len(times) if times else 0
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
            plt.bar(x - width / 2, self.stats['procedures']['xrays'], width, label='X-rays', color='blue')
            plt.bar(x + width / 2, self.stats['procedures']['blood_work'], width, label='Blood Work', color='red')
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
                  f"Daily average: {total_patients / 7:.1f}, "
                  f"Percentage: {percentage:.1f}%")
