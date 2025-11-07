# Multiline string input
input_text = """
- Ineffable: indescribable
- Pious
- Behold
- Epiphany
- Indolent
- Eschatology
- Serendipity
- Ineffable: indescribable
"""

words = [line.strip().lstrip('-').strip() for line in input_text.strip().splitlines()]

# Sort the words alphabetically, case-insensitive
words_sorted = sorted(words, key=lambda word: word.lower())
word_counts = {}
for word in words_sorted:
    word_counts[word] = word_counts.get(word, 0) + 1

# Identify any repeated words
repeated_words = [word for word, count in word_counts.items() if count > 1]
# Count non-repeated words
non_repeated_count = sum(1 for count in word_counts.values() if count == 1)

# Output the sorted list in the input format
print("Sorted words:")
for word in words_sorted:
    print(f"- {word}")

# Output any repeated words in the input format, if any
if repeated_words:
    print("\nRepeated words:")
    for word in repeated_words:
        print(f"- {word}")
else:
    print("\nNo repeated words found.")

# Output the count of non-repeated words
print(f"\nAmount of non-repeated words: {non_repeated_count}\n")