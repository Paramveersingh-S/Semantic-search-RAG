import spacy
from typing import List

# Ensure you have model downloaded: python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")

def semantic_chunk(text: str, tokenizer, max_tokens: int = 512, overlap: int = 64) -> List[str]:
    """
    Token-aware sliding window with sentence boundary detection.
    Never split in the middle of a sentence.
    Return chunks with overlap for context continuity.
    """
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        tokens = tokenizer.encode(sentence, add_special_tokens=False)
        sent_len = len(tokens)
        
        if current_length + sent_len > max_tokens and current_chunk:
            # Join current chunk and add to list
            chunks.append(" ".join(current_chunk))
            
            # Start new chunk with overlap
            # We approximate overlap by picking the last few sentences
            overlap_length = 0
            overlap_chunk = []
            for s, s_toks in reversed(list(zip(current_chunk, [tokenizer.encode(c, add_special_tokens=False) for c in current_chunk]))):
                if overlap_length + len(s_toks) <= overlap:
                    overlap_chunk.insert(0, s)
                    overlap_length += len(s_toks)
                else:
                    break
                    
            current_chunk = overlap_chunk
            current_length = overlap_length
            
        current_chunk.append(sentence)
        current_length += sent_len
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks
