import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize Groq LLM
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Prompt Template
sql_prompt = PromptTemplate(
    input_variables=["query"],
    template="""
You are a friendly SQL tutor for beginners.

Explain the following SQL query step-by-step in very simple language.
Do NOT use complex database terms.
Explain in the logical order SQL executes.

SQL Query:
{query}

Return the explanation as numbered steps.
"""
)

# Chain
sql_explainer_chain = LLMChain(
    llm=llm,
    prompt=sql_prompt
)

def explain_sql_langchain(query: str):
    response = sql_explainer_chain.run(query=query)

    # Convert response into clean steps list
    steps = [
        step.strip()
        for step in response.split("\n")
        if step.strip()
    ]

    return steps
