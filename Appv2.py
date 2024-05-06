import json
import gradio as gr
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from crewai_tools import tool, ScrapeWebsiteTool
import asyncio

@tool('DuckDuckGoSearch')
def search(search_query: str) -> str:
    """Use DuckDuckGoSearch tool to search for the given query."""
    return DuckDuckGoSearchRun().run(search_query)

@tool('DuckDuckGoResults')
def search_results(search_query: str) -> str:
    """Use DuckDuckGoResults tool to get the search results."""
    return DuckDuckGoSearchResults().run(search_query)

@tool('WebScrapper')
def web_scrapper(url: str) -> ScrapeWebsiteTool:
    """Scrape content from a specified URL using a web scraping tool."""
    return ScrapeWebsiteTool(website_url=url)

def load_agents_and_tasks_from_json(file_path):
    """Load agents and tasks from a JSON file."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    agents = []
    for agent_data in data['agents']:
        agent = Agent(
            role=agent_data['role'],
            goal=agent_data['goal'],
            tools=[eval(tool) for tool in agent_data['tools']],
            llm=eval(agent_data['llm']),
            backstory=agent_data['backstory'],
            allow_delegation=agent_data['allow_delegation'],
            max_iter=agent_data['max_iter'],
            verbose=agent_data['verbose']
        )
        agents.append(agent)
    
    tasks = []
    for task_data in data['tasks']:
        task = Task(
            description=task_data['description'],
            expected_output=task_data['expected_output'],
            agent=agents[task_data['agent_index']],
            context=[tasks[index] for index in task_data.get('context', [])]
        )
        tasks.append(task)
    
    return agents, tasks

def kickoff_crew(topic: str) -> dict:
    """Kickoff the research process for a given topic using CrewAI components."""
    try:
        groq_api_key = "" #YOUR KEY
        if not groq_api_key:
            raise ValueError("API Key for Groq is not set in environment variables")
        
        globals()['groq_llm_70b'] = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="llama3-70b-8192")
        globals()['groq_llm_8b'] = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="llama3-8b-8192")
        
        agents, tasks = load_agents_and_tasks_from_json('agents_and_tasks.json')
        crew = Crew(agents=agents, tasks=tasks)
        
        return crew.kickoff(inputs={'topic': topic})
    except Exception as e:
        return f"Error: {str(e)}"

async def process_research(topic):
    """Process the research asynchronously."""
    return await asyncio.to_thread(kickoff_crew, topic)

async def main():
    """Set up the Gradio interface for the CrewAI Research Tool."""
    with gr.Blocks() as demo:
        gr.Markdown("## CrewAI Research Tool")
        
        topic_input = gr.Textbox(label="Enter Topic", placeholder="Type here...")
        submit_button = gr.Button("Start Research")
        output = gr.Markdown(label="Result")
        
        submit_button.click(fn=process_research, inputs=topic_input, outputs=output)
        
        gr.Markdown("Enter a topic and click 'Start Research' to initiate the research process.")

    demo.queue(api_open=False, max_size=3).launch()

if __name__ == "__main__":
    asyncio.run(main())
