"""AI Service - abstracts LLM provider"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AIService:
    """
    AI Service abstracts external LLM providers.
    
    Currently supports OpenAI. Future support for KisanSLM or other providers.
    """

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize AI Service
        
        Args:
            provider: LLM provider ('openai', 'kisanslm', etc.)
            api_key: API key for the provider
        """
        self.provider = provider
        self.api_key = api_key

        if provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required")
            try:
                import openai
                openai.api_key = api_key
                self.client = openai.ChatCompletion
            except ImportError:
                raise ImportError("openai package not installed")
        elif provider == "kisanslm":
            # KisanSLM support (currently frozen)
            logger.warning("KisanSLM provider not yet stable for this sprint")
            self.client = None
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            
        Returns:
            Generated response
        """
        if self.provider == "openai":
            return await self._generate_openai(
                prompt, system_prompt, max_tokens, temperature
            )
        elif self.provider == "kisanslm":
            raise NotImplementedError("KisanSLM generation not stable yet")
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """Generate using OpenAI"""
        try:
            import openai

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """Synchronous chat (for non-async contexts)"""
        if self.provider == "openai":
            return self._chat_openai(prompt, system_prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _chat_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """Synchronous OpenAI chat"""
        try:
            import openai

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")
            raise
