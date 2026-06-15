"""AWS Bedrock and Azure OpenAI LLM factory.

This module provides a LangChain chat model implementing `.invoke()` and
compatible with LangChain Expression Language (LCEL), supporting AWS Bedrock 
and Azure OpenAI APIs.
"""
import logging
import os
from urllib.parse import urlsplit, urlunsplit
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

log = logging.getLogger(__name__)


def _clean_env_text(value: str) -> str:
    return value.split("#", 1)[0].strip()


def _normalize_resource_endpoint(raw_value: str) -> str:
    cleaned = _clean_env_text(raw_value)
    if not cleaned:
        return ""

    parsed = urlsplit(cleaned)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")).rstrip("/")

    return cleaned.rstrip("/")


class BedrockConverseChatModel(BaseChatModel):
    model_id: str
    region_name: str
    temperature: float = 0.2
    max_tokens: int = 1024
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_profile: str | None = None

    @property
    def _llm_type(self) -> str:
        return "bedrock-converse"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "region_name": self.region_name}

    def _client(self):
        import boto3

        session = boto3.Session(
            profile_name=self.aws_profile or None,
            aws_access_key_id=self.aws_access_key_id or None,
            aws_secret_access_key=self.aws_secret_access_key or None,
            aws_session_token=self.aws_session_token or None,
            region_name=self.region_name,
        )
        return session.client("bedrock-runtime", region_name=self.region_name)

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs):
        system_chunks: list[str] = []
        bedrock_messages: list[dict[str, Any]] = []

        for message in messages:
            content = message.content if isinstance(message.content, str) else str(message.content)
            if isinstance(message, SystemMessage):
                system_chunks.append(content)
            elif isinstance(message, HumanMessage):
                bedrock_messages.append({"role": "user", "content": [{"text": content}]})
            elif isinstance(message, AIMessage):
                bedrock_messages.append({"role": "assistant", "content": [{"text": content}]})

        request: dict[str, Any] = {
            "modelId": self.model_id,
            "messages": bedrock_messages,
            "inferenceConfig": {
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        if system_chunks:
            request["system"] = [{"text": "\n\n".join(system_chunks)}]

        try:
            response = self._client().converse(**request)
        except Exception:
            log.exception("Bedrock converse call failed")
            raise
            
        content_blocks = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(block.get("text", "") for block in content_blocks if isinstance(block, dict))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


def _build_bedrock(model: str, temperature: float, max_tokens: int):
    model_id = (
        os.getenv("BEDROCK_INFERENCE_PROFILE_ID")
        or os.getenv("BEDROCK_INFERENCE_PROFILE_ARN")
        or model
        or os.getenv("BEDROCK_MODEL_ID")
    )
    if not model_id:
        raise ValueError(
            "BEDROCK_INFERENCE_PROFILE_ID, BEDROCK_INFERENCE_PROFILE_ARN, "
            "BEDROCK_MODEL_ID, or LLM_MODEL must be set for Bedrock"
        )

    region_name = (
        os.getenv("AWS_DEFAULT_REGION") 
        or os.getenv("AWS_REGION") 
        or os.getenv("BEDROCK_REGION") 
        or "us-east-1"
    )
    
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID") or None
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY") or None
    aws_session_token = os.getenv("AWS_SESSION_TOKEN") or None
    aws_profile = os.getenv("AWS_PROFILE") or None

    if not aws_profile and not (aws_access_key_id and aws_secret_access_key):
        log.warning("Bedrock will rely on the default AWS credential chain (env, profile, or role)")

    log.info("LLM provider=bedrock model=%s temperature=%s", model_id, temperature)

    return BedrockConverseChatModel(
        model_id=model_id,
        region_name=region_name,
        temperature=temperature,
        max_tokens=max_tokens,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        aws_profile=aws_profile,
    )


def _build_azure_openai(model: str, temperature: float, max_tokens: int):
    from langchain_openai import AzureChatOpenAI
    
    deployment_name = model or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if not deployment_name:
        raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME or LLM_MODEL must be set for Azure")

    raw_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("OPENAI_BASE_URL") or ""
    azure_endpoint = _normalize_resource_endpoint(raw_endpoint)
    if azure_endpoint and azure_endpoint != _clean_env_text(raw_endpoint).rstrip("/"):
        log.warning("Azure endpoint normalized to resource root: %s", azure_endpoint)

    if not azure_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT or OPENAI_BASE_URL must be set for Azure")

    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY or OPENAI_API_KEY must be set for Azure")

    log.info("LLM provider=azure model=%s temperature=%s", deployment_name, temperature)

    return AzureChatOpenAI(
        azure_deployment=deployment_name,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        temperature=temperature,
        max_tokens=max_tokens,
    )


_PROVIDERS = {
    "bedrock": _build_bedrock,
    "azure": _build_azure_openai,
}


def build_llm():
    """Build a chat model from env: LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS."""
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    model = os.getenv("LLM_MODEL", "")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    factory = _PROVIDERS.get(provider)
    if factory is None:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. "
            f"Supported: {', '.join(_PROVIDERS)}"
        )
    return factory(model, temperature, max_tokens)