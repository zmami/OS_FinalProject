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