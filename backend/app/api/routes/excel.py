from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import pandas as pd
from typing import Dict, Any, Optional
import chardet
import logging
import uuid
import os
import math
import tempfile
import json
from fastapi.concurrency import run_in_threadpool
import numpy as np
from datetime import datetime

router = APIRouter(tags=["Excel"])
logger = logging.getLogger(__name__)

# Store processing status and file paths
processing_files = {}  # UUID -> {"status": "processing|done", "file_path": path}


async def process_file_in_background(file_id: str, file_path: str, file_type: str):
    """Background task to process the file and save results as JSON"""
    try:
        # Read the file based on type
        na_values = ["", "null", "NULL", "na", "NA", "n/a", "N/A", "#N/A", 
                     "nan", "NaN", "None", "none", "NONE", "Null", "N.A.", 
                     "na.", "NA.", "n.a.", "N.A", "n.a", "undefined"]
        
        if file_type == "csv":
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            df = None
            
            for enc in encodings:
                try:
                    # Use na_values during loading to catch null values early
                    df = pd.read_csv(file_path, encoding=enc, na_values=na_values)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error with encoding {enc}: {str(e)}")
            
            if df is None:
                processing_files[file_id] = {
                    "status": "error", 
                    "error": "Unable to decode CSV with any encoding"
                }
                return
        else:
            # Excel file - use na_values during loading
            df = pd.read_excel(file_path, na_values=na_values)
        
        # Get total row count for pagination info
        # Special case for Excel files with columns that might be all null
        df = df.replace({pd.NA: None})
        df = df.replace({np.nan: None})
        
        # Convert directly to JSON string first (more reliable null handling)
        json_str = df.to_json(orient='records')
        # Then parse it back to get proper Python objects
        raw_data = json.loads(json_str)
        
        # Process each record to remove all null-like values
        # cleaned_data = []
        # for record in raw_data:
        #     # Only keep fields with actual values
        #     cleaned_record = {}
            
        #     for key, value in record.items():
        #         # Skip fields with None/null values
        #         if value is None:
        #             continue
                    
        #         # Handle string values
        #         if isinstance(value, str):
        #             # Skip if empty string or just whitespace
        #             if not value.strip():
        #                 continue
                        
        #             # Skip if it's any variation of null/na/etc.
        #             value_lower = value.lower()
        #             if any(null_str in value_lower for null_str in ["null", "na", "n/a", "none", "nan", "undefined"]):
        #                 continue
                
        #         # Skip explicit null in JSON
        #         if value == "null":
        #             continue
                    
        #         # For numeric values, keep them (including zero)
        #         cleaned_record[key] = value
                
        #     # Add the record to our cleaned data if it has any fields left
        #     if cleaned_record:
        #         cleaned_data.append(cleaned_record)
        
        # Log some debugging info
        # logger.info(f"File {file_id}: Cleaned {len(raw_data)} records to {len(cleaned_data)} records")
        # if raw_data and cleaned_data:
        #     logger.info(f"Sample raw fields: {list(raw_data[0].keys())[:5]}")
        #     logger.info(f"Sample cleaned fields: {list(cleaned_data[0].keys())[:5]}")
        
        # Save to a JSON file with the same ID
        json_dir = os.path.join(tempfile.gettempdir(), "excel_uploads")
        os.makedirs(json_dir, exist_ok=True)
        json_path = os.path.join(json_dir, f"{file_id}.json")
        
        # Save both the data and metadata
        result = {
            "data": raw_data,
            "pagination": {
                "total_rows": len(raw_data),
                "total_pages": math.ceil(len(raw_data) / 25)  # Default page size
            },
            "file_info": {
                "type": file_type,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Write with explicit encoding to avoid issues
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
        
        # Update status
        processing_files[file_id] = {
            "status": "done",
            "file_path": json_path
        }
        
        # Clean up the original uploaded file (not the processed JSON)
        if os.path.exists(file_path) and file_path != json_path:
            os.remove(file_path)
            
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {str(e)}", exc_info=True)
        processing_files[file_id] = {
            "status": "error",
            "error": str(e)
        }
        
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload", response_model=Dict[str, Any])
async def upload_excel_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    First step: Upload a file and return a processing ID immediately.
    
    The file will be processed in the background.
    Check the status with the /excel/status/{file_id} endpoint.
    """
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400, 
            detail="File must be Excel (.xlsx, .xls) or CSV (.csv)"
        )
    
    try:
        # Generate a unique ID for this file
        file_id = str(uuid.uuid4())[:8]
        
        # Get temporary directory
        temp_dir = tempfile.gettempdir()
        
        # Determine file type
        if file.filename.endswith('.csv'):
            file_type = "csv"
            file_ext = ".csv"
        else:
            file_type = "excel"
            file_ext = ".xlsx"
        
        # Save the uploaded file to a temporary file
        temp_file_name = f"{file_id}{file_ext}"
        temp_file_path = os.path.join(temp_dir, temp_file_name)
        
        # Create a temp file
        with open(temp_file_path, "wb") as temp_file:
            # Process in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)
        
        # Register file as processing
        processing_files[file_id] = {
            "status": "processing",
            "file_path": temp_file_path
        }
        
        # Start background task to process the file
        background_tasks.add_task(
            process_file_in_background,
            file_id=file_id,
            file_path=temp_file_path,
            file_type=file_type
        )
        
        # Return immediately with the file ID
        return {
            "file_id": file_id,
            "status": "processing",
            "message": "File upload received. Processing started."
        }
    
    except Exception as e:
        logger.error(f"Error initiating file processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/status/{file_id}", response_model=Dict[str, Any])
async def check_file_status(
    file_id: str,
    page: int = Query(1, description="Page number for paginated results"),
    page_size: int = Query(25, description="Number of records per page")
):
    """
    Second step: Check the status of a file processing task.
    
    If processing is complete, returns the processed data.
    If still processing, returns a status message.
    """
    # Check if file ID exists
    if file_id not in processing_files:
        # Try to recover the file directly from temp directory
        json_dir = os.path.join(tempfile.gettempdir(), "excel_uploads")
        json_path = os.path.join(json_dir, f"{file_id}.json")
        
        if os.path.exists(json_path):
            processing_files[file_id] = {
                "status": "done",
                "file_path": json_path
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="File ID not found. The file may have been processed and cleaned up."
            )
    
    # Get file status
    file_info = processing_files[file_id]
    
    # If still processing
    if file_info["status"] == "processing":
        return {
            "file_id": file_id,
            "status": "processing",
            "message": "File is still being processed. Please try again later."
        }
    
    # If processing failed
    if file_info["status"] == "error":
        error_msg = file_info.get("error", "Unknown error occurred")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {error_msg}"
        )
    
    # If done, return the data
    try:
        if not os.path.exists(file_info["file_path"]):
            raise HTTPException(
                status_code=404,
                detail="Processed file not found. It may have been deleted due to storage cleanup."
            )
            
        with open(file_info["file_path"], 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Extract data for pagination
        data = result["data"]
        total_rows = len(data)
        
        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        # Return paginated data
        return {
            "file_id": file_id,
            "status": "done",
            "data": data[start_idx:end_idx],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": math.ceil(total_rows / page_size)
            },
            "file_info": result["file_info"]
        }
    
    except Exception as e:
        logger.error(f"Error retrieving processed file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving processed file: {str(e)}"
        )
