"""
stammer_hammer.py

Implements in Python the logic of Kevins jq stammer hammer:
https://github.com/WGBH-MLA/transcript_processing_scripts/blob/main/stammer_hammer_mmif.jq

(Written by Gemini based on the jq script abvoe.)
"""

from collections import defaultdict

def find_only_contiguous_repeating_sequences(chunk):
    words = [item["word"] for item in chunk]
    n = len(words)
    slices = []

    # 1. Generate all possible slices (Length 2 to n)
    for L in range(2, n + 1):
        for i in range(0, n - L + 1):
            pattern = tuple(words[i : i + L])
            slices.append({
                "pattern": pattern,
                "i": i,
                "L": L,
                "global_indices": [chunk[k]["global_idx"] for k in range(i, i + L)]
            })

    # 2. Group slices by pattern
    groups = defaultdict(list)
    for s in slices:
        groups[s["pattern"]].append(s)

    indices_to_remove = set()

    # 3. Filter groups matching contiguous repetition criteria
    for pattern, group in groups.items():
        if not group:
            continue

        filtered_group = []
        for j in range(len(group)):
            current = group[j]

            # Condition A: Single word repeated 3 or more times inside the pattern
            cond_a = (len(current["pattern"]) > 2) and (len(set(current["pattern"])) == 1)
            
            # Condition B: Next occurrence is perfectly contiguous
            cond_b = False
            if j + 1 < len(group):
                cond_b = (group[j + 1]["i"] == current["i"] + current["L"])

            # Condition C: Previous occurrence was perfectly contiguous
            cond_c = False
            if j - 1 >= 0:
                cond_c = (group[j - 1]["i"] == current["i"] - current["L"])

            if cond_a or cond_b or cond_c:
                filtered_group.append(current)

        # Drop the first iteration of the contiguous sequence (AAPB Policy)
        if len(filtered_group) > 1:
            for item in filtered_group[1:]:
                for idx in item["global_indices"]:
                    indices_to_remove.add(idx)

    return indices_to_remove

def blank_repeating_sequences(input_data):
    # Create a copy of the input data to avoid side-effects on the source array
    output_data = [list(item) for item in input_data]
    word_json_len = len(output_data)
    all_indices_to_remove = set()
    start = 0
    
    # Sliding Window Chunking (300 words window, 200 words step)
    while start < word_json_len:
        end = start + 300
        chunk = [
            {"word": output_data[k][2], "global_idx": k} 
            for k in range(start, min(end, word_json_len))
        ]
        
        if chunk:
            indices = find_only_contiguous_repeating_sequences(chunk)
            all_indices_to_remove.update(indices)
            
        start += 200

    # Text Blanking (replaces characters with spaces, preserving original length)
    for idx in all_indices_to_remove:
        original_word = output_data[idx][2]
        output_data[idx][2] = " " * len(original_word)

    return output_data