from sklearn.feature_extraction.text import TfidfVectorizer


def create_vectorizer():
    return TfidfVectorizer()


def extract_features(vectorizer, text):
    return vectorizer.transform(text)
