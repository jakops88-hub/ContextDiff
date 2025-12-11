"""
Text processing utilities for sanitization and normalization.

This module handles text preprocessing to ensure consistency between
LLM analysis and client-side usage.
"""

import re
import unicodedata
from typing import Optional


class TextSanitizer:
    """
    Text sanitization utility for normalizing input text.
    
    Ensures consistent text representation across the entire pipeline:
    - LLM sees the same text format
    - Index calculations are accurate
    - Client receives the same sanitized version
    """
    
    @staticmethod
    def clean(text: str) -> str:
        """
        Sanitize and normalize text to prevent index mismatches.
        
        Performs the following operations:
        1. Unicode normalization (NFKC) - converts smart quotes, non-breaking spaces, etc.
        2. Remove invisible characters (zero-width spaces, control characters)
        3. Standardize line breaks (convert \\r\\n to \\n)
        4. Normalize whitespace (collapse multiple spaces)
        
        Args:
            text: Raw input text to sanitize.
            
        Returns:
            Sanitized text with normalized encoding and whitespace.
            
        Example:
            >>> raw = "Smart "quotes" and\u200bzero-width\r\nspaces"
            >>> TextSanitizer.clean(raw)
            'Smart "quotes" and zero-width\\nspaces'
        """
        if not text:
            return text
        
        # Step 1: Unicode normalization
        # NFKC = Compatibility decomposition, followed by canonical composition
        # Converts characters like ﬁ (ligature) to fi, ' (smart quote) to ', etc.
        text = unicodedata.normalize('NFKC', text)
        
        # Step 2: Remove invisible and control characters
        # Keep only printable characters plus whitespace (space, tab, newline)
        text = TextSanitizer._remove_invisible_chars(text)
        
        # Step 3: Standardize line breaks
        # Convert Windows (CRLF) to Unix (LF)
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Step 4: Normalize whitespace (optional - be careful not to break intentional spacing)
        # Collapse multiple spaces into single space (but preserve single newlines)
        text = re.sub(r' +', ' ', text)  # Multiple spaces -> single space
        text = re.sub(r'\n{3,}', '\n\n', text)  # More than 2 newlines -> 2 newlines
        
        return text
    
    @staticmethod
    def _remove_invisible_chars(text: str) -> str:
        """
        Remove invisible Unicode characters that can break index matching.
        
        Removes:
        - Zero-width space (U+200B)
        - Zero-width non-joiner (U+200C)
        - Zero-width joiner (U+200D)
        - Soft hyphen (U+00AD)
        - Other control characters (except tab, newline, carriage return)
        
        Args:
            text: Text to process.
            
        Returns:
            Text without invisible characters.
        """
        # Define characters to keep
        # Keep: space, tab (\t), newline (\n), carriage return (\r)
        allowed_chars = []
        
        for char in text:
            category = unicodedata.category(char)
            
            # Keep printable characters
            if category[0] != 'C':  # Not a control character
                allowed_chars.append(char)
            # Keep specific whitespace control characters
            elif char in ('\t', '\n', '\r'):
                allowed_chars.append(char)
            # Remove all other control characters (including zero-width spaces)
            # This includes:
            # - Cc (control characters)
            # - Cf (format characters like zero-width spaces)
            # - Cs (surrogates)
            # - Co (private use)
            # - Cn (not assigned)
        
        return ''.join(allowed_chars)
    
    @staticmethod
    def validate_length(text: str, max_length: int = 20000) -> tuple[bool, Optional[str]]:
        """
        Validate text length against maximum limit.
        
        Args:
            text: Text to validate.
            max_length: Maximum allowed character count.
            
        Returns:
            Tuple of (is_valid, error_message).
            If valid, error_message is None.
            
        Example:
            >>> is_valid, error = TextSanitizer.validate_length("short", 20000)
            >>> is_valid
            True
            >>> is_valid, error = TextSanitizer.validate_length("x" * 25000, 20000)
            >>> is_valid
            False
        """
        length = len(text)
        
        if length > max_length:
            return (
                False,
                f"Text length ({length:,} characters) exceeds maximum limit "
                f"of {max_length:,} characters. Please shorten the text."
            )
        
        return (True, None)
    
    @staticmethod
    def get_context(
        text: str,
        start: int,
        end: int,
        context_chars: int = 5
    ) -> tuple[str, str]:
        """
        Extract context before and after a text span.
        
        Used for creating unique fingerprints when validating spans.
        
        Args:
            text: Source text.
            start: Start index of target span.
            end: End index of target span.
            context_chars: Number of characters to extract before/after.
            
        Returns:
            Tuple of (context_before, context_after).
            
        Example:
            >>> text = "The word is here in the text"
            >>> start, end = 12, 16  # "here"
            >>> before, after = TextSanitizer.get_context(text, start, end, 5)
            >>> before
            "rd is"
            >>> after
            " in t"
        """
        # Extract context before (max context_chars)
        context_before = text[max(0, start - context_chars):start]
        
        # Extract context after (max context_chars)
        context_after = text[end:min(len(text), end + context_chars)]
        
        return (context_before, context_after)


# Convenience functions for direct use
def sanitize_text(text: str) -> str:
    """
    Convenience function for text sanitization.
    
    Args:
        text: Text to sanitize.
        
    Returns:
        Sanitized text.
    """
    return TextSanitizer.clean(text)


def validate_text_length(text: str, max_length: int = 20000) -> tuple[bool, Optional[str]]:
    """
    Convenience function for text length validation.
    
    Args:
        text: Text to validate.
        max_length: Maximum character count.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    return TextSanitizer.validate_length(text, max_length)
