from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
key = ""
endpoint = ""
region = "eastus" # e.g., "eastus"


# 2. Initialize the Text Translation Client
credential = AzureKeyCredential(key)
text_translator = TextTranslationClient(
    endpoint=endpoint, 
    credential=credential, 
    region=region
)

# 3. Define the text elements and target languages
input_text = ["Hello World! Welcoem to the coding"]
target_languages = ["fr", "es"]

try:
    # 4. Call the translate method
    response = text_translator.translate(body=input_text, to_language=target_languages)

    # 5. Parse and print the results
    for translation in response:
        
        print(translation)
        # The service can auto-detect the source language if not explicitly provided
    #    if translation.detected_language:
           
            #print(translation)
            
        for translated_text in translation.translations:
            print(f"Translated to {translated_text.to}: {translated_text.text}")

except Exception as e:
    print(f"An error occurred: {e}")
