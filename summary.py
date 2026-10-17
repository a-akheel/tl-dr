from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktTrainer
from nltk.stem import WordNetLemmatizer
from collections import OrderedDict
from itertools import islice
from operator import itemgetter

lemmatizer = WordNetLemmatizer()
pcts = r'''!()-[]{};:'"\,“”’``''<>./?@#$%^&*_~''' + "'s"


def clean_text(text):

	stop_words = set(stopwords.words('english'))
	text = text.lower()
	tokens = word_tokenize(text)

	words = [w for w in tokens if w not in stop_words]
	words = [w for w in words if w not in pcts]

	return words


def score_words(text):

	unique = []
	imp_words = clean_text(text)
	score = {}
	
	for w in imp_words:
		#print(w)
		w = lemmatizer.lemmatize(w)
		if w not in unique:
			unique.append(w)
			score[w] = 1

		elif w in unique:
			score[w] += 1

	return [score, unique]

def score_sentences(text, word_scores, unique):

	trainer = PunktTrainer()
	trainer.INCLUDE_ALL_COLLOCS = True
	trainer.train(text)
	sent_score = {}
	
	sent_tokenizer = PunktSentenceTokenizer(trainer.get_params())
	sentences = sent_tokenizer.tokenize(text.lower())

	for s in sentences:
		words = clean_text(s)
		sent_score[s] = 0

		for w in words:
			w = lemmatizer.lemmatize(w)
			if w in unique:
				sent_score[s] += word_scores[w]

	return sent_score


def similarity_score(t, s):

	tt = clean_text(t)
	st = clean_text(s)
	count = 0

	for w in st:
		if w in tt:
			count += 1

	ratio = count / len(tt) if tt else 0

	return ratio


def rank_sentences(text, sentence_scores, title="", n=7):

	final_sentences = []

	trainer = PunktTrainer()
	trainer.INCLUDE_ALL_COLLOCS = True
	trainer.train(text)	
	sent_tokenizer = PunktSentenceTokenizer(trainer.get_params())

	for s in sentence_scores:
		if title == "":
			break
		else:
			sentence_scores[s] *= (1 + similarity_score(title, s))

	sc = sentence_scores.copy()
	sc = OrderedDict(sorted(sc.items(), key=lambda t: t[1], reverse=True))
	ordered_sents = dict(islice(sc.items(), n))

	proper_sentences = sent_tokenizer.tokenize(text)

	for s in proper_sentences:
		if s.lower() in ordered_sents:
			final_sentences.append(s)

	return final_sentences


def summarize(text, title="", n=7):

	word_scores, unique_words = score_words(text)
	sentence_scores = score_sentences(text, word_scores, unique_words)
	final_sentences = rank_sentences(text, sentence_scores, title, n)

	return final_sentences

def getPercentage(text, final_sentences):

	stext = ""
	for s in final_sentences:
		stext += s

	TextWordCount = word_tokenize(text)
	words = [w for w in TextWordCount if w not in pcts]
	wcount0 = len(words)

	FinalWordCount = word_tokenize(stext)
	wds = [w for w in FinalWordCount if w not in pcts]
	wcount1 = len(wds)

	per = round(((wcount0 - wcount1) / wcount0) * 100) if wcount0 else 0

	return per

def getTopWords(text, n=5):

	score, unique = score_words(text)
	topWords = dict(sorted(score.items(), key=itemgetter(1), reverse=True)[:n])
	tpWords = []
	for word in topWords:
		tpWords.append(word.capitalize())
	return tpWords
