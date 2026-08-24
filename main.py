import sys
from loop import run_agent_loop

def cli_entry():
    if len(sys.argv) < 2:
        print("Usage: agent-loop \"Build a Python calculator...\"")
        sys.exit(1)
        
    # Combines all arguments into a single prompt string
    user_prompt = " ".join(sys.argv[1:])
    
    print("=== Starting Lightweight Local Agent ===")
    final_result = run_agent_loop(initial_prompt=user_prompt, max_iterations=10)
    
    print("\n=== Execution Complete ===")
    if final_result:
        print(f"Final Output: {final_result}")

if __name__ == "__main__":
    cli_entry()