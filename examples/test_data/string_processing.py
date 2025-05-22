from typing import List, Dict
import re

def process_text(text: str) -> Dict[str, int]:
    """Process text and return word frequency statistics."""
    # Convert to lowercase and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count word frequencies
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    return word_freq

def find_patterns(text: str, patterns: List[str]) -> Dict[str, List[str]]:
    """Find all occurrences of given patterns in text."""
    results = {}
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        results[pattern] = [match.group() for match in matches]
    
    return results

def main():
    # Test text processing
    sample_text = """
    The quick brown fox jumps over the lazy dog.
    The fox is quick and brown, while the dog is lazy.
    """
    
    # Get word frequencies
    frequencies = process_text(sample_text)
    print("Word frequencies:")
    for word, count in sorted(frequencies.items()):
        print(f"{word}: {count}")
    
    # Find patterns
    patterns = [
        r'\b\w{4}\b',  # 4-letter words
        r'\bthe\b',    # occurrences of 'the'
        r'\b\w+ing\b'  # words ending in 'ing'
    ]
    
    pattern_matches = find_patterns(sample_text, patterns)
    print("\nPattern matches:")
    for pattern, matches in pattern_matches.items():
        print(f"{pattern}: {matches}")

if __name__ == "__main__":
    main() 