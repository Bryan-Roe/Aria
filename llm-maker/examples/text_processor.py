"""
Example Tool: Text Processor
Demonstrates string manipulation tool
"""
import re
from typing import List

def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text
    
    Args:
        text: Input text to search
        
    Returns:
        List of email addresses found
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return list(set(emails))  # Remove duplicates


def count_words(text: str) -> dict:
    """
    Count word occurrences in text
    
    Args:
        text: Input text
        
    Returns:
        Dictionary of word counts
    """
    words = re.findall(r'\b\w+\b', text.lower())
    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    return counts


# Example usage:
if __name__ == "__main__":
    sample_text = "Contact us at support@example.com or sales@example.org"
    print("Emails found:", extract_emails(sample_text))
    
    sample_text2 = "The quick brown fox jumps over the lazy dog"
    print("Word counts:", count_words(sample_text2))
