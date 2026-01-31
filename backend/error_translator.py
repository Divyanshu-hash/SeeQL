import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize Groq LLM
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0.1,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Prompt Template
error_prompt = PromptTemplate(
    input_variables=["error"],
    template="""
You are a friendly SQL tutor helping beginners.

A student ran a SQL query and got the following database error:

"{error}"

Your job:
1. Explain what this error means in very simple language.
2. Explain why this error happened.
3. Give a clear suggestion on how to fix it.

Rules:
- Do NOT use complex database jargon.
- Do NOT mention internal database details.
- Keep the explanation short and beginner-friendly.
- Use bullet points.

Respond in this format:

Meaning:
- ...

Reason:
- ...

How to Fix:
- ...
"""
)

# LangChain Chain
error_explainer_chain = LLMChain(
    llm=llm,
    prompt=error_prompt
)

def translate_error_langchain(error: str):
    response = error_explainer_chain.run(error=error)

    # Convert response into structured sections
    sections = {"meaning": [], "reason": [], "fix": []}
    current = None

    for line in response.split("\n"):
        line = line.strip()

        if line.lower().startswith("meaning"):
            current = "meaning"
        elif line.lower().startswith("reason"):
            current = "reason"
        elif line.lower().startswith("how to fix"):
            current = "fix"
        elif line.startswith("-") and current:
            sections[current].append(line[1:].strip())

    return sections
