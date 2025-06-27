#!/usr/bin/env python
import asyncio
import os
import sys
import json
import argparse
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from ai.src.write_a_book_with_flows.crews.write_book_chapter_crew.write_book_chapter_crew import (
    WriteDemandLetterSectionCrew,
)
from ai.src.write_a_book_with_flows.types_1 import Sections, SectionOutline, DemandLetterInfo
from ai.src.write_a_book_with_flows.info_collector import collect_demand_letter_info, load_from_file
from ai.src.write_a_book_with_flows.data_processor import process_salesforce_data

from ai.src.write_a_book_with_flows.crews.outline_book_crew.outline_crew import OutlineCrew


class DemandLetterState(BaseModel):
    title: str = (
        "Demand Letter"
    )
    demand_letter: List[Sections] = []
    demand_letter_outline: List[SectionOutline] = []
    topic: str = (
        "A comprehensive demand letter for legal violations"
    )
    goal: str = """
        The goal of this demand letter is to formally address serious workplace 
        violations by the employer against the employee. This letter will be drafted by 
        a third-party attorney representing the employee's interests. 
        The letter will document unsafe working conditions, detail unauthorized 
        and unexplained payment issues or wage violations, and outline the legal 
        obligations the employer has failed to meet. This comprehensive demand letter will 
        establish a clear timeline of events, cite relevant labor laws and 
        regulations that have been violated, and specify the remedies being 
        sought including back pay, damages, and workplace safety improvements.
    """
    letter_info: DemandLetterInfo = None
    output_file_id: str = None


class DemandLetterFlow(Flow[DemandLetterState]):

    @start()
    def collect_information(self):
        """Collect employer and employee information for the demand letter"""
        print("Starting Demand Letter Generation Process")
        
        # Check if we're processing data from an API call with file path
        if self.state.output_file_id and os.path.exists(self.args.data_file):
            print(f"Processing data from file: {self.args.data_file}")
            with open(self.args.data_file, 'r') as f:
                salesforce_data = json.load(f)
                
            # Process the Salesforce data into our letter_info format
            letter_info = process_salesforce_data(salesforce_data)
            self.state.letter_info = letter_info
            
            # Update the title with output_file_id
            self.state.title = f"Demand Letter {self.state.output_file_id}"
            
            # Update the topic with employer/employee names
            self.state.topic = (
                f"A comprehensive demand letter for {letter_info.employee.name} "
                f"against {letter_info.employer.name}"
            )
            return
        
        # # First, try to load existing information
        # loaded_info = load_from_file()
        
        # if loaded_info:
        #     use_existing = input("\nExisting information found. Would you like to use it? (y/n): ").strip().lower()
        #     if use_existing == 'y':
        #         self.state.letter_info = loaded_info
                
        #         # Update the title and topic with actual names
        #         self.state.title = f"{self.state.letter_info.employer.name} vs {self.state.letter_info.employee.name}"
        #         self.state.topic = f"A comprehensive demand letter for {self.state.letter_info.employee.name} against {self.state.letter_info.employer.name}"
        #         return
        
        # # If no existing info or user doesn't want to use it, collect new info
        # letter_info = collect_demand_letter_info()
        # self.state.letter_info = letter_info
        
        # Update the title and topic with actual names
        # self.state.title = f"{letter_info.employer.name} vs {letter_info.employee.name}"
        # self.state.topic = f"A comprehensive demand letter for {letter_info.employee.name} against {letter_info.employer.name}"
    @listen(collect_information)
    def generate_letter_outline(self):
        print("Kickoff the Demand Letter Outline Crew")
        
        # Include employee and employer info in the inputs
        employer_info = self.state.letter_info.employer.model_dump_json() if self.state.letter_info else "{}"
        employee_info = self.state.letter_info.employee.model_dump_json() if self.state.letter_info else "{}"     
        output = (
            OutlineCrew()
            .crew()
            .kickoff(inputs={
                "topic": self.state.topic, 
                "goal": self.state.goal,
                "employer_info": employer_info,
                "employee_info": employee_info,
                "incidents_info": self.state.letter_info.incidents
            })
        )

        sections = output["sections"]
        print("Sections:", sections)

        self.state.demand_letter_outline = sections

    @listen(generate_letter_outline)
    async def write_sections(self):
        print("Writing Demand Letter Sections")
        tasks = []

        async def write_single_section(section_outline):
            # Include employee and employer info in the inputs
            employer_info = self.state.letter_info.employer.model_dump_json() if self.state.letter_info else "{}"
            employee_info = self.state.letter_info.employee.model_dump_json() if self.state.letter_info else "{}"
            
            output = (
                WriteDemandLetterSectionCrew()
                .crew()
                .kickoff(
                    inputs={
                        "goal": self.state.goal,
                        "topic": self.state.topic,
                        "section_title": section_outline.title,
                        "section_description": section_outline.description,
                        "letter_outline": [
                            section_outline.model_dump_json()
                            for section_outline in 
                            self.state.demand_letter_outline

                            
                        ],
                        "employer_info": employer_info,
                        "employee_info": employee_info,
                        "incidents_info": self.state.letter_info.incidents
                    }
                )
            )
            title = output["title"]
            content = output["content"]
            section = Sections(title=title, content=content)
            return section

        for section_outline in self.state.demand_letter_outline:
            print(f"Writing Section: {section_outline.title}")
            print(f"Description: {section_outline.description}")
            # Schedule each section writing task
            task = asyncio.create_task(write_single_section(section_outline))
            tasks.append(task)

        # Await all section writing tasks concurrently
        sections = await asyncio.gather(*tasks)
        print("Newly generated sections:", sections)
        self.state.demand_letter.extend(sections)

        print("Demand Letter Sections", self.state.demand_letter)

    @listen(write_sections)
    async def join_and_save_section(self):
        print("Joining and Saving Demand Letter Sections")
        # Combine all sections into a single markdown string
        letter_content = ""

        for section in self.state.demand_letter:
            # Add the section title as an H1 heading
            letter_content += f"# {section.title}\n\n"
            # Add the section content
            letter_content += f"{section.content}\n\n"

        # The title of the letter from self.state.title
        letter_title = self.state.title

        # Create the filename by either using output_file_id or creating from title
        if self.state.output_file_id:
            filename = f"./{self.state.output_file_id}.md"
        else:
            filename = f"./{letter_title.replace(' ', '_')}.md"

        # Save the combined content into the file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(letter_content)

        print(f"Demand Letter saved as {filename}")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a demand letter")
    parser.add_argument("--data", dest="data_file", help="Path to JSON data file")
    parser.add_argument("--output-id", dest="output_id", help="Output file ID")
    return parser.parse_args()


def kickoff():
    args = parse_arguments()
    letter_flow = DemandLetterFlow()
    
    if args.data_file and args.output_id:
        letter_flow.state.output_file_id = args.output_id
        letter_flow.args = args
    
    letter_flow.kickoff()


def plot():
    letter_flow = DemandLetterFlow()
    letter_flow.plot()


# if __name__ == "__main__":
#     kickoff()
