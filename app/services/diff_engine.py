"""
Core semantic difference analysis engine.

This module contains the DiffEngine class which orchestrates
LLM-powered semantic text comparison.
"""

import json
import logging
import difflib
import asyncio
from typing import Optional, AsyncGenerator, List, Tuple
from uuid import uuid4

from openai import AsyncOpenAI, OpenAIError, APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.models import (
    CompareRequest,
    DiffResponse,
    DiffSummary,
    ChangeItem,
    SemanticChangeLevel,
)
from app.utils.prompts import get_system_prompt, get_user_prompt
from app.services.cache import get_cache


# Configure logging
logger = logging.getLogger(__name__)


class DiffEngineError(Exception):
    """Base exception for DiffEngine errors."""
    pass


class LLMResponseError(DiffEngineError):
    """Raised when LLM response cannot be parsed or validated."""
    pass


class LLMAPIError(DiffEngineError):
    """Raised when OpenAI API call fails."""
    pass


class DiffEngine:
    """
    Semantic difference analysis engine powered by OpenAI LLM.
    
    This class handles all interaction with the LLM for semantic text comparison,
    including prompt construction, API calls, and response validation.
    """
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """
        Initialize the DiffEngine.
        
        Args:
            openai_client: Optional AsyncOpenAI client. If not provided, creates one.
        """
        self.client = openai_client or AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT
        )
        self.default_model = settings.DEFAULT_LLM_MODEL
        self.premium_model = settings.PREMIUM_LLM_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.cache = get_cache()
        
        logger.info(f"DiffEngine initialized with default model: {self.default_model}")
    
    async def analyze_diff(
        self,
        request: CompareRequest
    ) -> DiffResponse:
        """
        Analyze semantic differences between original and generated text.
        
        This is the main entry point for semantic analysis. It:
        1. Constructs appropriate prompts based on sensitivity level
        2. Calls the OpenAI API with JSON mode enabled
        3. Parses and validates the response
        4. Validates and fixes text spans to prevent broken indices
        5. Returns a structured DiffResponse
        
        Args:
            request: CompareRequest containing texts and sensitivity level.
            
        Returns:
            DiffResponse with summary and detailed changes.
            
        Raises:
            LLMAPIError: If the API call fails.
            LLMResponseError: If the response cannot be parsed or validated.
        """
        # Select model based on premium_mode flag (cost optimization)
        selected_model = self.premium_model if request.premium_mode else self.default_model
        
        logger.info(
            f"Starting semantic analysis with sensitivity={request.sensitivity.value}, "
            f"original_len={len(request.original_text)}, "
            f"generated_len={len(request.generated_text)}, "
            f"model={selected_model}, premium={request.premium_mode}"
        )
        
        # Check cache first
        cached_response = self.cache.get(
            request.original_text,
            request.generated_text,
            request.sensitivity.value
        )
        
        if cached_response:
            logger.info("Returning cached response (0ms, $0 cost)")
            return DiffResponse(**cached_response)
        
        # ZERO-COST SHORT-CIRCUIT: Check if texts are nearly identical
        similarity_ratio = difflib.SequenceMatcher(
            None,
            request.original_text,
            request.generated_text
        ).ratio()
        
        logger.debug(f"Text similarity ratio: {similarity_ratio:.4f}")
        
        # Use strict threshold from settings for cost optimization
        if similarity_ratio > settings.SHORT_CIRCUIT_THRESHOLD:
            logger.info(
                f"Texts are {similarity_ratio:.1%} identical (>{settings.SHORT_CIRCUIT_THRESHOLD:.0%}), "
                f"skipping LLM call (ZERO COST)"
            )
            response = DiffResponse(
                summary=DiffSummary(
                    is_safe=True,
                    risk_score=0,
                    semantic_change_level=SemanticChangeLevel.NONE
                ),
                changes=[]
            )
            
            # Cache the result
            self.cache.set(
                request.original_text,
                request.generated_text,
                request.sensitivity.value,
                response.model_dump()
            )
            
            return response
        
        # Check if texts are large enough to warrant chunking
        CHUNK_THRESHOLD = 4000  # Characters
        original_length = len(request.original_text)
        generated_length = len(request.generated_text)
        
        if original_length > CHUNK_THRESHOLD or generated_length > CHUNK_THRESHOLD:
            logger.info(
                f"Large texts detected (orig: {original_length}, gen: {generated_length}). "
                f"Using parallel chunking strategy."
            )
            return await self._analyze_with_chunking(request, selected_model)
        
        # Standard single-call analysis for smaller texts
        # Build prompts
        system_prompt = get_system_prompt(request.sensitivity.value)
        user_prompt = get_user_prompt(request.original_text, request.generated_text)
        
        try:
            # Call OpenAI API with JSON mode (with retry logic)
            response = await self._call_llm_with_retry(
                system_prompt,
                user_prompt,
                selected_model
            )
            
            # Extract the JSON response
            raw_content = response.choices[0].message.content
            
            if not raw_content:
                raise LLMResponseError("LLM returned empty response")
            
            logger.debug(f"Raw LLM response: {raw_content[:500]}...")
            
            # Parse JSON
            try:
                response_data = json.loads(raw_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                raise LLMResponseError(f"Invalid JSON from LLM: {e}")
            
            # Validate and fix spans before building response
            response_data = self._validate_and_fix_spans(
                response_data,
                request.original_text,
                request.generated_text
            )
            
            # Validate and convert to Pydantic models
            diff_response = self._validate_and_build_response(response_data)
            
            # Cache the successful response
            self.cache.set(
                request.original_text,
                request.generated_text,
                request.sensitivity.value,
                diff_response.model_dump()
            )
            
            logger.info(
                f"Analysis complete: risk_score={diff_response.summary.risk_score}, "
                f"change_level={diff_response.summary.semantic_change_level.value}, "
                f"changes_detected={len(diff_response.changes)}"
            )
            
            return diff_response
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMAPIError("Rate limit exceeded. Please try again later.")
        
        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {e}")
            raise LLMAPIError("Request timed out. Please try again.")
        
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMAPIError(f"API error: {e.message if hasattr(e, 'message') else str(e)}")
        
        except OpenAIError as e:
            logger.error(f"OpenAI client error: {e}")
            raise LLMAPIError(f"OpenAI client error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
            raise LLMAPIError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        reraise=True
    )
    async def _call_llm_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str
    ):
        """
        Call OpenAI API with automatic retry logic.
        
        Retries up to 3 times with exponential backoff on:
        - API timeouts
        - Rate limit errors
        - General API errors
        
        Args:
            system_prompt: System prompt for LLM.
            user_prompt: User prompt with texts to compare.
            model: Model to use (gpt-4o-mini or gpt-4o).
            
        Returns:
            OpenAI API response object.
            
        Raises:
            APITimeoutError: If all retries timeout.
            RateLimitError: If rate limited after retries.
            APIError: If API errors persist after retries.
        """
        logger.debug(f"Calling OpenAI API (model={model}, with retry logic)")
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )
        
        return response
    
    async def _analyze_with_chunking(self, request: CompareRequest, model: str) -> DiffResponse:
        """
        Analyze large texts using parallel chunking strategy (map-reduce).
        
        Strategy:
        1. Split texts into paragraph-based chunks
        2. Analyze chunks in parallel using asyncio.gather
        3. Merge results into single response
        4. Adjust risk score based on aggregate
        
        Args:
            request: CompareRequest with large texts.
            model: Model to use (gpt-4o-mini or gpt-4o).
            
        Returns:
            Merged DiffResponse from all chunks.
        """
        logger.info(f"Starting parallel chunking analysis (model={model})")
        
        # Split texts into chunks
        original_chunks = self._split_into_chunks(request.original_text)
        generated_chunks = self._split_into_chunks(request.generated_text)
        
        # Ensure same number of chunks (pad if needed)
        max_chunks = max(len(original_chunks), len(generated_chunks))
        
        while len(original_chunks) < max_chunks:
            original_chunks.append("")
        while len(generated_chunks) < max_chunks:
            generated_chunks.append("")
        
        logger.info(f"Split texts into {max_chunks} chunks for parallel processing")
        
        # Create tasks for parallel execution
        tasks = []
        for i, (orig_chunk, gen_chunk) in enumerate(zip(original_chunks, generated_chunks)):
            if not orig_chunk and not gen_chunk:
                continue
            
            chunk_request = CompareRequest(
                original_text=orig_chunk,
                generated_text=gen_chunk,
                sensitivity=request.sensitivity
            )
            
            tasks.append(self._analyze_single_chunk(chunk_request, chunk_index=i, model=model))
        
        # Execute in parallel
        logger.info(f"Executing {len(tasks)} chunk analyses in parallel")
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        merged_response = self._merge_chunk_results(chunk_results, original_chunks)
        
        # Cache the merged result
        self.cache.set(
            request.original_text,
            request.generated_text,
            request.sensitivity.value,
            merged_response.model_dump()
        )
        
        logger.info(
            f"Chunking analysis complete: {len(merged_response.changes)} total changes, "
            f"risk_score={merged_response.summary.risk_score}"
        )
        
        return merged_response
    
    def _split_into_chunks(self, text: str, max_chunk_size: int = 3000) -> List[str]:
        """
        Split text into chunks based on paragraph boundaries.
        
        Args:
            text: Text to split.
            max_chunk_size: Maximum characters per chunk.
            
        Returns:
            List of text chunks.
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        # Split by paragraphs (double newline)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > max_chunk_size and current_chunk:
                # Finalize current chunk
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length + 2  # +2 for \n\n
        
        # Add remaining
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    async def _analyze_single_chunk(
        self,
        chunk_request: CompareRequest,
        chunk_index: int,
        model: str
    ) -> DiffResponse:
        """
        Analyze a single chunk (used in parallel execution).
        
        Args:
            chunk_request: CompareRequest for this chunk.
            chunk_index: Index of this chunk (for logging).
            model: Model to use (gpt-4o-mini or gpt-4o).
            
        Returns:
            DiffResponse for this chunk.
        """
        try:
            logger.debug(f"Analyzing chunk {chunk_index} (model={model})")
            
            # Check cache for this specific chunk
            cached = self.cache.get(
                chunk_request.original_text,
                chunk_request.generated_text,
                chunk_request.sensitivity.value
            )
            
            if cached:
                return DiffResponse(**cached)
            
            # Build prompts
            system_prompt = get_system_prompt(chunk_request.sensitivity.value)
            user_prompt = get_user_prompt(
                chunk_request.original_text,
                chunk_request.generated_text
            )
            
            # Call LLM
            response = await self._call_llm_with_retry(system_prompt, user_prompt, model)
            raw_content = response.choices[0].message.content
            
            if not raw_content:
                raise LLMResponseError(f"Empty response for chunk {chunk_index}")
            
            response_data = json.loads(raw_content)
            
            # Validate spans
            response_data = self._validate_and_fix_spans(
                response_data,
                chunk_request.original_text,
                chunk_request.generated_text
            )
            
            # Build response
            diff_response = self._validate_and_build_response(response_data)
            
            # Cache chunk result
            self.cache.set(
                chunk_request.original_text,
                chunk_request.generated_text,
                chunk_request.sensitivity.value,
                diff_response.model_dump()
            )
            
            return diff_response
            
        except Exception as e:
            logger.error(f"Error analyzing chunk {chunk_index}: {e}")
            # Return empty response for failed chunk
            return DiffResponse(
                summary=DiffSummary(
                    is_safe=True,
                    risk_score=0,
                    semantic_change_level=SemanticChangeLevel.NONE
                ),
                changes=[]
            )
    
    def _merge_chunk_results(
        self,
        chunk_results: List[DiffResponse],
        original_chunks: List[str]
    ) -> DiffResponse:
        """
        Merge multiple chunk results into single response.
        
        Args:
            chunk_results: List of DiffResponse objects from chunks.
            original_chunks: Original text chunks (for offset calculation).
            
        Returns:
            Merged DiffResponse.
        """
        all_changes = []
        total_risk_score = 0
        max_change_level = SemanticChangeLevel.NONE
        
        # Calculate offsets for each chunk
        offsets = [0]
        for chunk in original_chunks[:-1]:
            offsets.append(offsets[-1] + len(chunk) + 2)  # +2 for \n\n
        
        # Merge changes and adjust indices
        for chunk_idx, result in enumerate(chunk_results):
            if isinstance(result, Exception):
                logger.warning(f"Chunk {chunk_idx} failed: {result}")
                continue
            
            offset = offsets[chunk_idx] if chunk_idx < len(offsets) else 0
            
            # Adjust span indices for global position
            for change in result.changes:
                change.original_span.start += offset
                change.original_span.end += offset
                change.generated_span.start += offset
                change.generated_span.end += offset
                all_changes.append(change)
            
            # Aggregate risk
            total_risk_score += result.summary.risk_score
            
            # Track highest change level
            if result.summary.semantic_change_level.value > max_change_level.value:
                max_change_level = result.summary.semantic_change_level
        
        # Calculate average risk score
        valid_chunks = len([r for r in chunk_results if not isinstance(r, Exception)])
        avg_risk_score = total_risk_score // valid_chunks if valid_chunks > 0 else 0
        
        # Determine safety
        has_critical = any(c.severity == "critical" for c in all_changes)
        is_safe = avg_risk_score <= 40 and not has_critical
        
        return DiffResponse(
            summary=DiffSummary(
                is_safe=is_safe,
                risk_score=min(100, avg_risk_score),
                semantic_change_level=max_change_level
            ),
            changes=all_changes
        )
    
    def _validate_and_fix_spans(
        self,
        response_data: dict,
        original_text: str,
        generated_text: str
    ) -> dict:
        """
        Validate and auto-correct text span indices using context-aware matching.
        
        Uses a three-phase validation strategy:
        1. Exact match: Check if text[start:end] matches expected text
        2. Context fingerprint: Use context_before + text + context_after to find correct location
        3. Proximity search: Search within ±50 chars of provided index as fallback
        
        This handles duplicate words by using surrounding context as a unique fingerprint.
        
        Args:
            response_data: Raw dictionary from LLM JSON response.
            original_text: The original text for validation.
            generated_text: The generated text for validation.
            
        Returns:
            Corrected response_data dictionary with validated spans.
        """
        if "changes" not in response_data:
            return response_data
        
        valid_changes = []
        removed_count = 0
        corrected_count = 0
        
        for change in response_data["changes"]:
            is_valid = True
            
            # Validate original_span
            if "original_span" in change and change["original_span"]:
                is_valid, corrected = self._validate_single_span(
                    change["original_span"],
                    original_text,
                    "original"
                )
                
                if corrected:
                    corrected_count += 1
                
                if not is_valid:
                    removed_count += 1
            
            # Validate generated_span
            if is_valid and "generated_span" in change and change["generated_span"]:
                is_valid, corrected = self._validate_single_span(
                    change["generated_span"],
                    generated_text,
                    "generated"
                )
                
                if corrected:
                    corrected_count += 1
                
                if not is_valid:
                    removed_count += 1
            
            # Add change only if valid
            if is_valid:
                valid_changes.append(change)
        
        # Update changes list
        response_data["changes"] = valid_changes
        
        if corrected_count > 0:
            logger.info(f"Auto-corrected {corrected_count} span indices")
        
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} hallucinated changes")
        
        return response_data
    
    def _validate_single_span(
        self,
        span: dict,
        source_text: str,
        span_type: str
    ) -> tuple[bool, bool]:
        """
        Validate a single text span using three-phase strategy.
        
        Phase 1: Exact match check
        Phase 2: Context fingerprint matching
        Phase 3: Proximity search (±50 chars)
        
        Args:
            span: Span dictionary with text, start, end, context_before, context_after.
            source_text: The source text to validate against.
            span_type: "original" or "generated" (for logging).
            
        Returns:
            Tuple of (is_valid, was_corrected).
        """
        text = span.get("text", "")
        start = span.get("start")
        end = span.get("end")
        context_before = span.get("context_before", "")
        context_after = span.get("context_after", "")
        
        if not text or start is None or end is None:
            return (True, False)  # Empty span, skip validation
        
        # Phase 1: Exact match check
        try:
            actual_text = source_text[start:end]
            if actual_text == text:
                logger.debug(f"{span_type} span exact match at [{start}:{end}]")
                return (True, False)  # Valid, no correction needed
        except IndexError:
            logger.warning(f"{span_type} span indices out of range: [{start}:{end}]")
        
        # Phase 2: Context fingerprint matching
        if context_before or context_after:
            fingerprint = context_before + text + context_after
            found_index = source_text.find(fingerprint)
            
            if found_index != -1:
                # Calculate new start/end based on context
                new_start = found_index + len(context_before)
                new_end = new_start + len(text)
                
                # Update span
                span["start"] = new_start
                span["end"] = new_end
                
                logger.info(
                    f"Context fingerprint match for {span_type} span: "
                    f"[{start}:{end}] -> [{new_start}:{new_end}]"
                )
                return (True, True)  # Valid, corrected
        
        # Phase 3: Proximity search (±50 chars radius)
        search_start = max(0, start - 50)
        search_end = min(len(source_text), end + 50)
        search_region = source_text[search_start:search_end]
        
        local_index = search_region.find(text)
        if local_index != -1:
            # Calculate absolute position
            new_start = search_start + local_index
            new_end = new_start + len(text)
            
            # Update span
            span["start"] = new_start
            span["end"] = new_end
            
            logger.info(
                f"Proximity search match for {span_type} span: "
                f"[{start}:{end}] -> [{new_start}:{new_end}]"
            )
            return (True, True)  # Valid, corrected
        
        # Phase 4: Global fallback (original simple find)
        global_index = source_text.find(text)
        if global_index != -1:
            span["start"] = global_index
            span["end"] = global_index + len(text)
            
            logger.warning(
                f"Global fallback match for {span_type} span: "
                f"[{start}:{end}] -> [{global_index}:{global_index + len(text)}] "
                f"(may be wrong if text appears multiple times)"
            )
            return (True, True)  # Valid, corrected (but risky)
        
        # All phases failed - hallucination detected
        logger.warning(
            f"{span_type} span text not found: '{text[:50]}...' "
            f"with context '{context_before}..{context_after}'. Removing change."
        )
        return (False, False)  # Invalid, not correctable
    
    def _validate_and_build_response(self, response_data: dict) -> DiffResponse:
        """
        Validate raw JSON response and build Pydantic models.
        
        Args:
            response_data: Raw dictionary from LLM JSON response.
            
        Returns:
            Validated DiffResponse object.
            
        Raises:
            LLMResponseError: If validation fails.
        """
        try:
            # Ensure UUIDs are generated for changes if not provided
            if "changes" in response_data:
                for change in response_data["changes"]:
                    if "id" not in change or not change["id"]:
                        change["id"] = str(uuid4())
            
            # Validate using Pydantic
            diff_response = DiffResponse(**response_data)
            
            # Additional validation: is_safe consistency check
            has_critical_changes = any(
                change.severity == "critical" for change in diff_response.changes
            )
            high_risk = diff_response.summary.risk_score > 40
            
            if has_critical_changes or high_risk:
                if diff_response.summary.is_safe:
                    logger.warning(
                        "Inconsistency detected: is_safe=True but risk_score > 40 or critical changes present. "
                        "Correcting to is_safe=False."
                    )
                    diff_response.summary.is_safe = False
            
            return diff_response
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            raise LLMResponseError(f"Invalid response structure: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            raise LLMResponseError(f"Failed to validate response: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Perform a health check by making a minimal API call.
        
        Returns:
            True if the API is accessible, False otherwise.
        """
        try:
            # Make a minimal API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Dependency injection function for FastAPI
async def get_diff_engine() -> AsyncGenerator[DiffEngine, None]:
    """
    FastAPI dependency to provide DiffEngine instance.
    
    Yields:
        DiffEngine instance.
    """
    engine = DiffEngine()
    try:
        yield engine
    finally:
        # Cleanup if needed (AsyncOpenAI client handles its own cleanup)
        pass
