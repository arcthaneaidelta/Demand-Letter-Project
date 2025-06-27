from typing import List, Optional
import json
import os
from ai.src.write_a_book_with_flows.types_1 import EmployerInfo, EmployeeInfo, IncidentInfo, DemandLetterInfo


def collect_employer_info() -> EmployerInfo:
    """Collect employer information from the user"""
    print("\n=== EMPLOYER INFORMATION ===")
    print("Please provide the following details about the employer:\n")
    
    name = input("Employer Name: ")
    address = input("Employer Address: ")
    recipient_name = input("Recipient Name (person who will receive the letter): ")
    recipient_title = input("Recipient Title: ")
    
    business_registration = input("Business Registration Number (optional - press Enter to skip): ").strip() or None
    employer_id = input("Employer ID Number (optional - press Enter to skip): ").strip() or None
    
    supervisor_input = input("Supervisor Names (comma separated, optional - press Enter to skip): ").strip()
    supervisor_names = [name.strip() for name in supervisor_input.split(",")] if supervisor_input else None
    
    return EmployerInfo(
        name=name,
        address=address,
        recipient_name=recipient_name,
        recipient_title=recipient_title,
        business_registration=business_registration,
        employer_id=employer_id,
        supervisor_names=supervisor_names
    )


def collect_employee_info() -> EmployeeInfo:
    """Collect employee information from the user"""
    print("\n=== EMPLOYEE INFORMATION ===")
    print("Please provide the following details about the employee:\n")
    
    name = input("Employee Name: ")
    position = input("Position/Job Title: ")
    start_date = input("Employment Start Date: ")
    end_date = input("Employment End Date (if applicable, press Enter to skip): ").strip() or None
    employee_id = input("Employee ID (optional - press Enter to skip): ").strip() or None
    work_location = input("Work Location: ")
    pay_rate = input("Pay Rate/Salary: ")
    work_schedule = input("Work Schedule/Hours: ")
    department = input("Department/Division (optional - press Enter to skip): ").strip() or None
    reporting_to = input("Reporting To (manager/supervisor name, optional - press Enter to skip): ").strip() or None
    contact_info = input("Contact Information for correspondence: ")
    
    return EmployeeInfo(
        name=name,
        position=position,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        work_location=work_location,
        pay_rate=pay_rate,
        work_schedule=work_schedule,
        department=department,
        reporting_to=reporting_to,
        contact_info=contact_info
    )


def collect_incident_info() -> List[IncidentInfo]:
    """Collect information about incidents from the user"""
    incidents = []
    
    print("\n=== INCIDENT INFORMATION ===")
    print("Please provide information about incidents or violations:\n")
    
    while True:
        print(f"\nIncident #{len(incidents) + 1}")
        description = input("Description of the incident/violation: ")
        
        dates_input = input("Date(s) of incident (comma separated): ")
        dates = [date.strip() for date in dates_input.split(",")]
        
        witnesses_input = input("Witnesses (comma separated, optional - press Enter to skip): ").strip()
        witnesses = [name.strip() for name in witnesses_input.split(",")] if witnesses_input else None
        
        evidence_input = input("Evidence (comma separated, optional - press Enter to skip): ").strip()
        evidence = [item.strip() for item in evidence_input.split(",")] if evidence_input else None
        
        complaints_input = input("Prior complaints made (comma separated, optional - press Enter to skip): ").strip()
        prior_complaints = [complaint.strip() for complaint in complaints_input.split(",")] if complaints_input else None
        
        incidents.append(IncidentInfo(
            description=description,
            dates=dates,
            witnesses=witnesses,
            evidence=evidence,
            prior_complaints=prior_complaints
        ))
        
        add_another = input("\nAdd another incident? (y/n): ").strip().lower()
        if add_another != 'y':
            break
    
    return incidents


def collect_demand_letter_info() -> DemandLetterInfo:
    """Collect all information needed for a demand letter"""
    print("=== DEMAND LETTER INFORMATION COLLECTION ===")
    print("This tool will collect necessary information to generate a formal demand letter.")
    print("Please fill in the following information carefully.\n")
    
    employer = collect_employer_info()
    employee = collect_employee_info()
    incidents = collect_incident_info()
    
    # Create the complete demand letter info object
    demand_letter_info = DemandLetterInfo(
        employer=employer,
        employee=employee,
        incidents=incidents
    )
    
    # Save the information to a file for future reference
    save_to_file(demand_letter_info)
    
    return demand_letter_info


def save_to_file(info: DemandLetterInfo) -> None:
    """Save the collected information to a JSON file"""
    try:
        # Create 'data' directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Convert to dict for JSON serialization
        info_dict = info.model_dump()
        
        # Save to file
        with open('data/demand_letter_info.json', 'w') as f:
            json.dump(info_dict, f, indent=2)
            
        print("\nInformation saved successfully to data/demand_letter_info.json")
    except Exception as e:
        print(f"\nError saving information to file: {e}")


def load_from_file() -> Optional[DemandLetterInfo]:
    """Load previously saved information from a JSON file"""
    try:
        file_path = 'data/demand_letter_info.json'
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r') as f:
            info_dict = json.load(f)
            
        return DemandLetterInfo.model_validate(info_dict)
    except Exception as e:
        print(f"Error loading information from file: {e}")
        return None


if __name__ == "__main__":
    # Test the information collection
    info = collect_demand_letter_info()
    print("\nCollected information:")
    print(json.dumps(info.model_dump(), indent=2)) 