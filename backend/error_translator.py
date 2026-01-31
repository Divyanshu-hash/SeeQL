import os
import re

# Optional: LangChain/Groq for richer explanations
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
        temperature=0.1,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )
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
""",
    )
    error_explainer_chain = LLMChain(llm=llm, prompt=error_prompt)


def _fallback_translate(error: str):
    """Rule-based friendly explanation when Groq is not available."""
    err_lower = error.lower()
    sections = {"meaning": [], "reason": [], "fix": []}

    if "no such table" in err_lower or "no such column" in err_lower:
        sections["meaning"].append("The database doesn't recognize a table or column name you used.")
        m = re.search(r"no such (?:table|column):?\s*[\w.]*(\w+)", err_lower, re.I)
        name = m.group(1) if m else "it"
        sections["reason"].append(f"Either the table/column '{name}' doesn't exist, or there's a typo.")
        sections["fix"].append("Check your table and column names. Use the dataset selector to see the correct names.")
    elif "syntax error" in err_lower or "near" in err_lower:
        sections["meaning"].append("SQL couldn't understand part of your query — there's a syntax mistake.")
        sections["reason"].append("A keyword might be misspelled, or a comma, quote, or bracket is missing or in the wrong place.")
        sections["fix"].append("Read the query from left to right and check spelling and punctuation. Try a simpler query first.")
    elif "ambiguous" in err_lower:
        sections["meaning"].append("A column name appears in more than one table, so the database doesn't know which one you mean.")
        sections["reason"].append("When multiple tables have the same column name, you need to specify the table.")
        sections["fix"].append("Use the table name before the column, e.g. students.name instead of just name.")
    elif "not allowed" in err_lower or "forbidden" in err_lower:
        sections["meaning"].append("This playground only allows safe read-only queries.")
        sections["reason"].append("Commands that change or delete data are disabled here.")
        sections["fix"].append("Use only SELECT queries to explore and filter data.")
    else:
        sections["meaning"].append("Something went wrong while running your query.")
        sections["reason"].append("The database returned an error. It might be a typo, wrong table/column name, or invalid syntax.")
        sections["fix"].append("Double-check your query. Try selecting from one table with SELECT * FROM table_name first.")

    return sections


def translate_error(error: str):
    if GROQ_AVAILABLE:
        try:
            response = error_explainer_chain.run(error=error)
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
            if any(sections.values()):
                return sections
        except Exception:
            pass
    return _fallback_translate(error)
