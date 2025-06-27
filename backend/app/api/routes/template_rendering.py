from fastapi import APIRouter, Body, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any, List
import uuid
from pathlib import Path
from docxtpl import DocxTemplate
from datetime import datetime, timedelta
from app.api.deps import run_openai_model, run_openai_model_for_factual_allegations
from app.api.prompts import gender_prompt, claims_prompt, factual_allegations_prompt, damages_calculation_prompt
import re

router = APIRouter()


def generate_short_uuid():
    """Generate a short UUID for file identification"""
    return str(uuid.uuid4())[:8]
def get_date_three_weeks_later():
    """Return a date 3 weeks from current date in format 'Month DD, YYYY'"""
    future_date = datetime.now() + timedelta(weeks=3.0)
    return future_date.strftime("%B %d, %Y")

def settelment_calculation(damages_data):
    """Calculate the settlement amount for the client"""
    total_damages = damages_data.get('Total', '')
    total_damages = float(total_damages.replace('$', '').replace(',', ''))
    settlement_amount = 0
    if total_damages > 1000000:
        settlement_amount = total_damages - 25000
    else:
        settlement_amount = total_damages - 5000
    
    settlement_amount = "${:,.2f}".format(settlement_amount)
    return settlement_amount, total_damages






damages_1 = """
At this stage of the case, and in an effort to reach a resolution before engaging in costly and time-consuming litigation,honerif_ics. client_full_name has authorized our office to extend a settlement offer of settelment_amount to resolve their claims. As liability becomes clearer and witness testimony is further established, the value of this case will undoubtedly rise, leading to increased demands, along with accumulating attorneys' fees.
"""

damages_2 = """
At this point in the case, in an effort to resolve the matter before entering into costly and time-consuming litigation, honerif_ics. client_full_name has authorized our office to propose that both parties engage in a half-day mediation. The mediators I typically work with have a 90% success rate in settling cases like this, which can save both sides considerable resources that would otherwise be spent on litigation. I believe it would be more cost-effective for the Defendant to address its liability before the trial preparation and depositions begin. In fact, accumulating defense costs may encourage settlement discussions sooner rather than later.
"""



