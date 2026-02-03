"""Ollama Client"""

from typing import List, Dict, Any, Optional
import ollama
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Ollama Client"""

    def __init__(self, model_name: str = None):
        """Initialize Ollama client"""

        self.model_name = model_name or settings.OLLAMA_MODEL
        logger.info("Initializing Ollama client with model: %s", self.model_name)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Generate text using ollama"""

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({"role": "user", "content": prompt})

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"temperature": temperature, "num_predict": max_tokens},
            )

            answer = response["message"]["content"]
            logger.info("Generated response(tokens: %s)", len(answer.split()))

            return answer

        except Exception as e:
            logger.error("Error generating response: %s", e)
            raise

    def generate_with_context(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate text using ollama with context"""

        try:
            context_parts = []
            for idx, doc in enumerate(context_documents, 1):
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                source = metadata.get("source", "Unknown")
                page = metadata.get("page", "")
                page_info = f"(Page{page})" if page else ""
                context_parts.append(f"Document {idx}: {source} {page_info}\n{content}")

            context_text = "\n\n".join(context_parts)

            # Build system prompt

            system_prompt = """You are a helpful AI assistant. Answer the user's question based on the provided context documents.
            Rules: 
            1. Answer based ONLY on the information in the provided context.
            2. If the context does not contain enough information to answer the question, respond with 'I don't know'.
            3. Be concise and accurate in your answer, by thinking and analyzing the context documents carefully and thoroughly.
            4. Cite with source(s) you used in your answer
            5. If asked about something not in the context, politely say you don't have that information and you are just a AI assistant created to help understand your queries with any documents."""

            # Build user prompt

            user_prompt = f"""Context Documents: {context_text}
            Question: {query}

            Please provide a concise and accurate answer based on the context above."""

            # Generate response
            answer = self.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                temperature=0.7,
                max_tokens=1500,
            )

            return {
                "answer": answer,
                "context_used": len(context_documents),
                "model": self.model_name,
            }

        except Exception as e:
            logger.error("Error generating response:%s", e)
            raise
