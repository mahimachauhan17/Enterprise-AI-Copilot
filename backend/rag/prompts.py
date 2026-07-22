"""
Prompt Templates

System and user prompt templates for the RAG pipeline.
The prompts instruct the LLM to answer only from context,
cite sources, and format responses in markdown.
"""

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from backend.utils.logger import get_logger

logger = get_logger(__name__)


SYSTEM_TEMPLATE = """You are an expert AI assistant for enterprise document analysis. Your role is to answer questions accurately based ONLY on the provided document context.

## Rules:
1. **Answer ONLY from the provided context.** Do not use any prior knowledge or make assumptions beyond what the documents contain.
2. **Cite your sources** using [Source N] markers that correspond to the numbered sources in the context. Place citations inline near the relevant information.
3. **If the context does not contain enough information** to answer the question, clearly state: "I don't have enough information in the uploaded documents to answer this question."
4. **Be professional, concise, and accurate.** Provide thorough answers but avoid unnecessary verbosity.
5. **Use markdown formatting** when appropriate — headings, bullet points, numbered lists, bold text, and code blocks for better readability.
6. **When summarizing**, cover all key points from the relevant sources.

## Context from uploaded documents:
{context}"""


HUMAN_TEMPLATE = """{question}"""


def get_rag_prompt() -> ChatPromptTemplate:
    """
    Get the RAG prompt template.

    Returns:
        ChatPromptTemplate with system and human message templates.
        Variables: {context}, {question}
    """
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ])
