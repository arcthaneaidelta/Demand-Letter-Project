from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools.tools import SerperDevTool
from langchain_openai import ChatOpenAI

from ai.src.write_a_book_with_flows.types_1 import Sections


@CrewBase
class WriteDemandLetterSectionCrew:
    """Write Demand Letter Section Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    llm = ChatOpenAI(model="gpt-4o")

    @agent
    def researcher(self) -> Agent:
        search_tool = SerperDevTool()
        return Agent(
            config=self.agents_config["researcher"],
            tools=[search_tool],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=self.llm,
            verbose=True,
        )

    @task
    def research_section(self) -> Task:
        return Task(
            config=self.tasks_config["research_section"],
        )

    @task
    def write_section(self) -> Task:
        return Task(
            config=self.tasks_config["write_section"], 
            output_pydantic=Sections
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Write Demand Letter Section Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
