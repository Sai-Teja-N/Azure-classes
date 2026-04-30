# Azure-classes —  Examples and Usage

This repository contains  example scripts that demonstrate basic Azure OpenAI usage and prompt-quality examples.

Files included
- [Temperature_Analyzer.py] : Analyze logs and return a concise root-cause and remediation.
- [azure_chat_example.py] : Simple Azure OpenAI chat example asking a plain-language question.
- [bad_prompt_terraform_example.py] : Illustration of a vague prompt that produces low-quality Terraform output.
- [good_prompt_terraform_example.py](: Precise prompts that encourage production-ready Terraform HCL output.
- [requirements.txt]: Python dependencies for this project.

Quick start (macOS)

1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Configure environment variables

Create a `.env` file in the repository root with these variables (example):

```text
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

4. Run an example

```bash
python3 azure_chat_example.py
python3 incident_analyzer.py
python3 bad_prompt_terraform_example.py
python3 good_prompt_terraform_example.py
```

Optional: Clone example repos

If you depend on external example repositories, clone them into this workspace. Replace `<repo-url>` with the repository URL:

```bash
git clone <repo-url>
```

Notes
- The code uses the `openai` Python package's Azure client surface (`from openai import AzureOpenAI`).
- Adjust `AZURE_OPENAI_API_VERSION` and `AZURE_OPENAI_DEPLOYMENT` to match your Azure AI Studio deployment.
