"""LLM synthesis module for screenscribe."""

from litellm import Router, completion
import asyncio
from typing import List, Optional, Dict, Any
import base64
from pathlib import Path
import os
import logging
import json

from .models import AlignedContent, SynthesisResult
from .config import config
from .utils import load_prompt_template, format_prompt_template

logger = logging.getLogger(__name__)


class ContentSynthesizer:
    """Synthesizes frame and transcript content using LLM vision models."""
    
    def __init__(self, 
                 provider: str = "openai",
                 model: Optional[str] = None,
                 no_fallback: bool = False,
                 prompts_dir: Optional[Path] = None):
        """
        Initialize content synthesizer.
        
        Args:
            provider: LLM provider (openai, anthropic, etc.)
            model: Specific model name (optional)
            no_fallback: Disable fallback to other providers
            prompts_dir: Custom directory for prompt templates (optional)
        """
        self.provider = provider
        self.model = model
        self.no_fallback = no_fallback
        self.prompts_dir = prompts_dir or config.prompts_dir
        self.router = None
        self._prompt_template = None
        
        logger.info(f"ContentSynthesizer initialized: provider={provider}, model={model}, no_fallback={no_fallback}, prompts_dir={self.prompts_dir}")
        
        # Load prompt template
        self._load_prompt_template()
        
        # Setup LLM configuration
        self._setup_llm()
    
    def _load_prompt_template(self) -> None:
        """Load the synthesis prompt template from markdown file."""
        try:
            self._prompt_template = load_prompt_template("synthesis", self.prompts_dir)
            logger.info("Loaded synthesis prompt template")
        except Exception as e:
            logger.warning(f"Failed to load prompt template: {e}")
            # Fall back to hardcoded prompt
            self._prompt_template = """You are analyzing a technical video frame with its corresponding audio transcript.

Frame timestamp: {timestamp_str}
Transcript (±{time_window}s): "{transcript_text}"

Analyze this frame and create a structured summary that:
1. Describes what is visually shown
2. Explains how it relates to what is being said
3. Extracts key technical points or concepts
4. Notes any important visual elements (diagrams, code, charts)

Provide response in this JSON format:
{{
  "summary": "Brief synthesis of audio and visual content",
  "visual_description": "What is shown in the frame",
  "key_points": ["point 1", "point 2", ...]
}}"""
            logger.info("Using fallback hardcoded prompt template")
    
    def _setup_llm(self) -> None:
        """Setup LLM router or direct model configuration."""
        # Set environment variables for authentication
        if config.openai_api_key:
            os.environ['OPENAI_API_KEY'] = config.openai_api_key
        if config.anthropic_api_key:
            os.environ['ANTHROPIC_API_KEY'] = config.anthropic_api_key
        
        # Determine model name
        if self.model:
            primary_model = f"{self.provider}/{self.model}"
        else:
            # Default models for each provider
            model_defaults = {
                "openai": "gpt-4-vision-preview",
                "anthropic": "claude-3-sonnet-20240229"
            }
            primary_model = f"{self.provider}/{model_defaults.get(self.provider, 'gpt-4-vision-preview')}"
        
        if not self.no_fallback:
            # Setup router with fallbacks
            model_list = [
                {
                    "model_name": "primary",
                    "litellm_params": {
                        "model": primary_model,
                    },
                }
            ]
            
            # Add fallback if different from primary
            fallback_model = "openai/gpt-4-vision-preview"
            if primary_model != fallback_model:
                model_list.append({
                    "model_name": "fallback",
                    "litellm_params": {
                        "model": fallback_model,
                    },
                })
            
            try:
                self.router = Router(
                    model_list=model_list,
                    fallbacks=[{"primary": ["fallback"]}] if len(model_list) > 1 else [],
                    timeout=30,
                    retry_policy={"initial_retry_delay": 1, "max_retries": 3}
                )
                logger.info("LLM router configured with fallbacks")
            except Exception as e:
                logger.warning(f"Failed to setup router, using direct model: {e}")
                self.router = None
                self.primary_model = primary_model
        else:
            # Single provider, no fallback
            self.primary_model = primary_model
            logger.info(f"LLM configured for direct model: {self.primary_model}")
    
    async def synthesize_frame(self, aligned: AlignedContent) -> SynthesisResult:
        """Synthesize summary for a single frame with context."""
        logger.debug(f"Synthesizing frame at {aligned.frame.timestamp:.2f}s")
        
        try:
            # Encode image for vision models
            image_base64 = self._encode_image(aligned.frame.thumbnail_path)
            
            # Build prompt with transcript context
            transcript_text = aligned.get_transcript_text()
            
            prompt = self._build_synthesis_prompt(aligned, transcript_text)
            
            # Prepare messages for vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "low"  # Use "low" for cost efficiency
                            }
                        }
                    ]
                }
            ]
            
            # Make LLM request
            response = await self._make_llm_request(messages)
            
            # Parse response
            result_data = self._parse_llm_response(response)
            
            return SynthesisResult(
                frame_timestamp=aligned.frame.timestamp,
                summary=result_data.get("summary", ""),
                visual_description=result_data.get("visual_description"),
                key_points=result_data.get("key_points", [])
            )
            
        except Exception as e:
            logger.error(f"Synthesis error for frame at {aligned.frame.timestamp:.2f}s: {e}")
            # Return placeholder result
            return SynthesisResult(
                frame_timestamp=aligned.frame.timestamp,
                summary="[Error during synthesis]",
                visual_description="[Unable to analyze visual content]",
                key_points=[]
            )
    
    def _build_synthesis_prompt(self, aligned: AlignedContent, transcript_text: str) -> str:
        """Build the synthesis prompt using the loaded template."""
        try:
            return format_prompt_template(
                self._prompt_template,
                timestamp_str=aligned.frame.timestamp_str,
                time_window=aligned.time_window,
                transcript_text=transcript_text
            )
        except Exception as e:
            logger.error(f"Failed to format prompt template: {e}")
            # Fallback to basic prompt
            return f"Analyze this video frame at {aligned.frame.timestamp_str} with transcript: '{transcript_text}'"
    
    async def _make_llm_request(self, messages: List[Dict[str, Any]]) -> Any:
        """Make LLM request using router or direct model."""
        request_params = {
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        if self.router:
            # Use router
            response = await self.router.acompletion(
                model="primary",
                **request_params
            )
        else:
            # Use direct model
            response = await completion(
                model=self.primary_model,
                **request_params
            )
        
        return response
    
    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """Parse LLM response and extract JSON data."""
        try:
            content = response.choices[0].message.content
            result_data = json.loads(content)
            return result_data
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "summary": "[Unable to parse response]",
                "visual_description": "[Parse error]",
                "key_points": []
            }
    
    async def synthesize_all(self, 
                           aligned_content: List[AlignedContent],
                           max_concurrent: int = 5) -> List[SynthesisResult]:
        """Process all frames with concurrency limit."""
        logger.info(f"Synthesizing {len(aligned_content)} frames with max concurrency {max_concurrent}")
        
        # Semaphore for API rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(aligned):
            async with semaphore:
                return await self.synthesize_frame(aligned)
        
        # Create tasks for all frames
        tasks = [process_with_semaphore(a) for a in aligned_content]
        
        # Process with error handling
        results = []
        completed = 0
        
        for future in asyncio.as_completed(tasks):
            try:
                result = await future
                results.append(result)
                completed += 1
                
                if completed % 5 == 0:  # Log progress every 5 completions
                    logger.info(f"Synthesized {completed}/{len(tasks)} frames")
                    
            except Exception as e:
                logger.error(f"Synthesis task failed: {e}")
                # Create placeholder result
                results.append(SynthesisResult(
                    frame_timestamp=0,
                    summary="[Error during synthesis]"
                ))
        
        # Sort by timestamp
        results.sort(key=lambda r: r.frame_timestamp)
        logger.info(f"Synthesis complete: {len(results)} results")
        
        return results
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64."""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            raise RuntimeError(f"Image encoding failed: {e}")
    
    def get_synthesis_info(self) -> Dict[str, Any]:
        """Get information about the synthesizer configuration."""
        return {
            "provider": self.provider,
            "model": self.model,
            "no_fallback": self.no_fallback,
            "has_router": self.router is not None,
            "primary_model": getattr(self, 'primary_model', None)
        }