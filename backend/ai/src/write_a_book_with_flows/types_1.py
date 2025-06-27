from typing import List, Optional, Dict

from pydantic import BaseModel


class SectionOutline(BaseModel):
    title: str
    description: str


class DemandLetterOutline(BaseModel):
    sections: List[SectionOutline]


class Sections(BaseModel):
    title: str
    content: str


class EmployerInfo(BaseModel):
    name: str
    address: str


class EmployeeInfo(BaseModel):
    name: str
    position: str
    start_date: str
    end_date: Optional[str] = None
    address: str
    email: str
    phone: str
    hourly_rate: float
    weekly_hours: float


class IncidentInfo(BaseModel):
    description: str
    dates: List[str]
    witnesses: Optional[List[str]] = None
    evidence: Optional[List[str]] = None
    prior_complaints: Optional[List[str]] = None


class DemandLetterInfo(BaseModel):
    employer: EmployerInfo
    employee: EmployeeInfo
    incidents: Dict
    attorney_name: str
    attorney_email: str
    attorney_phone: str
    settlement_demand: float
    