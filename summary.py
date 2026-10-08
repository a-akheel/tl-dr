"""Frequency-based extractive summaries: retain original wording and order."""
from collections import Counter

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

lemmatizer = WordNetLemmatizer()


def clean_text(text):
    excluded = set(stopwords.words("english"))
    return [lemmatizer.lemmatize(word.lower()) for word in word_tokenize(text)
            if word.isalnum() and word.lower() not in excluded]


def summarize(text, title="", n=7):
    if n < 1:
        raise ValueError("Summary length must be positive.")
    if not text.strip():
        return []
    sentences = sent_tokenize(text)
    tokens = [clean_text(sentence) for sentence in sentences]
    frequencies = Counter(word for words in tokens for word in words)
    title_words = set(clean_text(title)) if title else set()
    scores = []
    for index, words in enumerate(tokens):
        score = sum(frequencies[word] for word in words) / max(len(words), 1)
        if title_words:
            score *= 1 + len(title_words.intersection(words)) / len(title_words)
        scores.append((index, score))
    selected = sorted(index for index, _ in sorted(scores, key=lambda row: -row[1])[:n])
    return [sentences[index] for index in selected]


def word_count(text):
    return sum(word.isalnum() for word in word_tokenize(text))


def getPercentage(text, final_sentences):
    original = word_count(text)
    if original == 0:
        return 0
    return round(100 * (1 - word_count(" ".join(final_sentences)) / original))


def getTopWords(text, n=5):
    return [word.capitalize() for word, _ in Counter(clean_text(text)).most_common(n)]
