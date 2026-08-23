import os
import sys
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing import clean_text
from feature_extraction import create_vectorizer

# Load dataset
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_FILE = os.path.join(
    BASE_DIR,
    "dataset",
    "emails.csv"
)

data = pd.read_csv(DATASET_FILE)

# Clean email text
data["text"] = data["text"].apply(clean_text)

X = data["text"]
y = data["label"]


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Create TF-IDF vectorizer
vectorizer = create_vectorizer()

X_train_features = vectorizer.fit_transform(X_train)
X_test_features = vectorizer.transform(X_test)


# Create and train model
model = MultinomialNB()

model.fit(X_train_features, y_train)


# Test model
predictions = model.predict(X_test_features)

accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)


# Function to classify a new email
def classify_email(email_text):

    cleaned_email = clean_text(email_text)

    features = vectorizer.transform([cleaned_email])

    prediction = model.predict(features)

    return prediction[0]


# Test new email
if __name__ == "__main__":

    email = input("\nEnter an email to classify: ")

    result = classify_email(email)

    print("\nClassification:", result)
