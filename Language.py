import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import (
    TextAnalyticsClient,
    RecognizeEntitiesAction,
    RecognizeLinkedEntitiesAction,
    RecognizePiiEntitiesAction,
    ExtractKeyPhrasesAction,
    AnalyzeSentimentAction,
)

def get_client() -> TextAnalyticsClient:
    """Loads environment variables and authenticates the Azure client."""
    load_dotenv()
    endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
    key = os.getenv("AZURE_LANGUAGE_KEY")
    
    if not endpoint or not key:
        raise ValueError("Missing credentials. Please check AZURE_LANGUAGE_ENDPOINT and AZURE_LANGUAGE_KEY in your .env file.")
        
    return TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def analyze_all_in_one(client: TextAnalyticsClient, documents: list):
    """Detects language, then runs NER, PII, Sentiment, Key Phrases, and Linked Entities in one payload."""
    
    print("1. Detecting Language...")
    lang_result = client.detect_language(documents=documents)
    
    # We will format the documents as dictionaries to explicitly pass the detected language
    # to the next stage. This improves accuracy for the downstream models.
    formatted_docs = []
    for idx, doc in enumerate(lang_result):
        if not doc.is_error:
            lang_code = doc.primary_language.iso6391_name
            print(f"   ↳ Document [{idx}] Language: {doc.primary_language.name} ({lang_code})")
            formatted_docs.append({"id": str(idx), "language": lang_code, "text": documents[idx]})
        else:
            print(f"   ↳ Document [{idx}] Language Error: {doc.error}")
            formatted_docs.append({"id": str(idx), "language": "en", "text": documents[idx]})

    print("\n2. Submitting Batch Actions (NER, PII, Sentiment, Key Phrases, Linked Entities)...")
    poller = client.begin_analyze_actions(
        formatted_docs,
        display_name="Comprehensive Text Analysis",
        actions=[
            RecognizeEntitiesAction(),
            RecognizeLinkedEntitiesAction(),
            RecognizePiiEntitiesAction(),
            ExtractKeyPhrasesAction(),
            AnalyzeSentimentAction(),
        ]
    )

    # Wait for the long-running operation to finish
    document_results = poller.result()

    # Parse and print the results
    for result_group in document_results:
        for idx, doc_results in enumerate(result_group):
            print(f"\n{'='*50}")
            print(f"RESULTS FOR DOCUMENT [{idx}]: '{documents[idx]}'")
            print(f"{'='*50}")

            if doc_results.is_error:
                print(f"Error processing document: {doc_results.error.message}")
                continue
            
            # Switch based on the action kind returned by the poller
            if doc_results.kind == "EntityRecognition":
                print("\n[ NAMED ENTITIES (NER) ]")
                for entity in doc_results.entities:
                    print(f"  - {entity.text} (Category: {entity.category}, Confidence: {entity.confidence_score:.2f})")
            
            elif doc_results.kind == "EntityLinking":
                print("\n[ LINKED ENTITIES ]")
                for entity in doc_results.entities:
                    print(f"  - {entity.name} (Data Source: {entity.data_source}, URL: {entity.url})")
            
            elif doc_results.kind == "PiiEntityRecognition":
                print("\n[ PII DETECTED ]")
                if doc_results.entities:
                    for entity in doc_results.entities:
                        print(f"  - {entity.text} (Category: {entity.category}, Confidence: {entity.confidence_score:.2f})")
                else:
                    print("  - No PII found.")
            
            elif doc_results.kind == "KeyPhraseExtraction":
                print("\n[ KEY PHRASES ]")
                print(f"  - {', '.join(doc_results.key_phrases)}")
            
            elif doc_results.kind == "SentimentAnalysis":
                print("\n[ SENTIMENT ANALYSIS ]")
                print(f"  - Overall Sentiment: {doc_results.sentiment.upper()}")
                print(f"  - Scores: Positive={doc_results.confidence_scores.positive:.2f} | "
                      f"Neutral={doc_results.confidence_scores.neutral:.2f} | "
                      f"Negative={doc_results.confidence_scores.negative:.2f}")

if __name__ == "__main__":
    sample_text = [
        "ABC is the CEO of ABC. He sent an email to abc@gmail.com regarding the "
        "new Azure AI implementation in Paris. I absolutely loved the presentation, it was incredible!"
    ]
    
    text_client = get_client()
    analyze_all_in_one(text_client, sample_text)
