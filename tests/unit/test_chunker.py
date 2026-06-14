import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../services/processing')))
from chunker import semantic_chunk

class MockTokenizer:
    def encode(self, text, add_special_tokens=False):
        return text.split()

def test_semantic_chunk():
    tokenizer = MockTokenizer()
    text = "This is sentence one. This is sentence two. This is sentence three."
    
    # Very small max_tokens to force chunking
    chunks = semantic_chunk(text, tokenizer, max_tokens=10, overlap=4)
    
    assert len(chunks) > 1
    assert "This is sentence one." in chunks[0]
