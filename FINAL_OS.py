from HospitalSimulation import HospitalSimulation


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