def create_document(file_id: str, data: Dict[str, Any]):

    # Load the template
    template_path = Path(__file__).parent.parent.parent.parent / "files" / "template.docx"
    print(f"the template_path is {template_path}")
    template = DocxTemplate(str(template_path))
    gender = run_openai_model(gender_prompt, str(data), "gpt-4o", 0.3)
    gender = gender.get('gender', '')
    if gender.lower() == "male":
        gender = "his"
        honerif_ics = "Mr"
    elif gender.lower() == "female":
        gender = "her"
        honerif_ics = "Ms"
    else:
        gender = "their"
        honerif_ics = "Mx"
    claims = run_openai_model(claims_prompt, str(data), "gpt-4o", 0.3)
    claims = claims.get('claims', '')
    paragraphs = populate_claims_paragraphs(claims)
    claims_text = ""
    for i, claim in enumerate(claims):
        claims_text += f"{i+1}. {claim}\n"
    # Define the context with sample data - use data if provided
    factual_allegations = run_openai_model_for_factual_allegations(factual_allegations_prompt, str(data) + str(claims_text), "gpt-4o", 0.8)
    damages_calculation = run_openai_model(damages_calculation_prompt, str(data) + str(claims_text), "gpt-4o", 0.5)
    
    # Create local copies of the damages templates
    damages_1_text = damages_1.replace("honerif_ics", honerif_ics)
    damages_1_text = damages_1_text.replace("client_full_name", data.get('Client_Name__c', ''))
    damages_1_text = damages_1_text.replace("settelment_amount", settelment_calculation(damages_calculation)[0])
    
    damages_2_text = damages_2.replace("honerif_ics", honerif_ics)
    damages_2_text = damages_2_text.replace("client_full_name", data.get('Client_Name__c', ''))
    
    context = {
        "top_date": datetime.now().strftime("%B %d, %Y"),
        "oc_defendant_name": data.get('Name_Of_Employer__c', ''),
        "defendant_street_address": data.get('Employer_Address__Street__s', ''),
        "defendant_state_address": f"{data.get('Employer_Address__City__s', '') or ''} {data.get('Employer_Address__StateCode__s', '') or ''} {data.get('Employer_Address__PostalCode__s', '') or ''}".strip(),
        'client_full_name': data.get('Client_Name__c', ''),
        "client_subjective": gender,
        "honerif_ics": honerif_ics,
        "last_name": data.get('Client_Last_Name__c', ''),
        "start_date": format_date(data.get('Start_Date_of_Employment__c', '')),
        "end_date": format_date(data.get('Last_Date_of_Employment__c', '')),
        "job_title": data.get('Position_Title__c', ''),
        "wage": "hourly" if data.get('Hourly_Rate__c') else "Annual Salary",
        "pay_rate": data.get('Hourly_Rate__c', '') or data.get('Annual_Salary__c', ''),
        "three_weeks_later": get_date_three_weeks_later(),
        "paragraph_wrongful_termination": data.get('Paragraph_Wrongful_Termination__c', ''),
        "paragraph_labor_code_violations": data.get('Paragraph_Labor_Code_Violations__c', ''),
        "paragraphs": paragraphs,
        "factual_allegations": factual_allegations,
        "claims": claims_text,
        "total_damages": damages_calculation.get('Total', ''),
        "lost_wages": damages_calculation.get('Lost_Wages', ''),
        "emotional_distress_damages": damages_calculation.get('Emotional_Distress_Damages', ''),
        "waiting_time_penalties": damages_calculation.get('Waiting_Time_Penalties', ''),
        "attorney_fees_and_costs": damages_calculation.get('Attorney_Fees_and_Costs', ''),
        "punitive_damages": damages_calculation.get('Punitive_Damages', ''),
        "settlement_amount": settelment_calculation(damages_calculation)[0],
        "damages_1": damages_1_text if settelment_calculation(damages_calculation)[1] < 1000000 else "",
        "damages_2": [damages_1_text, damages_2_text] if settelment_calculation(damages_calculation)[1] > 1000000 else ""
    }

    
    # print(f"the context is {context}")

    # Render the template with the context
    template.render(context)

    # Save the new document
    output_path = Path(__file__).parent.parent.parent.parent / "files" / "output_files" / f"{file_id}.docx"
    template.save(str(output_path))

    print(f"Document generated successfully! Check '{file_id}.docx'.")





def populate_claims_paragraphs(calims_headings: List[str]):
    
    all_paragraphs = ""
    for i, heading in enumerate(calims_headings):
        # Remove numbers followed by a period at the beginning of the sentence
        heading = re.sub(r'^\d+\.\s*', '', heading)
        all_paragraphs += f"{heading}: \n{original_claims_paragraphs.get(f'{heading}', '')}\n\n"
    
        # paragraph = {f"h1": heading,"paragraph": original_claims_paragraphs.get(f"{heading}", "")}
        # claim_paragraphs.append(paragraph)
    # print(f"the claim_paragraphs are {claim_paragraphs}")
    return all_paragraphs

