import spacy
import random
import numpy as np
import logging
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier

nlp = spacy.load('en_core_web_sm')

def preprocess(text):

    doc = nlp(text)
    lemmatized = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct]
    return ' '.join(lemmatized)

try:
    with open('responses.json', 'r') as file:
        data = json.load(file)

except FileNotFoundError:
    logging.error("Intent File not found.")
    data = {'intents':[]}

patterns = []
tags = []
responses = {}

#Extracting the patters, tags and responses from the responses.json file
for intent in data['intents']:
    for pattern in intent['patterns']:
        
        pattern = preprocess(pattern)
        patterns.append(pattern)

        tags.append(intent['tag'])
    
    responses[intent['tag']] = intent['responses']

#Transforming to tfidf vectors
vectorizer = TfidfVectorizer()
x = vectorizer.fit_transform(patterns)

#Encoding the tags to numerical codes
tag_to_code = {tag:i for i,tag in enumerate(set(tags))}
code_to_tag = {i:tag for tag,i in tag_to_code.items()}
y = np.array([tag_to_code[tag] for tag in tags])

#Train the model based on the tfidf which is in x and the numpy which is in y
model = MLPClassifier(hidden_layer_sizes=(50, 50), max_iter=1000, random_state=42, alpha=0.01)
model.fit(x,y)

def get_response(user_input, context):
    try:
        # Preprocess user input
        preprocessed_input = preprocess(user_input)
        input_vector = vectorizer.transform([preprocessed_input])

        # Predict intent
        predicted_code = model.predict(input_vector)[0]
        predicted_tag = code_to_tag.get(predicted_code, None)

        # Get response based on predicted intent
        if predicted_tag:
            response = random.choice(responses[predicted_tag])
            context["last_intent"] = predicted_tag  # Optional context tracking
        else:
            response = "I’m not sure I understand. Could you rephrase that or ask about our services?"
            context["last_intent"] = "fallback"

        return response, context

    except Exception as e:
        logging.error(f"Error in get_response: {e}")
        return "Something went wrong. Please try again!", context

if __name__ == '__main__':
    context = {}
    print("MASTA-BOT : Hello! How can I assist you with Samasta Groups today? (Type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye! Let us know if you need more IT help!")
            break
        response, context = get_response(user_input, context)
        print(f"Bot: {response}")