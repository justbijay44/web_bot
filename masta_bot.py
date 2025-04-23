import spacy
import random
import numpy as np
import logging
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from textblob import TextBlob
import re

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for development

# Setting a logging to track interactions and errors
logging.basicConfig(filename='chatbot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


nlp = spacy.load('en_core_web_sm')

def preprocess(text):
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Correct spelling
    blob = TextBlob(text)
    text = str(blob.correct())
    
    # Lemmatize and remove stop words
    doc = nlp(text)
    lemmatized = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    
    # Join words back into a string
    return ' '.join(lemmatized) if lemmatized else text

try:
    with open('responses.json', 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    logging.error("Intent File not found.")
    print("Error: Intent file not found. Please ensure 'responses.json' exists.")
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
unique_tags = list(set(tags))
tag_to_code = {tag:i for i,tag in enumerate(unique_tags)}
code_to_tag = {i:tag for tag,i in tag_to_code.items()}
y = np.array([tag_to_code[tag] for tag in tags])

#Train the model based on the tfidf which is in x and the numpy which is in y
model = MLPClassifier(hidden_layer_sizes=(50, 50), max_iter=1000, random_state=42, alpha=0.01)
model.fit(x,y)

def get_response(user_input, context):
    if not user_input or len(user_input.strip()) == 0:
        return "How can I assist you today!", context
    if len(user_input) > 200:
        return "That's a bit long! Could you keep it shorter?", context

    try:
        # Get sentiment of the input
        sentiment = TextBlob(user_input).sentiment.polarity
        
        preprocessed_input = preprocess(user_input)
        input_vector = vectorizer.transform([preprocessed_input])
        
        # Get prediction probabilities
        prediction_probs = model.predict_proba(input_vector)[0]
        predicted_code = model.predict(input_vector)[0]
        predicted_tag = code_to_tag.get(predicted_code, None)
        
        # Get confidence score
        confidence = prediction_probs[predicted_code]
        
        logging.info(f"User input: {user_input} | Predicted intent: {predicted_tag} | Confidence: {confidence:.2f} | Sentiment: {sentiment:.2f}")

        # Check for pricing-related keywords in the input
        pricing_keywords = ['price', 'cost', 'how much', 'pricing', 'budget', 'rate', 'quote']
        is_pricing_question = any(keyword in user_input.lower() for keyword in pricing_keywords)

        # Handle low confidence predictions
        if confidence < 0.5:
            if sentiment < -0.3:
                response = "I sense you might be frustrated. Let me help you better. Could you try rephrasing your question?"
            else:
                response = "I'm not entirely sure what you mean. Could you try asking in a different way?"
            context["last_intent"] = "fallback"
            return response, context

        if predicted_tag:
            # If it's a pricing question for any service, provide pricing response
            if is_pricing_question:
                response = "Pricing varies based on your specific needs and requirements. For a detailed quote, please contact us at info@samastagroups.com or call +977 9844874516. We'll be happy to discuss your project and provide a customized pricing plan."
            elif predicted_tag == "follow_up" and context.get("last_intent"):
                last_tag = context["last_intent"]
                if last_tag == "list_services":
                    response = "I just listed our services—want details on one, like 'cloud solutions' or 'custom software'?"
                else:
                    response = random.choice(responses[last_tag]) + " Anything else you'd like to know?"
            else:
                response = random.choice(responses[predicted_tag])
            
            # Add sentiment-aware follow-up
            if sentiment < -0.3:
                response += " I want to make sure I understand your needs correctly. Could you tell me more?"
            elif sentiment > 0.3:
                response += " I'm glad you're interested! What else would you like to know?"
                
            context["last_intent"] = predicted_tag
        else:
            response = "I'm not sure I understand. Could you rephrase that or ask about our services?"
            context["last_intent"] = "fallback"

        return response, context
    except Exception as e:
        logging.error(f"Error in get_response: {str(e)}")
        return "Something went wrong. Please try again!", context

# Flask routes
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        context = data.get('context', {})
        response, updated_context = get_response(user_input, context)
        return jsonify({'response': response, 'context': updated_context, 'timestamp': get_current_timestamp()})
    except Exception as e:
        logging.error(f"Error in /chat endpoint: {str(e)}")
        return jsonify({'response': "Oops, something went wrong!", 'context': context, 'timestamp': get_current_timestamp()}), 500

def get_current_timestamp():
    from datetime import datetime
    return datetime.now().strftime("%I:%M %p")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)