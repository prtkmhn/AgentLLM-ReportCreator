import os
import gradio as gr
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from crewai_tools import tool, SeleniumScrapingTool, ScrapeWebsiteTool
import asyncio
from langchain_community.output_parsers.rail_parser import GuardrailsOutputParser
import json
# Define the DuckDuckGoSearch tool using the decorator for tool registration
@tool('DuckDuckGoSearch')
def search(search_query: str):
    """
    This function uses DuckDuckGoSearch tool to search for the given query.
    
    Args:
    search_query (str): The query to search for.
    
    Returns:
    The search results.
    """
    return DuckDuckGoSearchRun().run(search_query)

# Define the DuckDuckGoSearch tool
@tool('DuckDuckGoResults')
def search_results(search_query: str):
    """
    This function uses DuckDuckGoResults tool to get the search results.
    
    Args:
    search_query (str): The query to get results for.
    
    Returns:
    The search results.
    """
    return DuckDuckGoSearchResults().run(search_query)



# Define the WebScrapper tool
@tool('WebScrapper')

def web_scrapper(url: str):

    """
    Scrape content from a specified URL using a web scraping tool.
    
    Args:
    url (str): The URL to scrape.

    Returns:
    ScrapeWebsiteTool: An object containing the scraped data.
    llm=ChatGroq(temperature=0, groq_api_key="", model_name="llama3-70b-8192"),
                
    """
    return ScrapeWebsiteTool(website_url=url)

def load_agents_and_tasks_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        agents = []
        tasks = []

        for agent_data in data['agents']:
            # Assuming Agent is a dictionary for simplicity. Adjust based on your actual Agent class implementation.
            agent = {
                'role': agent_data['role'],
                'goal': agent_data['goal'],
                'tools': [globals()[tool_name] for tool_name in agent_data['tools']],
                'llm': ChatGroq(temperature=0, groq_api_key="YOUR API KEY", model_name="llama3-70b-8192"),
                'backstory': agent_data['backstory'],
                'allow_delegation': agent_data['allow_delegation'],
                'max_iter': agent_data['max_iter'],
                'verbose': agent_data['verbose'],
            }
            agents.append(agent)
            for task_data in agent_data['tasks']:
                task = {
                    'description': task_data['description'],
                    'expected_output': task_data['expected_output'],
                    'agent': agent  # Here, we're linking the task to the agent dictionary. Adjust based on your implementation.
                }
                tasks.append(task)
        
        # Debugging: Print the first agent to verify structure
        print("First agent loaded:", agents[0])

        return agents, tasks
async def kickoff_crew(topic: str, selected_agent_roles: list, agents, tasks):
    results = []
    for role in selected_agent_roles:
        selected_agent = next(agent for agent in agents if agent['role'] == role)
        selected_tasks = [task for task in tasks if task['agent']['role'] == role]
        crew = Crew(agents=[selected_agent], tasks=selected_tasks)
        result = crew.kickoff(inputs={'topic': topic})
        results.append(result)
    return results

async def process_research(topic, selected_agent_roles):
    agents, tasks = load_agents_and_tasks_from_json('agents_and_tasks.json')
    results = await kickoff_crew(topic, selected_agent_roles, agents, tasks)
    # Assuming results is a list of strings, join them with newline characters
    formatted_results = "\n".join(results)
    return formatted_results

def sync_process_research(topic, selected_agent_roles):
    return asyncio.run(process_research(topic, selected_agent_roles))

def main():
    agents, _ = load_agents_and_tasks_from_json('agents_and_tasks.json')
    agent_roles = [agent['role'] for agent in agents]

    with gr.Blocks() as demo:
        gr.Markdown("## CrewAI Research Tool")
        with gr.Tab("Research"):
            topic_input = gr.Textbox(label="Enter Topic", placeholder="Type here...")
            agent_dropdown = gr.CheckboxGroup(label="Select Agents", choices=agent_roles)
            submit_button = gr.Button("Start Research")
            output = gr.Markdown(label="Result")
            
            submit_button.click(
                fn=sync_process_research,
                inputs=[topic_input, agent_dropdown],
                outputs=output
            )
            
            gr.Markdown("### Research\nEnter a topic, select one or more agents, and click 'Start Research' to initiate the research process. The selected agents will work sequentially on gathering information, analyzing data, and generating a comprehensive report on the given topic.")

    demo.launch()

if __name__ == "__main__":
    main()