def format_date(date_str):
    """Format date from ISO format to Month Day, Year format"""
    if not date_str:
        return ''
    
    # List of possible date formats to try
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 2025-04-19 00:00:00
        '%Y-%m-%d',           # 2025-04-19
        '%d/%m/%Y %H:%M',     # 19/09/2023 0:00
        '%d/%m/%Y',           # 19/09/2023
        '%m/%d/%Y %H:%M:%S',  # 04/19/2025 00:00:00
        '%m/%d/%Y %H:%M',     # 04/19/2025 00:00
        '%m/%d/%Y',           # 04/19/2025
        '%d-%m-%Y %H:%M:%S',  # 19-04-2025 00:00:00
        '%d-%m-%Y %H:%M',     # 19-04-2025 00:00
        '%d-%m-%Y',           # 19-04-2025
        '%Y/%m/%d %H:%M:%S',  # 2025/04/19 00:00:00
        '%Y/%m/%d',           # 2025/04/19
        '%d.%m.%Y %H:%M:%S',  # 19.04.2025 00:00:00
        '%d.%m.%Y',           # 19.04.2025
        '%b %d, %Y',          # Apr 19, 2025
        '%B %d, %Y',          # April 19, 2025
        '%d %b %Y',           # 19 Apr 2025
        '%d %B %Y'            # 19 April 2025
    ]
    
    for date_format in formats:
        try:
            # Try to parse with current format
            date_obj = datetime.strptime(date_str, date_format)
            # Format to Month Day, Year
            return date_obj.strftime('%B %d, %Y')
        except ValueError:
            continue
    
    # If no format matches, return the original
    return date_str


@router.post("/render_template/")
async def render_template(
    background_tasks: BackgroundTasks,
    data: Dict[str, Any] = Body(...)
):
    """
    Endpoint to receive client data and start background template rendering. 
    Returns a file_id that can be used to retrieve the rendered template later
    """
    # # Generate a short UUID for this request
    file_id = generate_short_uuid()
    
    
    background_tasks.add_task(create_document, file_id, data)

    # # Return the file_id immediately
    # return claims_paragraphs
    return {"file_id": file_id, "status": "in_progress"}
    # return run_openai_model(claims_prompt,str(data), "gpt-4o", 0.3)
    # return run_openai_model(str(data), "gpt-4o", 0.3)


