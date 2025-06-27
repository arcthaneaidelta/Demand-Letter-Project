# Demand Letter Generation System

Welcome to the Demand Letter Generation System, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system that generates formal demand letters for legal cases, leveraging the powerful and flexible framework provided by crewAI.

## Overview

This system will guide you through the process of creating a professional demand letter by leveraging multiple AI agents, each with specific roles. Here's a brief overview of what will happen in this flow:

1. **Collect Information**: The system will first collect necessary information about the employer, employee, and incidents for the demand letter.

2. **Generate Letter Outline**: The flow then uses the `OutlineCrew` to create a comprehensive outline for your demand letter. This crew will search the internet, define the structure, and main sections of the letter based on the provided information.

3. **Write Letter Sections**: Once the outline is ready, the flow will kick off a new crew, `WriteDemandLetterSectionCrew`, for each section outlined in the previous step. Each crew will be responsible for writing a specific section, ensuring that the content is detailed and legally sound.

4. **Join and Save Sections**: In the final step, the flow will combine all the sections into a single markdown file, creating a complete demand letter. This file will be saved in the root folder of your project.

By following this flow, you can efficiently produce a well-structured and comprehensive demand letter, leveraging the power of multiple AI agents to handle different aspects of the writing process.

## Installation

Ensure you have Python >=3.10 <=3.13 installed on your system. This project uses [Poetry](https://python-poetry.org/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install Poetry:

```bash
pip install poetry
```

Next, navigate to your project directory and install the dependencies:

1. First lock the dependencies and then install them:

```bash
crewai install
```

### Customizing & Dependencies

**Add your `OPENAI_API_KEY` into the `.env` file**  
**Add your `SERPER_API_KEY` into the `.env` file**

## Required Information for Demand Letters

Before generating a demand letter, you will need to collect the following information:

### Employer Information

- Full legal name of the company/business
- Complete business address
- Name and title of the appropriate recipient (HR director, CEO, legal department)
- Business registration information (optional)
- Employer Identification Number (optional)
- Supervisor names involved in the situation (optional)

### Employee Information

- Full legal name
- Position/job title
- Employment dates (start date, end date if applicable)
- Employee ID number (optional)
- Work location
- Pay rate/salary information
- Work schedule/hours
- Department/division (optional)
- Reporting structure (optional)
- Contact information for correspondence

### Incident Information

- Description of each incident/violation
- Dates of each incident
- Witnesses (optional)
- Evidence available (optional)
- Record of any prior complaints made (optional)

The system will prompt you to enter this information when you run it. You can also save this information for future use.

## Running the Project

To generate a demand letter, run this from the root folder of your project:

```bash
crewai run
```

This command initializes the demand letter generation process. The system will:

1. Prompt you to enter employer, employee, and incident information (or use previously saved information)
2. Generate a comprehensive outline for the demand letter
3. Write detailed sections based on the outline
4. Combine all sections into a final demand letter in markdown format

The final demand letter will be saved as a markdown file in the root directory, with a filename based on the employer and employee names.

## Support

For support, questions, or feedback regarding the Demand Letter Generation System or crewAI:

- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create professional demand letters with the power and simplicity of crewAI.
