from typing import Literal
from langchain_groq import ChatGroq
from langgraph.types import Command, interrupt
from langgraph.graph import END
import uuid

from .state import EmailAgentState, EmailClassification

llm = ChatGroq(model="openai/gpt-oss-120b")

def read_email(state: EmailAgentState) -> EmailAgentState:
    pass

def classify_intent(state: EmailAgentState) -> EmailAgentState:
    structured_llm = llm.with_structured_output(EmailClassification)
    
    classification_prompt = f"""
    Analyze this customer email and classify it:
    
    Email: {state.get('email_content')}
    From: {state.get('sender_email')}
    
    Provide classification, including intent, urgency, topic, and summary
    """
    
    classification = structured_llm.invoke(classification_prompt)
    return {"classification": classification}

def search_documentation(state: EmailAgentState) -> dict:
    classification = state.get('classification', {})
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"
    
    try:
        search_results = [
            "--Search_result_1--",
            "--Search_result_2--",
            "--Search_result_3--"
        ]
    except Exception as e:
        search_results = [f"Search temporarily unavailable: {str(e)}"]
        
    return {"search_results": search_results}

def bug_tracking(state: EmailAgentState) -> dict:
    ticket_id = f"BUG_{uuid.uuid4()}"
    return {"ticket_id": ticket_id}

def write_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    classification = state.get('classification', {})
    
    context_sections = []
    
    if state.get('search_results'):
        formatted_docs = "\n".join([f"- {doc}" for doc in state['search_results']])
        context_sections.append(f"Relevant documentation:\n{formatted_docs}")
        
    if state.get('customer_history'):
        context_sections.append(f"Customer tier: {state['customer_history'].get('tier', 'standard')}")
        
    draft_prompt = f"""
    Draft a response to this customer email:
    {state.get('email_content')}
    
    Email intent: {classification.get('intent', 'unknown')}
    Urgency level: {classification.get('urgency', 'medium')}
    
    {chr(10).join(context_sections)}
    
    Guidelines:
    - Be professional and helpful
    - Address their specific concern
    - Use the provided documentation when relevant
    - Be brief
    """
    
    response = llm.invoke(draft_prompt)
    
    needs_review = (
        classification.get('urgency') in ['high', 'critical'] or
        classification.get('intent') == 'complex'
    )
    
    if needs_review:
        goto = "human_review"
    else:
        goto = "send_reply"
        
    return Command(
        update={"draft_response": response.content},
        goto=goto
    )

def human_review(state: EmailAgentState) -> Command[Literal["send_reply", "__end__"]]:
    classification = state.get('classification', {})
    
    human_decision = interrupt({
        "email_id": state['email_id'],
        "original_email": state['email_content'],
        "draft_response": state['draft_response'],
        "urgency": classification['urgency'],
        "intent": classification['intent'],
        "action": "Please review and approve/edit this response"
    })
    
    if human_decision.get("approved"):
        return Command(
            update={"draft_response": human_decision.get("edited_response", state.get('draft_response'))},
            goto="send_reply"
        )
    else:
        return Command(update={}, goto=END)

def send_reply(state: EmailAgentState) -> dict:
    return {}