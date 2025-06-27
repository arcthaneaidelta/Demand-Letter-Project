from ai.src.write_a_book_with_flows.types_1 import (
    DemandLetterInfo, 
    EmployeeInfo, 
    EmployerInfo, 
    IncidentInfo
)
from typing import Dict, Any, List


def process_salesforce_data(data: Dict[str, Any]) -> DemandLetterInfo:
    """
    Process Salesforce data into DemandLetterInfo format
    
    Args:
        data: Dictionary containing data from Salesforce
        
    Returns:
        DemandLetterInfo object with properly formatted data
    """
    # Extract employee information
    employee = EmployeeInfo(
        name=data.get("Client_Name__c", ""),
        position=data.get("Position_Title__c", ""),
        address=f"{data.get('Client_Address__Street__s', '')} {data.get('Client_Address__City__s', '')}, {data.get('Client_Address__StateCode__s', '')} {data.get('Client_Address__PostalCode__s', '')}",
        email=data.get("Client_Email__c", ""),
        phone=data.get("Client_Phone_Number__c", ""),
        start_date=data.get("Start_Date_of_Employment__c", "").split()[0] if data.get("Start_Date_of_Employment__c") else "",
        end_date=data.get("Last_Date_of_Employment__c", "").split()[0] if data.get("Last_Date_of_Employment__c") else "",
        hourly_rate=float(data.get("Hourly_Rate__c", 0)),
        weekly_hours=float(data.get("Hours_Worked_per_Week__c", 0)),
    )


    # Extract employer information
    employer = EmployerInfo(
        name=data.get("Name_Of_Employer__c", ""),
        address=f"{data.get('Employer_Address__Street__s', '')} {data.get('Employer_Address__City__s', '')}, {data.get('Employer_Address__StateCode__s', '')} {data.get('Employer_Address__PostalCode__s', '')}",
    )
    
    incidents = {}
    
    # Discrimination/FEHA incident
    if data.get('FEHA__c') == 'Yes' or any(data.get(f) == 1 for f in [
        'Race_Color__c', 'Religion__c', 'Sex_or_Gender__c', 'Sexual_Orientation__c',
        'Ancestry_or_National_Origin__c', 'Age_40_or_over__c', 'Mental_Disability__c',
        'Physical_Disability__c', 'Gender_Identity_or_Expression__c', 'Medical_Condition__c',
        'Genetic_Information__c', 'Marital_Status__c', 'Military_or_Veteran_Status__c'
    ]):
        incidents['discrimination'] = {
            'description': "Workplace discrimination based on protected characteristics",
            'details': {},
            'dates': [data.get('Termination_Date__c', '')]
        }
        
        # Add specific discrimination factors
        if data.get('Race_Color__c') == 1:
            incidents['discrimination']['details']['race'] = data.get('If_YES_to_Race_or_Color_why__c', '')
        if data.get('Religion__c') == 1:
            incidents['discrimination']['details']['religion'] = data.get('If_YES_to_Religion_why__c', '')
        if data.get('Sex_or_Gender__c') == 1:
            incidents['discrimination']['details']['gender'] = data.get('If_YES_to_Sex_Gender_why__c', '')
        if data.get('Sexual_Orientation__c') == 1:
            incidents['discrimination']['details']['sexual_orientation'] = data.get('If_YES_to_Sexual_Orientation_why__c', '')
    
    # Sexual harassment incident
    if data.get('Sexual_Harassment_Assault__c') == 'Yes':
        incidents['harassment'] = {
            'description': f"Sexual harassment: {data.get('Incident_Type__c', '')}",
            'perpetrator': data.get('Name_s_of_Perpetrator_s__c', ''),
            'perpetrator_role': data.get('Role_of_Perpetrator_s__c', ''),
            'location': data.get('Location_of_Incident__c', ''),
            'frequency': data.get('Frequency_Of_Incident__c', ''),
            'reported': data.get('Did_You_Report_The_Incident__c', 'No'),
            'witnesses': data.get('Key_Witnesses__c', 'No')
        }
    
    # Misclassification incident
    if data.get('X1099_Misclassification__c') == 'Yes':
        incidents['misclassification'] = {
            'description': "Employee misclassified as independent contractor",
            'details': data.get('X1099_Misclassification_Notes__c', ''),
            'dates': [data.get('Start_Date_of_Employment__c', ''), data.get('Last_Date_of_Employment__c', '')]
        }
    
    # Wrongful termination
    if data.get('Were_you_fired_or_did_you_resign__c') == 'Fired':
        incidents['wrongful_termination'] = {
            'description': "Wrongful termination",
            'date': data.get('Termination_Date__c', ''),
            'union_grievance': data.get('Union_Grievance__c', 'No')
        }
    
    # Rest break violations
    if data.get('Able_To_Take_Rest_Breaks__c') == 'No':
        incidents['rest_breaks'] = {
            'description': "Denial of legally required rest breaks",
            'hours_per_week': data.get('Hours_Worked_per_Week__c', 0)
        }
    
    # Leave violations
    if (data.get('Attempt_To_Take_Sick_Leave__c') == 'Yes' or 
        data.get('Attempt_to_Schedule_Medical_Family_Leave__c') == 'Yes'):
        incidents['leave_denial'] = {
            'description': "Denial of legally protected leave",
            'sick_leave': data.get('Attempt_To_Take_Sick_Leave__c', 'No'),
            'family_leave': data.get('Attempt_to_Schedule_Medical_Family_Leave__c', 'No')
        }
    
    # Add any general workplace conduct issues
    if data.get('Illegal_or_Unethical_Workplace_Conduct__c') == 'Yes':
        incidents['workplace_conduct'] = {
            'description': "Illegal or unethical workplace conduct"
        }
    
    return DemandLetterInfo(
        employee=employee,
        employer=employer,
        incidents=incidents,
        attorney_name="Hassan Halawi",
        attorney_email="hassanhalawi@legalcorner.com",
        attorney_phone="(818) 900-6255",
        settlement_demand=data.get("Settlement_Authority__c", 0)
    ) 