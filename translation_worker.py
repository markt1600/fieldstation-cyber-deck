"""CPU translation using Argos models; no network access or text persistence."""
import json
import re
import sys
from pathlib import Path
import ctranslate2
import sentencepiece

ROOT = Path('/media/library/Tools/Translation/models')

def direct(text, source, target):
    root = ROOT/(source+'_'+target)
    tokenizer = sentencepiece.SentencePieceProcessor(model_file=str(root/'sentencepiece.model'))
    translator = ctranslate2.Translator(str(root/'model'), device='cpu', compute_type='int8', inter_threads=1, intra_threads=3)
    paragraphs = []
    for paragraph in text.split('\n'):
        if not paragraph.strip(): paragraphs.append(''); continue
        # Bound each input independently, preserving paragraph boundaries.
        chunks = []
        for sentence in re.split(r'(?<=[.!?。！？])\s*', paragraph):
            tokens = tokenizer.encode(sentence, out_type=str)
            chunks.extend(tokens[i:i+192] for i in range(0, len(tokens), 192))
        if not chunks: paragraphs.append(''); continue
        results = translator.translate_batch(chunks, beam_size=4, max_decoding_length=384)
        paragraphs.append(('' if target == 'ja' else ' ').join(tokenizer.decode(r.hypotheses[0]).replace('▁', ' ').strip() for r in results))
    return '\n'.join(paragraphs)

if __name__ == '__main__':
    request = json.load(sys.stdin)
    source, target, text = request['source'], request['target'], request['text']
    pivot = source != 'en' and target != 'en'
    if pivot: text = direct(text, source, 'en'); source = 'en'
    print(json.dumps({'text': direct(text, source, target), 'pivot': pivot}, ensure_ascii=False))
