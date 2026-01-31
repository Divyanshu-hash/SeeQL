import os
import re

# Optional: LangChain/Groq for step-by-step explanations
GROQ_AVAILABLE = False
try:
    from langchain_groq import ChatGroq
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    GROQ_AVAILABLE = bool(os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_AVAILABLE = False

if GROQ_AVAILABLE:
    llm = ChatGroq(
        model="llama3-8b-8192",
        temperature=0.2,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )
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
""",
    )
    sql_explainer_chain = LLMChain(llm=llm, prompt=sql_prompt)


def _fallback_explain(query: str):
    """Simple rule-based explanation when Groq is not available."""
    q = query.strip()
    q_upper = q.upper()
    steps = []

    if "SELECT" in q_upper:
        steps.append("SELECT tells the database which columns to show. You listed the columns (or * for all) you want to see.")
    if "FROM" in q_upper:
        steps.append("FROM tells the database which table to read from. Your data comes from this table.")
    if "WHERE" in q_upper:
        steps.append("WHERE filters the rows. Only rows that match your condition are kept.")
    if "ORDER BY" in q_upper:
        steps.append("ORDER BY sorts the result. Rows are arranged in the order you specified (e.g. by a column, ascending or descending).")
    if "GROUP BY" in q_upper:
        steps.append("GROUP BY groups rows that share the same value in a column. Often used with COUNT or AVG to summarize data.")
    if "LIMIT" in q_upper:
        steps.append("LIMIT caps how many rows are returned. The rest are not shown.")

    if not steps:
        steps.append("Your query is read by the database, which then returns matching rows from the table.")
    return steps


def explain_sql(query: str):
    if GROQ_AVAILABLE:
        try:
            response = sql_explainer_chain.run(query=query)
            steps = [s.strip() for s in response.split("\n") if s.strip()]
            if steps:
                return steps
        except Exception:
            pass
    return _fallback_explain(query)