@router.get("/get_rendered_template/{file_id}")
async def get_rendered_template(file_id: str):
    """
    Endpoint to retrieve the rendered template
    """
    output_path = Path(__file__).parent.parent.parent.parent / "files" / "output_files" / f"{file_id}.docx"
    print(f"Checking for file at: {output_path}")
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        return FileResponse(
            path=str(output_path), 
            filename=f"{file_id}.docx",
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")


claims_dict = {
    "h1": "Retaliation in Violation of Labor Code Section 98.6",
    "2": "Retaliation in Violation of Labor Code Section 1102.5",
    "3": "Harassment in Violation of FEHA",
    "4": "Discrimination in Violation of FEHA",
    "5": "Retaliation in Violation of FEHA",
    "6": "Failure to Accommodate in Violation of FEHA",
    "7": "Failure to Engage in the Good Faith Interactive Process in Violation of FEHA",
    "8": "Wrongful Termination in Violation of Public Policy",
    "9": "Failure to Provide Earned/Overtime Wages",
    "10": "Failure to Pay Wages Due Upon Termination; Waiting Time Penalties",
    "11": "Failure to Issue Accurate and Itemized Wage Statements",   
}

original_claims_paragraphs = {
    "Retaliation in Violation of Labor Code Section 98.6": "Labor Code §98.6 states, \"A person shall not discharge an employee or in any manner discriminate, retaliate, or take any adverse action against any employee or applicant for employment because the employee or applicant engaged in any conduct delineated in this chapter, including… or because the employee or applicant for employment has filed a bona fide complaint or claim or instituted or caused to be instituted any proceeding under or relating to his or her rights that are under the jurisdiction of the Labor Commissioner, made a written or oral complaint that he or she is owed unpaid wages, or because the employee has initiated any action or notice pursuant to Section 2699, or has testified or is about to testify in a proceeding pursuant to that section, or because of the exercise by the employee or applicant for employment on behalf of himself, herself, or others of any rights afforded him or her.\"",
    "Retaliation in Violation of Labor Code Section 1102.5": "Labor Code §1102.5 prohibits retaliation by an employer against an employee for disclosing any information to any person with authority to investigate, or any public body investigating, violation of a state or federal statute or regulation if the employee has reasonable cause to believe that the information discloses a violation of state or federal statute, or a violation of or noncompliance with a local, state, or federal rule or regulation. \n\"In order to establish a prima facie case of retaliation against an employee under the California Fair Employment and Housing Act (Gov. Code, § 12900 et seq.), a plaintiff must show (1) he or she engaged in a protected activity, (2) the employer subjected the employee to an adverse employment action, and (3) a causal link existed between the protected activity and the employer's action.\" (Yanowitz v. L'Oreal USA, Inc. (2005) 36 Cal.4th 1028).\nIn order to establish a prima facie case of retaliation under § 1102.5(b), plaintiff must demonstrate that he or she engaged in a protected activity as set forth in § 1102.5, that the employer subjected him or her to an adverse employment action, and a causal link between the two. (McVeigh v. Recology San Francisco (2013) 213 Cal.App.4th443,468). A Plaintiff who successfully prosecutes for retaliation in violation of § 1102.5 may recover compensatory damages, including economic and emotional distress damages. (Gardenhire v. Housing Authority of the City of Los Angeles (2000) 85 Cal.App.4th 236,237, 240-241).",
    "Harassment in Violation of FEHA": "In order to prevail on a hostile work environment claim, plaintiff must show that his 'workplace was permeated with discriminatory intimidation . . . that was sufficiently severe or pervasive to alter the conditions of his employment and create an abusive working environment.' Harris, 510 U.S. at 21, 114 S.Ct. 367. Furthermore, courts evaluate the totality of the circumstances test to determine whether a plaintiff's allegations make out a colorable claim of a hostile work environment. In Harris, the court listed frequency, severity and the level of interference with work performance among the factors particularly relevant to the inquiry. When assessing the objective portion of a plaintiff's claim, courts assume the perspective of the reasonable victim. See Ellison v. Brady, 924 F.2d 872, 879 (9th Cir. 1991).Every individual is entitled to work in a harassment-free environment and an employer's failure or refusal to provide this, in and of itself, is the denial of 'terms, conditions, privileges of employment' and is a violation of the law. (Government Code Sections 12940, et seq.; 2 Cal. Admin. Code 7287.6; DFEH v. Fresno Hilton Hotel, (1984) FEHC Dec. No. 84-03, p. 29; and see also Harris v. Forklift Systems, Inc. (1993) 114 S.Ct. 367.Although FEHA Section 12940(j)(1) prohibits any 'person' from harassing an employee, FEHA Section 12940(k) imposes on the employer the duty to take all reasonable steps to prevent this harassment (as well as discrimination) from occurring in the first place and to take immediate and appropriate action when it is or it should be aware of the unlawful conduct. Carrisales v. Department of Corrections (1999) 21 Cal.4th 1132, 1140. To establish harassment under FEHA, an employee must demonstrate: (1) membership in a protected group, (2) that she was subjected to harassment because she belonged to this group, and (3) the alleged harassment was so severe that it created a hostile work environment.",
    "Discrimination in Violation of FEHA": "California Government Code §12940(a) (the Fair Employment and Housing Act, or \"FEHA\") provides that it is unlawful employment practice \"[f]or an employer because of the race, religious creed, color, national origin, ancestry, physical disability, mental disability, medical condition, genetic information, marital status, sex, gender, gender identity, gender expression, age, sexual orientation, or military and veteran status of any person…to discriminate against the person in compensation or in terms, conditions, or privileges of employment.\"\n\nCalifornia uses a three-stage test, established in McDonnell Douglas Corp. v. Green (1973) 411 U.S. 792, to resolve discrimination cases. Once the employee establishes a prima facie case of discrimination using the three-stage test, a presumption of discrimination is established, shifting the burden to the employer to show that the action was motivated by legitimate, non-discriminatory reasons. If the employer meets this burden, the burden shifts to the employee to show that the employer's reasons are pretext for discrimination or to produce evidence of intentional discrimination. Guz v. Bechtel (2000) 24 Ca1.4th 317,354-356.\n\nTo establish a prima facie case of discrimination under FEHA, the plaintiff must provide evidence that (1) he was a member of a protected class, (2) he was qualified for the position she sought or was performing competently in the position she held, (3) he suffered an adverse employment action, such as termination, demotion, or denial of an available job, and (4) some other circumstance suggests discriminatory motive. Guz v. Bechtel (2000) 24 Ca1.4th at 355.",
    "Retaliation in Violation of FEHA": "California Government Code §12940(a) (the Fair Employment and Housing Act or \"FEHA\") states, \"It is unlawful employment practice… for an employer because of the race, religious creed, color, national origin, ancestry, physical disability, mental disability, medical condition, genetic information, marital status, sex, gender, gender identity, gender expression, age, sexual orientation, or military and veteran status of any person…to discriminate against the person in compensation or in terms, conditions, or privileges of employment.\"",
    "Failure to Accommodate in Violation of FEHA": "Government Code §12940(m)(1) provides that it is an unlawful employment practice \"For an employer or other entity covered by this part to fail to make reasonable accommodation for the known physical or mental disability of an applicant or employee. Any employer or other covered entity shall make reasonable accommodation to the disability of any individual with a disability if the employer or other covered entity knows of the disability, unless the employer or other covered entity can demonstrate that the accommodation would impose an undue hardship.\" (Cal. Code Regs., tit. 2, §7293.9.)\n\nGovernment Code §12926(n) states, \"Reasonable accommodation\" may include restructuring, part-time or modified work schedules, reassignment to a vacant position, acquisition or modification of equipment or devices, adjustment or modifications of examinations, training materials or policies, the provision of qualified readers or interpreters, and other similar accommodations for individuals with disabilities.\n\nGovernment Code §12940(m)(2) makes it unlawful \"for an employer or other entity covered by this part to, in addition to the employee protections provided pursuant to subdivision (h), retaliate or otherwise discriminate against a person for requesting accommodation under this subdivision, regardless of whether the request was granted.\" The Fair Employment and Housing Commission's regulations provide that \"it is unlawful for an employer or other covered entity to demote, suspend [...], fail to give equal consideration in making employment decisions, [...], adversely affect working conditions or otherwise deny any employment benefit to an individual because that individual has opposed practices prohibited by the Act [...].\" Cal. Code Regs., tit. 2, § 7287.8(a).",
    "Failure to Engage in the Good Faith Interactive Process in Violation of FEHA": "Government Code §12940(n) provides that it is an unlawful employment practice \"[f]or an employer or other entity covered by this part to fail to engage in a timely, good faith, interactive process with the employee or applicant to determine effective reasonable accommodations, if any, in response to a request for reasonable accommodation by an employee or applicant with a known physical or mental disability or known medical condition.\"\n\nA plaintiff has a prima facie case for failure to engage in the interactive process when she (1) was an employee of or seeking employment with the defendant; (2) she had a disability or limitation that was known to the defendant; (3) she requested a reasonable accommodation from her employer or potential employer so that she would be able to perform her job; (4) she was willing to participate in an interactive process to determine whether a reasonable accommodation could be made; and 5) the defendant failed to participate in a timely good faith interactive process with the plaintiff. See, e.g., Judicial Council of California Civil Jury Instructions (2017).",
    "Wrongful Termination in Violation of Public Policy": "\"[W]hen an employer's discharge of an employee violates fundamental principles of public policy, the discharged employee may maintain a tort action and recover damages traditionally available in such actions.\" Tameny v. Atlantic Richfield Co. (1980) 27 Cal.3d 167, 170. \"[T]he cases in which violations of public policy are found generally fall into four categories: (1) refusing to violate a statute; (2) performing a statutory obligation (3) exercising a statutory right or privilege; and (4) reporting an alleged violation of a statute of public importance.\" Gantt v. Sentry Insurance (1992) 1 Cal.4th 1083, 1090-1091.\n\nDamages for wrongful termination in violation of California public policy are calculated based on the following: front pay, which is the present cash value of any future wages and benefits that the employee would have earned for the length of time the employment would have been reasonably certain to continue, back pay, which is what employee would have earned up to today, including any benefits and pay increases, and emotional distress damages.",
    "Failure to Provide Earned/Overtime Wages": "Labor Code § 1197 requires that all employees be paid at least the minimum wage set by applicable state or local law. Labor Code § 1197.1 provides, \"1) For any initial violation that is intentionally committed, one hundred dollars ($100) for each underpaid employee for each pay period for which the employee is underpaid. This amount shall be in addition to an amount sufficient to recover underpaid wages. (2) For each subsequent violation for the same specific offense, two hundred fifty dollars ($250) for each underpaid employee for each pay period for which the employee is underpaid regardless of whether the initial violation is intentionally committed. This amount shall be in addition to an amount sufficient to recover underpaid wages. (3) Wages recovered pursuant to this section shall be paid to the affected employee.\"\n\nUnpaid Wages/Overtime Wages\nAn employer is required to pay an employee for all hours worked. \"Hours worked\" means the time during which an employee is subject to the control of an employer and includes all the time the employee is suffered or permitted to work, whether or not required to do so.\n\nPursuant to the applicable IWC Wage Orders, and California Code of Regulations, Title 8, Section 11010 no employee shall be employed for more than eight hours in any workday or forty hours in any workweek unless the employee receives overtime wages. Employment beyond eight hours in any workday or more than six days in any workweek is permissible provided the employee is compensated for such overtime at not less than: 1) One and one-half times the hourly rate of pay for all hours worked in excess of eight (8) hours per day, forty (40) hours per week, and/or the first eight (8) hours of the seventh consecutive workday; and twice times the rate of pay for all hours worked in excess of twelve (12) hours per day and/or eight (8) hours on the seventh consecutive workday; and 2) Double the employee's regular rate of pay for all hours worked in excess of twelve (12) hours in any workday and for all hours worked in excess of eight (8) hours on the seventh consecutive day of work in a workweek. Labor Code § 510.",
    "Failure to Pay Wages Due Upon Termination; Waiting Time Penalties": "Labor Code § 1194.2 provides that in an action \"to recover wages because of the payment of a wage less than the minimum wage fixed by an order of the commission or by statute, an employee shall be entitled to recover liquidated damages in an amount equal to the wages unlawfully paid and interest thereon.\"\n\nFor every pay period that the total paid by Defendant in wages and/or commissions is not equal to or greater than the applicable minimum wage, Plaintiff is owed not only the unpaid wages but also liquidated damages in an amount equal to the unpaid wages.",
    "Failure to Issue Accurate and Itemized Wage Statements": "Labor Code §201 provides, \"If an employer discharges an employee, the wages earned and unpaid at the time of discharge are due and payable immediately.\"\n\nIn Smith v. L'Oreal USA, Inc. (2006) 39 Cal.4th 77, the California Supreme Court emphasized the importance of paying California employees promptly, as follows:\n\n\"Delay of payment or loss of wages results in deprivation of the necessities of life, suffering inability to meet just obligations to others, and, in many cases may make the wage-earner a charge upon the public.' (Citation.) California has long regarded the timely payment of employee wage claims as indispensable to the public welfare: It has long been recognized that wages are not ordinary debts, that they may be preferred over other claims, and that, because of the economic position of the average worker and, in particular, his dependence on wages for the necessities of life for himself and his family, it is essential to the public welfare that he receive his pay when it is due.\" (Citations.)\n\nFailing to immediately pay an employee's wages upon termination is an expensive violation. If upon termination the employer does not immediately pay an employee what he or she is owed, Labor Code §203 imposes upon the employer a severe penalty. Labor Code §203 provides:\n\n\"If an employer willfully fails to pay, without abatement or reduction, in accordance with Sections 201…, any wages of an employee who is discharged or who quits, the wages of the employee shall continue as a penalty from the due date thereof at the same rate until paid or until an action therefor is commenced; but the wages shall not continue for more than 30 days. The word 'willful' does not require proof of a deliberate evil purpose' on the part of the employer. Barnhill v. Robert Saunders & Co. (1981) 125 Cal.App.3d 1. 'Willful' merely means the employer intentionally failed or refused to perform an act which was required to be done.' Id. at 7. Once a court determines wages are late, penalties are imposed without much regard for an employer's argument its failure to pay was not willful.\"",
    "Failure to Provide Meal Periods": "In Brinker Restaurant Corp. v. Superior Court (2012) 53 Cal.4th 1004, the California Supreme Court held that a California employer must ensure that its employees are actually free of job duties and must provide the opportunity for employees to take a full, uninterrupted off-duty meal period. The Court was unequivocal in specifying that an employer only satisfies this obligation if it relieves its employees of all duty, relinquishes control over their activities and permits them a reasonable opportunity to take an uninterrupted 30-minute break, and does not impede or discourage them from doing so. A discernable piece of evidence must be shown to prove an employer did not impair or impede an employee's meal period. Additionally, if the employee works over ten (10) hours she is entitled to a second timely uninterrupted meal period, subject to the same penalties. In describing and defining \"impede or discourage,\" the Brinker Court recommended that employers adopt formal policies and practices to ensure scheduled meal periods and not use common scheduling that makes it difficult for employees to take breaks but rather to have overlapping schedules where one employee covers for others and to not write up, reprimand or ridicule employees that took breaks when it was their break times. There remain several cases proving meal period violations based on employers' practice to implicitly or explicitly coerce employees not to take their meal periods. Cicairos v. Summit Logistics, Inc. (2005) 133 Cal.App.4th 949; Jaimez v. DAIOHS USA Inc. (2010) 181 Cal.App.4th 1286; and Dilts v. Penske Logistics, LLC, 267 F.R.D. 625, 638 (S.D.Cal.2010). Thus, a meal period violation will occur if the employer does not ensure an employee is free from their job duties.",
    "Failure to Provide Rest Breaks": "Labor Code §226.7 requires that an employer must provide its employees with a ten-minute duty-free rest break commencing in the middle of a four-hour shift. Labor Code §§ 226.7, IWC Wage Order. Failure to authorize or permit employees to take ten-minute rest breaks similarly triggers another obligation to pay one-hour's pay to that employee. Section 12 of the Industrial Welfare Commission Wage Orders requires that:",
    "Failure to Indemnify": "Labor Code § 2802(a) states, \"An employer shall indemnify his or her employee for all necessary expenditures or losses incurred by the employee in direct consequence of the discharge of his or her duties, or of his or her obedience to the directions of the employer, even though unlawful, unless the employee, at the time of obeying the directions, believed them to be unlawful.\" This Labor Code section requires employers to reimburse employees for all out-of-pocket expenses the employee incurs during the performance of their job. See Cochran v. Schwan's Home Services (2014) 228 CA.App.4th 1137"
}




# 6.Failure to Accommodate in Violation of FEHA 
# 7.Failure to Engage in the Good Faith Interactive Process in Violation of FEHA
# 8.Wrongful Termination in Violation of Public Policy
# 9.Failure to Provide Earned/Overtime Wages
# 10.Failure to Pay Wages Due Upon Termination; Waiting Time Penalties 
# 11.Failure to Issue Accurate and Itemized Wage Statements
# 12.Failure to Provide Meal Periods
# 13.Failure to Provide Rest Breaks
# Failure to Indemnify
