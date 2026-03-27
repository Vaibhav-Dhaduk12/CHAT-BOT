"""
LLM Response Generation Module

Features:
- Provider abstraction: Gemini (google), OpenAI, Hugging Face
- Context-aware response generation using RAG
- Temperature control for response consistency
- Error handling and fallback responses
"""

import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        query: str,
        context: List[Dict],
        max_tokens: int = 500
    ) -> str:
        """Generate a response based on query and context."""
        pass


class GoogleGeminiLLMProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, api_key: str = settings.GEMINI_API_KEY, model: str = settings.GEMINI_LLM_MODEL):
        if genai is None:
            raise ImportError("google-genai not installed. Run: pip install google-genai")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = settings.GEMINI_LLM_TEMPERATURE
        logger.info(f"Initialized Gemini LLM: {model}")
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict],
        max_tokens: int = 500
    ) -> str:
        """Generate response using Google Gemini."""
        try:
            # Build context string
            context_text = self._format_context(context)
            
            # Build prompt
            prompt = self._build_prompt(query, context_text)
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "max_output_tokens": max_tokens,
                    "temperature": self.temperature,
                },
            )
            
            response_text = getattr(response, "text", None)
            if response_text:
                logger.debug(f"Generated response: {response_text[:100]}...")
                return response_text.strip()
            else:
                return self._fallback_response(query, context)
        
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            return self._fallback_response(query, context)
    
    def _format_context(self, context: List[Dict]) -> str:
        """Format retrieved context for the prompt."""
        if not context:
            return "No relevant information found."
        
        formatted = []
        for i, item in enumerate(context[:4], 1):  # Use top 4 results
            text = item.get("text", "").strip()
            source = item.get("metadata", {}).get("source_url", "")
            
            if text:
                formatted.append(f"Source {i}:")
                formatted.append(text)
                if source:
                    formatted.append(f"(From: {source})")
                formatted.append("")
        
        return "\n".join(formatted) if formatted else "No relevant information found."
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for the LLM."""
        return f"""You are an expert LIMS (Laboratory Information Management System) assistant.

    Your job:
    - Explain lab results in plain language
    - Identify abnormal values and possible implications
    - Suggest practical next actions (repeat test, dilution, validation, escalation)
    - Answer naturally like a human assistant

CONTEXT:
{context}

    QUESTION:
    {query}

INSTRUCTIONS:
- Answer naturally and conversationally
    - Base your answer only on the provided context
    - Do not mention "context" or "retrieval" in your reply
    - If abnormal values are present, explain what they may mean clearly
    - If information is not available, say so politely and ask a clarifying follow-up
    - Keep answers concise (2-4 short lines)

ANSWER:"""
    
    def _fallback_response(self, query: str, context: List[Dict]) -> str:
        """Generate a simple fallback response when LLM fails."""
        if context and len(context) > 0:
            top_result = context[0].get("text", "")[:200]
            if top_result:
                return f"Based on our knowledge base: {top_result}..."
        
        return "I couldn't find specific information about that. Could you please rephrase your question or contact our support team for assistance?"


class OpenAILLMProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str = settings.OPENAI_API_KEY, model: str = settings.OPENAI_LLM_MODEL):
        if OpenAI is None:
            raise ImportError("openai not installed. Run: pip install openai")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = settings.OPENAI_LLM_TEMPERATURE
        logger.info(f"Initialized OpenAI LLM: {model}")
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict],
        max_tokens: int = 500
    ) -> str:
        """Generate response using OpenAI."""
        try:
            context_text = self._format_context(context)
            prompt = self._build_prompt(query, context_text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert LIMS assistant that explains laboratory results clearly and safely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return self._fallback_response(query, context)
        
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {e}")
            return self._fallback_response(query, context)
    
    def _format_context(self, context: List[Dict]) -> str:
        """Format retrieved context for the prompt."""
        if not context:
            return "No relevant information found."
        
        formatted = []
        for i, item in enumerate(context[:4], 1):
            text = item.get("text", "").strip()
            source = item.get("metadata", {}).get("source_url", "")
            
            if text:
                formatted.append(f"Source {i}:")
                formatted.append(text)
                if source:
                    formatted.append(f"(From: {source})")
                formatted.append("")
        
        return "\n".join(formatted) if formatted else "No relevant information found."
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for the LLM."""
        return f"""You are an expert LIMS (Laboratory Information Management System) assistant.

    Your job:
    - Explain lab results in plain language
    - Identify abnormal values and possible implications
    - Suggest practical next actions (repeat test, dilution, validation, escalation)
    - Answer naturally like a human assistant

CONTEXT:
{context}

    QUESTION:
    {query}

    INSTRUCTIONS:
    - Base your answer only on the provided context
    - Do not mention "context" or "retrieval" in your reply
    - If abnormal values are present, explain what they may mean clearly
    - If information is not available, say so politely and ask a clarifying follow-up
    - Keep answers concise (2-4 short lines)

    ANSWER:"""
    
    def _fallback_response(self, query: str, context: List[Dict]) -> str:
        """Generate a simple fallback response when LLM fails."""
        if context and len(context) > 0:
            top_result = context[0].get("text", "")[:200]
            if top_result:
                return f"Based on our knowledge base: {top_result}..."
        
        return "I couldn't find specific information about that. Could you please rephrase your question or contact our support team for assistance?"


class LLMManager:
    """Manages LLM response generation."""
    
    def __init__(self, provider: str = None):
        """Initialize LLM manager with specified provider."""
        self.provider_name = provider or settings.EMBEDDING_PROVIDER
        
        # Prefer explicit provider selection, then fallback safely.
        try:
            if self.provider_name == "google":
                self.provider = GoogleGeminiLLMProvider()
            elif self.provider_name == "openai":
                self.provider = OpenAILLMProvider()
            else:
                if genai is not None and settings.GEMINI_API_KEY:
                    self.provider = GoogleGeminiLLMProvider()
                elif OpenAI is not None and settings.OPENAI_API_KEY:
                    self.provider = OpenAILLMProvider()
                else:
                    raise ValueError("No LLM provider configured")
        except ValueError as e:
            logger.warning(f"Could not initialize LLM provider: {e}")
            logger.warning("Defaulting to fallback responses")
            self.provider = None
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict],
        max_tokens: int = 500
    ) -> str:
        """Generate a response using the configured LLM."""
        if not self.provider:
            # Fallback without LLM
            if context and len(context) > 0:
                top_result = context[0].get("text", "")[:200]
                if top_result:
                    return f"Based on our records: {top_result}..."
            return "I don't have information about that. Please contact support."
        
        return await self.provider.generate_response(query, context, max_tokens)
