import os
import gradio as gr
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from crewai_tools import tool, SeleniumScrapingTool, ScrapeWebsiteTool
import asyncio
from langchain_community.output_parsers.rail_parser import GuardrailsOutputParser

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
    """
    return ScrapeWebsiteTool(website_url=url)

def kickoff_crew(topic: str) -> dict:
    try:
        """Kickoff the research process for a given topic using CrewAI components."""
        # Retrieve the API key from the environment variables

        groq_api_key = #add your groq key
        if not groq_api_key:
            raise ValueError("API Key for Groq is not set in environment variables")
    
        # Initialize the Groq large language model
        groq_llm_70b = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="llama3-70b-8192")
        groq_llm_8b = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name="llama3-8b-8192")
    
        # Define Agents with Groq LLM
        researcher = Agent(
            role='Researcher',
            goal='Collect detailed information on {topic}',
            tools=[search, search_results, web_scrapper],
            llm=groq_llm_70b,  # Assigning the Groq LLM here
            backstory=(
                "As a diligent researcher, you explore the depths of the internet to "
                "unearth crucial information and insights on the assigned topics. "
                "With a keen eye for detail and a commitment to accuracy, you meticulously document every source "
                "and piece of data gathered. Your research is thorough, ensuring that no stone is left unturned. "
                "This dedication not only enhances the quality of the information but also ensures "
                "reliability and trustworthiness in your findings."
            ),
            allow_delegation=False,
            max_iter=5,
            verbose=True,  # Optional
        )
        
        editor = Agent(
            role='Editor',
            goal='Compile and refine the information into a comprehensive report on {topic}',
            llm=groq_llm_70b,  # Assigning the Groq LLM here
            backstory=(
                "With a keen eye for detail and a strong command of language, you transform "
                "raw data into polished, insightful reports that are both informative and engaging. "
                "Your expertise in editing ensures that every report is not only thorough but also "
                "clearly communicates the key findings in a manner that is accessible to all readers. "
                "As an editor, your role is crucial in shaping the final presentation of data, making "
                "complex information easy to understand and appealing to the audience."
            ),
            allow_delegation=False,
            max_iter=3,
            verbose=True,  # Optional
        )
        
        # Define Tasks
        research_task = Task(
            description=(
                "Use DuckDuckGoSearch tool to gather initial information about {topic}. "
                "Next, employ DuckDuckGoResults tool to gather full details of the insights from search results, reading them carefully and preparing detailed summaries on {topic}. "
                "Utilize the WebScrapper tool to extract additional information and insights from all links or URLs that appear significant regarding {topic} after analyzing the snippets of the search results. "
                "Compile your findings into an initial draft, ensuring to include all sources with their titles and links relevant to the topic. "
                "Throughout this process, maintain a high standard of accuracy and ensure that no information is fabricated or misrepresented."
            ),
            expected_output=(
                "A draft report containing all relevant information about the topic and sources used. "
                "The report should be well-structured, including an introduction, a detailed body with organized sections according to different aspects of the topic, and a conclusion. "
                "Each section should cite sources accurately and provide a comprehensive overview of the findings."
            ),
            agent=researcher
        )
        
        edit_task = Task(
            description=(
                "Review and refine the draft report produced by the research task. Organize the content methodically, "
                "ensuring that the structure is logical and enhances the flow of information. Check all factual data for accuracy, "
                "correct any discrepancies, and ensure that the information is current and well-supported by sources. "
                "Enhance the readability of the report by improving language clarity, adjusting sentence structure, and ensuring consistency in tone. "
                "Include a dedicated section that lists all sources used in the research_task. "
                "Each source used in the analysis should be presented as a bullet point in the format: title: link "
                "Ensure that all sources you include in the final report exist by scrapping them if necessary. "
                "This section should be comprehensive, clearly formatted, and easy to navigate, providing full transparency on the references used."
            ),
            expected_output=(
                "A finalized comprehensive report on ## {topic} ##. The report should be polished, with a clear and engaging narrative "
                "that accurately reflects the research findings. It should include an introduction, a detailed and extensive discussion section, a concise conclusion, "
                "and a well-organized source list. The document should be free of grammatical errors and ready for publication or presentation."
            ),
            agent=editor,
            context=[research_task]
        )
    
        # Forming the Crew
        crew = Crew(
            agents=[researcher, editor],
            tasks=[research_task, edit_task]
        )
    
        # Kick-off the research process
        result = crew.kickoff(inputs={'topic': topic})
        return result
    except Exception as e:
        return f"Error: {str(e)}"

async def process_research(topic):
    result = await asyncio.to_thread(kickoff_crew, topic)
    return result

async def main():
    """Set up the Gradio interface for the CrewAI Research Tool."""
    with gr.Blocks() as demo:
        gr.Markdown("## CrewAI Research Tool")
        
        with gr.Tab("Agents"):
            agent_list = gr.Dataframe(
                headers=["Role", "Goal", "Tools", "LLM", "Backstory", "Allow Delegation", "Max Iterations"],
                datatype=["str", "str", "str", "str", "str", "bool", "number"],
                col_count=(7, "fixed"),
                row_count=(2, "fixed"),
                value=[
                    ["Researcher", "Collect detailed information on {topic}", "DuckDuckGoSearch, DuckDuckGoResults, WebScrapper", "groq_llm_70b", "As a diligent researcher, you explore the depths of the internet to unearth crucial information and insights on the assigned topics. With a keen eye for detail and a commitment to accuracy, you meticulously document every source and piece of data gathered. Your research is thorough, ensuring that no stone is left unturned. This dedication not only enhances the quality of the information but also ensures reliability and trustworthiness in your findings.", False, 5],
                    ["Editor", "Compile and refine the information into a comprehensive report on {topic}", "", "groq_llm_70b", "With a keen eye for detail and a strong command of language, you transform raw data into polished, insightful reports that are both informative and engaging. Your expertise in editing ensures that every report is not only thorough but also clearly communicates the key findings in a manner that is accessible to all readers. As an editor, your role is crucial in shaping the final presentation of data, making complex information easy to understand and appealing to the audience.", False, 3]
                ]
            )
            gr.Markdown("### Agents\nHere you can define the agents that will be part of the research crew. Each agent has a specific role, goal, tools, LLM, backstory, and other settings. You can edit these details to customize the agents according to your needs.")
            gr.Markdown("#### Examples\n- Role: Researcher, Analyst, Editor, Fact-Checker\n- Goal: Collect information, Analyze data, Refine report, Verify facts\n- Tools: DuckDuckGoSearch, DuckDuckGoResults, WebScrapper\n- LLM: groq_llm_70b, groq_llm_8b\n- Backstory: Provide a brief description of the agent's background and expertise.")
        
        with gr.Tab("Research"):
            topic_input = gr.Textbox(label="Enter Topic", placeholder="Type here...")
            submit_button = gr.Button("Start Research")
            output = gr.Markdown(label="Result")
            
            submit_button.click(
                fn=process_research,
                inputs=topic_input,
                outputs=output
            )
            
            gr.Markdown("### Research\nEnter a topic and click 'Start Research' to initiate the research process. The crew of agents will work together to gather information, analyze data, and generate a comprehensive report on the given topic.")
            gr.Markdown("#### Example Topics\n- Artificial Intelligence\n- Climate Change\n- Blockchain Technology\n- Renewable Energy\n- Cybersecurity")

    # demo.launch(debug=True)
    demo.queue(api_open=False, max_size=3).launch()

if __name__ == "__main__":
    asyncio.run(main())
