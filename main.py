import os
from dotenv import load_dotenv
from langgraph.types import Command

load_dotenv() 

from src import app  

def main():
    print("📸 Generating graph image...")
    try:
        png_bytes = app.get_graph().draw_mermaid_png()
        with open("email_agent_graph.png", "wb") as f:
            f.write(png_bytes)
        print("✅ Graph image saved successfully as 'email_agent_graph.png'\n")
    except Exception as e:
        print(f"⚠️ Failed to generate graph image: {e}\n")

    initial_state = {
        "email_content": "I was charged twice for my subscription! This is urgent!",
        "sender_email": "customer@example.com",
        "email_id": "email_999"
    }

    config = {"configurable": {"thread_id": "customer_1"}}

    print("🚀 Starting Customer Support Agent...\n")

    result = app.invoke(initial_state, config)

    if '__interrupt__' in result:
        print("\n⚠️ Agent paused. Human Review Required!")
        
        interrupt_data = result['__interrupt__'][0].value
        print(f"Reason: {interrupt_data.get('action')}")
        print(f"Classification: Intent = {interrupt_data.get('intent')}, Urgency = {interrupt_data.get('urgency')}")
        print("-" * 40)
        print(f"Draft Ready for Review:\n{interrupt_data.get('draft_response')}")
        print("-" * 40)
        
        decision = input("\nDo you approve this draft? (y/n): ").strip().lower()
        
        if decision == 'y':
            print("\n👨‍💻 Admin approved. Resuming execution...")
            human_response = Command(
                resume={
                    "approved": True
                }
            )
        else:
            print("\n👨‍💻 Admin rejected. Agent will stop, human will handle it manually.")
            human_response = Command(
                resume={
                    "approved": False
                }
            )
            
        app.invoke(human_response, config)
        
    else:
        print("\n✅ Process completed automatically without human intervention.")

if __name__ == "__main__":
    main()