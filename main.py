import uuid

from pipeline import create_application_pipeline, get_current_state, print_state_summary

def get_interviewer_display(step: str) -> tuple[str, str]:
    """Get emoji and name for the current interviewer.
    
    Args:
        step: Current step name
        
    Returns:
        Tuple of (emoji, name)
    """
    interviewers = {
        "intake": ("🧑‍💼", "Alex (Recruiter)"),
        "assessment": ("👨‍💻", "Jordan (Assessor)"),
        "decision": ("👔", "Sam (Hiring Manager)"),
        "complete": ("✅", "System"),
    }
    return interviewers.get(step, ("🤖", "Agent"))



def display_interviewer(step: str):

    interviewer_display = get_interviewer_display(step)

    emoji, name = interviewer_display
    print(f"\n{emoji} {name}: ", end="")

def print_interviewer_message(state: dict):
    print(state.get("messages", [])[-1].content)

def get_current_step(state: dict):
    return state.get("current_step", "intake")

def send_user_message(pipeline, user_message: str, config: dict, current_step: str) -> str: 

    current_state = pipeline.invoke(
        {
            "messages": [{"role": "user", "content": user_message}]
        },
        config
    )

    active_step = get_current_step(current_state)
    print(active_step)

    # Check if handoff has occurred and send appropriate message
    if active_step != current_step:
        display_interviewer(current_step)

        hand_off_message_fragment = "Thanks for your answers."

        if active_step == "assessment":
            print(f"{hand_off_message_fragment} I'll now be transferring you to Jordan for technical Assessment")
        
        if active_step == "decision":
            print(f"{hand_off_message_fragment} I'll now be transferring you to Sam for a final decision")

        if active_step == "complete":
            # Check for Sam's feedback and print it
            feedback = current_state.get("feedback")
            if feedback:
                display_interviewer("decision")
                print(feedback)

                print("\n" + "=" * 60)
                print("  ✅ INTERVIEW COMPLETE")
                print("=" * 60)
                print_state_summary(current_state)
    else:
        display_interviewer(active_step)
        print_interviewer_message(current_state)

    return active_step
                

def interactive_mode():
    print("\n" + "=" * 60)
    print("💼 JOB APPLICATION PIPELINE")
    print("Handoffs Pattern Demo")
    print("=" * 60)
    
    print("""
Welcome! You're about to go through our interview process.

You'll speak with three interviewers:
  🧑‍💼 Alex (Recruiter) - Initial intake
  👨‍💻 Jordan (Assessor) - Technical evaluation
  👔 Sam (Hiring Manager) - Final decision

Commands:
  'state'  - Show current application state
  'new'    - Start a new application
  'quit'   - Exit the program
""")
    
    print("Initializing pipeline...")

    try:
        pipeline = create_application_pipeline()
        print("✅ Ready!\n")
    except Exception as e:
        print(f"❌ Error initializing pipeline: {e}")
        print("\nMake sure you have set your API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        return
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("-" * 60)
    print("Starting new application...")
    print("-" * 60)

    kickoff_message = "Hi, I'd like to apply for a job"

    current_interview_step = "intake"

    send_user_message(pipeline, kickoff_message, config, current_interview_step)

    while True:

        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Thanks for using the Job Application Pipeline. Goodbye!\n")
                break
            
            if user_input.lower() == "state":
                state = get_current_state(pipeline, thread_id)
                print_state_summary(state)
                continue
            
            if user_input.lower() == "new":
                thread_id = str(uuid.uuid4())
                config = {"configurable": {"thread_id": thread_id}}
                print("\n" + "-" * 60)
                print("Starting new application...")
                print("-" * 60)
                send_user_message(pipeline, kickoff_message, config, "intake")
                
                continue

            current_interview_step = send_user_message(pipeline, user_input, config, current_interview_step)


        except KeyboardInterrupt:
            print("\n\n👋 Goodbey! \n")
            break

if __name__ == "__main__":
    interactive_mode()