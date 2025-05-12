import sqlite3
from threading import Lock
from random import randint
from collections import defaultdict

from matplotlib import pyplot as plt


class Statistics:
    def __init__(self, db_name="hospital_stats.db"):
        self.db_name = db_name
        self.lock = Lock()
        self.mci_day = randint(0, 6)  # Random day for MCI

        # Initialize the database
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    day INTEGER PRIMARY KEY,
                    total_visits INTEGER DEFAULT 0,
                    ambulance_arrivals INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    surgeries INTEGER DEFAULT 0,
                    surgery_success INTEGER DEFAULT 0,
                    er_patients INTEGER DEFAULT 0,
                    xrays INTEGER DEFAULT 0,
                    blood_works INTEGER DEFAULT 0,
                    code_blues INTEGER DEFAULT 0,
                    code_blue_success INTEGER DEFAULT 0,
                    survivals INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conditions (
                    day INTEGER,
                    condition TEXT,
                    count INTEGER DEFAULT 0,
                    PRIMARY KEY (day, condition)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mci_stats (
                    mci_day INTEGER PRIMARY KEY,
                    mci_patients INTEGER DEFAULT 0,
                    mci_deaths INTEGER DEFAULT 0,
                    mci_survivals INTEGER DEFAULT 0
                )
            """)

            # Create the waiting_times table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS waiting_times (
                    day INTEGER,
                    waiting_time REAL,
                    PRIMARY KEY (day, waiting_time)
                )
            """)

            # Create the patients_per_department table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients_per_department (
                    day INTEGER,
                    department TEXT,
                    count INTEGER DEFAULT 0,
                    PRIMARY KEY (day, department)
                )
            """)

            # Insert initial MCI day
            cursor.execute("""
                INSERT OR IGNORE INTO mci_stats (mci_day) VALUES (?)
            """, (self.mci_day,))

    def record_visit(self, day, patient):
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Update daily stats
            cursor.execute("""
                INSERT INTO daily_stats (day, total_visits, ambulance_arrivals, deaths, surgeries, 
                                         surgery_success, er_patients, xrays, blood_works, code_blues, 
                                         code_blue_success, survivals)
                VALUES (?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                ON CONFLICT(day) DO NOTHING
            """, (day,))

            cursor.execute("""
                UPDATE daily_stats
                SET total_visits = total_visits + 1
                WHERE day = ?
            """, (day,))

            # Update conditions
            if patient.condition:
                cursor.execute("""
                    INSERT INTO conditions (day, condition, count)
                    VALUES (?, ?, 0)
                    ON CONFLICT(day, condition) DO NOTHING
                """, (day, patient.condition))

                cursor.execute("""
                    UPDATE conditions
                    SET count = count + 1
                    WHERE day = ? AND condition = ?
                """, (day, patient.condition))

            # Update other stats
            if patient.severity is not None and patient.severity >= 8:
                cursor.execute("""
                    UPDATE daily_stats
                    SET er_patients = er_patients + 1
                    WHERE day = ?
                """, (day,))

            # Record patients per department
            if patient.department:
                cursor.execute("""
                        INSERT INTO patients_per_department (day, department, count)
                        VALUES (?, ?, 0)
                        ON CONFLICT(day, department) DO NOTHING
                    """, (day, patient.department))

                cursor.execute("""
                        UPDATE patients_per_department
                        SET count = count + 1
                        WHERE day = ? AND department = ?
                    """, (day, patient.department))

            if patient.had_surgery:
                cursor.execute("""
                    UPDATE daily_stats
                    SET surgeries = surgeries + 1
                    WHERE day = ?
                """, (day,))
                if patient.surgery_success:
                    cursor.execute("""
                        UPDATE daily_stats
                        SET surgery_success = surgery_success + 1
                        WHERE day = ?
                    """, (day,))

            if patient.had_blood_work:
                cursor.execute("""
                    UPDATE daily_stats
                    SET blood_works = blood_works + 1
                    WHERE day = ?
                """, (day,))

            if patient.had_xray:
                cursor.execute("""
                    UPDATE daily_stats
                    SET xrays = xrays + 1
                    WHERE day = ?
                """, (day,))

            if patient.had_code_blue:
                cursor.execute("""
                    UPDATE daily_stats
                    SET code_blues = code_blues + 1
                    WHERE day = ?
                """, (day,))
                if patient.code_blue_success:
                    cursor.execute("""
                        UPDATE daily_stats
                        SET code_blue_success = code_blue_success + 1
                        WHERE day = ?
                    """, (day,))

            if patient.came_by_ambulance:
                cursor.execute("""
                    UPDATE daily_stats
                    SET ambulance_arrivals = ambulance_arrivals + 1
                    WHERE day = ?
                """, (day,))

            if patient.dead:
                cursor.execute("""
                    UPDATE daily_stats
                    SET deaths = deaths + 1
                    WHERE day = ?
                """, (day,))
            else:
                cursor.execute("""
                    UPDATE daily_stats
                    SET survivals = survivals + 1
                    WHERE day = ?
                """, (day,))

            # Record waiting time (if applicable)
            if patient.doctor_start_time and patient.arrival_time:
                wait_time = (patient.doctor_start_time - patient.arrival_time) * 1800 / 60
                cursor.execute("""
                    INSERT INTO waiting_times (day, waiting_time)
                    VALUES (?, ?)
                """, (day, wait_time))

    def record_mci_patient(self, patient):
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE mci_stats
                SET mci_patients = mci_patients + 1
            """)

            if patient.dead:
                cursor.execute("""
                    UPDATE mci_stats
                    SET mci_deaths = mci_deaths + 1
                """)
            else:
                cursor.execute("""
                    UPDATE mci_stats
                    SET mci_survivals = mci_survivals + 1
                """)

    def fetch_data_from_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Query total visits per day
            cursor.execute("SELECT total_visits FROM daily_stats ORDER BY day")
            total_visits_per_day = [row[0] for row in cursor.fetchall()]

            # Query ambulance arrivals per day
            cursor.execute("SELECT ambulance_arrivals FROM daily_stats ORDER BY day")
            ambulance_arrivals_per_day = [row[0] for row in cursor.fetchall()]

            # Query deaths per day
            cursor.execute("SELECT deaths FROM daily_stats ORDER BY day")
            deaths_per_day = [row[0] for row in cursor.fetchall()]

            # Query surgeries and successful surgeries per day
            cursor.execute("SELECT surgeries, surgery_success FROM daily_stats ORDER BY day")
            surgeries_data = cursor.fetchall()
            surgeries_per_day = [row[0] for row in surgeries_data]
            surgery_success_per_day = [row[1] for row in surgeries_data]

            # Query ER patients per day
            cursor.execute("SELECT er_patients FROM daily_stats ORDER BY day")
            er_patients_per_day = [row[0] for row in cursor.fetchall()]

            # Query X-rays and blood works per day
            cursor.execute("SELECT xrays, blood_works FROM daily_stats ORDER BY day")
            tests_data = cursor.fetchall()
            xrays_per_day = [row[0] for row in tests_data]
            blood_works_per_day = [row[1] for row in tests_data]

            # Query code blues and successful code blues per day
            cursor.execute("SELECT code_blues, code_blue_success FROM daily_stats ORDER BY day")
            code_blues_data = cursor.fetchall()
            code_blues_per_day = [row[0] for row in code_blues_data]
            code_blue_success_per_day = [row[1] for row in code_blues_data]

            # Query survivals per day
            cursor.execute("SELECT survivals FROM daily_stats ORDER BY day")
            survivals_per_day = [row[0] for row in cursor.fetchall()]

            # Query conditions for all days
            cursor.execute("SELECT day, condition, count FROM conditions")
            conditions_data = cursor.fetchall()
            conditions_per_day = defaultdict(dict)
            for day, condition, count in conditions_data:
                conditions_per_day[day][condition] = count

            # Ensure all days (0-6) are present in the dictionary
            for day in range(7):
                if day not in conditions_per_day:
                    conditions_per_day[day] = {}

            # Query MCI stats
            cursor.execute("SELECT mci_patients, mci_survivals, mci_deaths FROM mci_stats")
            mci_stats = cursor.fetchone()
            mci_patients, mci_survivals, mci_deaths = mci_stats

            # Query waiting times (if stored in a separate table)
            cursor.execute("SELECT day, waiting_time FROM waiting_times ORDER BY day")
            waiting_times_data = cursor.fetchall()
            waiting_times_per_day = [[] for _ in range(7)]
            for day, waiting_time in waiting_times_data:
                waiting_times_per_day[day].append(waiting_time)

            # Query patients per department for all days
            cursor.execute("SELECT day, department, count FROM patients_per_department")
            department_data = cursor.fetchall()
            patients_per_department = defaultdict(lambda: defaultdict(int))
            for day, department, count in department_data:
                patients_per_department[day][department] = count

            # Ensure all days (0-6) are present in the dictionary
            for day in range(7):
                if day not in patients_per_department:
                    patients_per_department[day] = {}

                # Query waiting times for the MCI day
            cursor.execute("SELECT waiting_time FROM waiting_times WHERE day = ?", (self.mci_day,))
            mci_waiting_times = [row[0] for row in cursor.fetchall()]

        return {
            "total_visits_per_day": total_visits_per_day,
            "ambulance_arrivals_per_day": ambulance_arrivals_per_day,
            "deaths_per_day": deaths_per_day,
            "surgeries_per_day": surgeries_per_day,
            "surgery_success_per_day": surgery_success_per_day,
            "er_patients_per_day": er_patients_per_day,
            "xrays_per_day": xrays_per_day,
            "blood_works_per_day": blood_works_per_day,
            "code_blues_per_day": code_blues_per_day,
            "code_blue_success_per_day": code_blue_success_per_day,
            "survivals_per_day": survivals_per_day,
            "conditions_per_day": conditions_per_day,
            "mci_patients": mci_patients,
            "mci_survivals": mci_survivals,
            "mci_deaths": mci_deaths,
            "waiting_times_per_day": waiting_times_per_day,
            "patients_per_department": patients_per_department,
            "mci_waiting_times": mci_waiting_times,
        }

    def visualize_data(self):
        print("\n📊 Hospital Simulation Statistics 📊")

        data = self.fetch_data_from_db()

        # Calculate average waiting times
        avg_waiting_times = []
        for day_waiting_times in data["waiting_times_per_day"]:
            if day_waiting_times:
                avg_waiting_times.append(int(sum(day_waiting_times) / len(day_waiting_times)))
            else:
                avg_waiting_times.append(0)

        # Create figure with multiple subplots
        fig, axs = plt.subplots(4, 3, figsize=(16, 14))
        fig.suptitle('Hospital Simulation: 7-Day Statistics', fontsize=16)

        # Total visits per day
        axs[0, 0].bar(range(1, 8), data["total_visits_per_day"])
        axs[0, 0].set_title('Total Visits per Day')
        axs[0, 0].set_xlabel('Day')
        axs[0, 0].set_ylabel('Number of Visits')

        # Average waiting time
        axs[0, 1].bar(range(1, 8), avg_waiting_times)
        axs[0, 1].set_title('Average Waiting Time per Day')
        axs[0, 1].set_xlabel('Day')
        axs[0, 1].set_ylabel('Time (minutes)')
        max_wait = max(avg_waiting_times)
        y_ticks = list(range(0, max_wait + 20, 10))
        axs[0, 1].set_yticks(y_ticks)
        axs[0, 1].set_ylim(bottom=0)

        # Ambulance arrivals
        axs[0, 2].bar(range(1, 8), data["ambulance_arrivals_per_day"])
        axs[0, 2].set_title('Ambulance Arrivals per Day')
        axs[0, 2].set_xlabel('Day')
        axs[0, 2].set_ylabel('Number of Ambulances')

        # Deaths per day
        axs[1, 0].bar(range(1, 8), data["deaths_per_day"])
        axs[1, 0].set_title('Deaths per Day')
        axs[1, 0].set_xlabel('Day')
        axs[1, 0].set_ylabel('Number of Deaths')

        # Number of surgeries and outcomes
        axs[1, 1].bar(range(1, 8), data["surgeries_per_day"], label='Total Surgeries')
        axs[1, 1].bar(range(1, 8), data["surgery_success_per_day"], label='Successful')
        axs[1, 1].set_title('Surgeries per Day and Outcomes')
        axs[1, 1].set_xlabel('Day')
        axs[1, 1].set_ylabel('Number of Surgeries')
        axs[1, 1].legend()

        # Number of ER patients
        axs[1, 2].bar(range(1, 8), data["er_patients_per_day"])
        axs[1, 2].set_title('ER Patients per Day')
        axs[1, 2].set_xlabel('Day')
        axs[1, 2].set_ylabel('Number of Patients')

        # Number of X-rays and blood works
        axs[2, 0].bar(range(1, 8), data["xrays_per_day"], label='X-rays')
        axs[2, 0].bar(range(1, 8), data["blood_works_per_day"], bottom=data["xrays_per_day"], label='Blood Works')
        axs[2, 0].set_title('X-rays and Blood Works per Day')
        axs[2, 0].set_xlabel('Day')
        axs[2, 0].set_ylabel('Number of Tests')
        axs[2, 0].legend()

        # Number of code blues and outcomes
        axs[2, 1].bar(range(1, 8), data["code_blues_per_day"], label='Total Code Blues')
        axs[2, 1].bar(range(1, 8), data["code_blue_success_per_day"], label='Successful')
        axs[2, 1].set_title('Code Blues per Day and Outcomes')
        axs[2, 1].set_xlabel('Day')
        axs[2, 1].set_ylabel('Number of Code Blues')
        axs[2, 1].legend()

        # Survivals per day
        axs[2, 2].bar(range(1, 8), data["survivals_per_day"])
        axs[2, 2].set_title('Survivals per Day')
        axs[2, 2].set_xlabel('Day')
        axs[2, 2].set_ylabel('Number of Survivals')

        # Plot conditions for Day 1 as an example
        day_to_show = 0
        conditions = list(data["conditions_per_day"][day_to_show].keys())
        condition_counts = [data["conditions_per_day"][day_to_show][c] for c in conditions]
        axs[3, 0].bar(conditions, condition_counts)
        axs[3, 0].set_title(f'Conditions on Day 1')
        axs[3, 0].set_xlabel('Condition')
        axs[3, 0].set_ylabel('Number of Patients')
        axs[3, 0].tick_params(axis='x', rotation=45)

        # Plot departments for Day 1 as an example
        departments = list(data["patients_per_department"][day_to_show].keys())
        department_counts = [data["patients_per_department"][day_to_show][d] for d in departments]
        axs[3, 1].bar(departments, department_counts)
        axs[3, 1].set_title(f'Departments on Day 1')
        axs[3, 1].set_xlabel('Department')
        axs[3, 1].set_ylabel('Number of Patients')
        axs[3, 1].tick_params(axis='x', rotation=45)

        # MCI day statistics
        mci_labels = ['Patients', 'Survivals', 'Deaths']
        mci_values = [data["mci_patients"], data["mci_survivals"], data["mci_deaths"]]
        axs[3, 2].bar(mci_labels, mci_values)
        axs[3, 2].set_title(f'MCI Day (Day {self.mci_day + 1}) Statistics')
        axs[3, 2].set_xlabel('Category')
        axs[3, 2].set_ylabel('Count')

        plt.tight_layout()
        plt.savefig('hospital_statistics.png')
        print(f"Statistics visualization saved as 'hospital_statistics.png'")

        # Print textual summary
        print("\n=== 7-Day Hospital Simulation Summary ===")
        total_patients = sum(data["total_visits_per_day"])
        total_deaths = sum(data["deaths_per_day"])
        death_rate = (total_deaths / total_patients) * 100 if total_patients > 0 else 0

        print(f"""
        Total Patients: {total_patients}
        Total Deaths: {total_deaths} ({death_rate:.2f}%)
        Total Surgeries: {sum(data["surgeries_per_day"])}
        Successful Surgeries: {sum(data["surgery_success_per_day"])}
        Total Code Blues: {sum(data["code_blues_per_day"])}
        Successful Code Blues: {sum(data["code_blue_success_per_day"])}
        """)

        # Average waiting time overall
        all_waiting_times = [time for day_times in data["waiting_times_per_day"] for time in day_times]
        if all_waiting_times:
            avg_wait = sum(all_waiting_times) / len(all_waiting_times)
            print(f"Average Waiting Time: {int(avg_wait)} minutes")

        # MCI day statistics
        print(f"""
        \n=== Mass Casualty Incident (Day {self.mci_day + 1}) ===
        Total MCI Patients: {data["mci_patients"]}
        MCI Survivals: {data["mci_survivals"]}
        MCI Deaths: {data["mci_deaths"]}
        """)

        if data["mci_waiting_times"]:
            avg_mci_wait = sum(data["mci_waiting_times"]) / len(data["mci_waiting_times"])
            print(f"Average Waiting Time during MCI: {int(avg_mci_wait)} minutes")