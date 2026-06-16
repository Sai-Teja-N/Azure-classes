import os
from pathlib import Path
from crewai.tools import tool
from config import TERRAFORM_OUTPUT_DIR

@tool("Write File")
def write_terraform_file(filename: str, content: str) -> str:
    """
    Writes content to a file in the terraform_output directory.
    Useful for creating main.tf, variables.tf, imports.tf, and recommendations.md.
    """
    try:
        # Strip 'terraform_output/' prefix if the LLM accidentally includes it
        if filename.startswith("terraform_output/"):
            filename = filename.replace("terraform_output/", "", 1)
            
        filepath = TERRAFORM_OUTPUT_DIR / filename
        
        # Ensure the subdirectories exist just in case
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully wrote {filename} to {filepath}"
    except Exception as e:
        return f"Error writing file {filename}: {e}"

@tool("Read File")
def read_terraform_file(filename: str) -> str:
    """
    Reads content from a file in the terraform_output directory.
    Useful for reviewing generated code or recommendations.
    """
    try:
        # Strip 'terraform_output/' prefix if the LLM accidentally includes it
        if filename.startswith("terraform_output/"):
            filename = filename.replace("terraform_output/", "", 1)
            
        filepath = TERRAFORM_OUTPUT_DIR / filename
        if not filepath.exists():
            return f"Error: File {filename} does not exist."
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {filename}: {e}"
