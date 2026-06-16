import os
import sys
from crew import create_infra_crew
from config import TERRAFORM_OUTPUT_DIR

def main():
    print("🚀 Initializing AWS Infrastructure CrewAI Agent...")
    print(f"📂 Output directory: {TERRAFORM_OUTPUT_DIR}")
    
    crew = create_infra_crew()
    
    print("\n⚡ Kicking off the Crew... this may take a few minutes as they scan the account.")
    try:
        result = crew.kickoff()
        
        print("\n" + "="*50)
        print("✅ CREW EXECUTION COMPLETE")
        print("="*50)
        print("\nFinal Result from Manager:")
        print(result)
        
        print("\nGenerated files should be located in:")
        print(f"  {TERRAFORM_OUTPUT_DIR}")
        
    except Exception as e:
        print(f"\n❌ Error during crew execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
