from fastapi import APIRouter, Body, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from pydantic import BaseModel, Field

# Add AI module path
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))\
    .parent.parent.parent
AI_DIR = BASE_DIR / "ai"
sys.path.insert(0, str(AI_DIR))
# Add base dir to path to ensure proper imports
sys.path.insert(0, str(BASE_DIR))  

# Need to import after modifying sys.path
from ai.src.write_a_book_with_flows.main import DemandLetterFlow  # noqa: E402

router = APIRouter()
logger = logging.getLogger(__name__)

# Dictionary to track letter generation status
letter_status = {}





# Define validation models
class ContactInfo(BaseModel):
    # Add required fields for contact info
    phone: str = Field(...)
    email: str = Field(...)
    address: str = Field(...)


class WorkSchedule(BaseModel):
    # Add required fields for work schedule
    days: List[str] = Field(...)
    start_time: str = Field(...)
    end_time: str = Field(...)


class EmployeeInfo(BaseModel):
    name: str = Field(...)
    position: str = Field(...)
    weekly_hours: float = Field(...)
    work_location: str = Field(...)
    pay_rate: float = Field(...)
    work_schedule: WorkSchedule = Field(...)
    contact_info: ContactInfo = Field(...)


def generate_demand_letter_task(data: Dict[str, Any], file_id: str):
    """Background task to generate the demand letter"""
    try:
        # Save the received data to a temporary JSON file
        temp_dir = Path("./temp")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / f"{file_id}.json"
        with open(temp_file, "w") as f:
            json.dump(data, f)
        
        # Set status to in progress
        letter_status[file_id] = "in_progress"
        
        try:
            # Initialize DemandLetterFlow
            letter_flow = DemandLetterFlow()
            
            # Set up arguments like the CLI would
            letter_flow.state.output_file_id = file_id
            letter_flow.args = type('Args', (), {
                'data_file': str(temp_file.absolute()),
                'output_id': file_id
            })
            
            # Add logging to debug the data structure
            logger.info(f"Input data structure: {json.dumps(data, indent=2)}")
            
            # Run the flow using the async method
            letter_flow.kickoff()
            letter_status[file_id] = "completed"
            
        except Exception as e:
            logger.error(f"Error in AI module: {str(e)}")
            letter_status[file_id] = "failed"
            
    except Exception as e:
        logger.error(f"Exception during demand letter generation: {str(e)}")
        letter_status[file_id] = "failed"


@router.post("/generate_demand_letter/")
async def generate_demand_letter(
    background_tasks: BackgroundTasks,
    data: Dict[str, Any] = Body(...)
):
    """
    Endpoint to receive client data and start background demand letter 
    generation. Returns a file_id that can be used to retrieve the letter later
    """
    # Generate a short UUID for this request
    file_id = generate_short_uuid()
    

    
    # Initialize status
    letter_status[file_id] = "in_progress"
    
    # Return the file_id immediately
    return {"file_id": file_id, "status": "in_progress"}


@router.get("/demand_letter/{file_id}")
async def get_demand_letter(file_id: str):
    """
    Retrieve a generated demand letter by its file_id
    Returns the letter content if ready, otherwise the current status
    """
    # Check if the file_id exists in our tracking dictionary
    if file_id not in letter_status:
        raise HTTPException(status_code=404, detail="Demand letter not found")
    
    status = letter_status[file_id]
    
    if status == "in_progress":
        return {
            "status": "in_progress",
            "message": "Demand letter is still being generated"
        }
    
    if status == "failed":
        return {
            "status": "failed", 
            "message": "Demand letter generation failed"
        }
    
    # If completed, try to return the file
    letter_path = Path(f"./{file_id}.md")
    
    if not letter_path.exists():
        # Check the AI output directory as fallback
        letter_path = Path(f"../ai/{file_id}.md")
        if not letter_path.exists():
            return {
                "status": "error",
                "message": (
                    "Demand letter file not found even though "
                    "generation was marked complete"
                )
            }
    
    # Read and return the letter content
    with open(letter_path, "r") as f:
        letter_content = f.read()
    
    return {
        "status": "completed", 
        "file_id": file_id, 
        "content": letter_content
    }
