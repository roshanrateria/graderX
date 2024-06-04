import gradio as gr
from huggingface_hub import InferenceClient
import os 
os.system('python -m spacy download en_core_web_md')
"""
For more information on `huggingface_hub` Inference API support, please check the docs: https://huggingface.co/docs/huggingface_hub/v0.22.2/en/guides/inference
"""
client = InferenceClient("HuggingFaceH4/zephyr-7b-beta")
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
import re
stop_words = [
  "what",'how','why','can','do','you','if','in','of','explain','concept','implement','difference',
  'the','is','and','it','between','give','an','example','from','describe','principles','purpose',
  'a','principle','to','its','as','are','are','using','process','discuss','use','does','relate',
  'to','for','design','create','on','develop','like','with','new','build','understand','or','they',
  'differ','when','would','work','code','define'
]
# Load spaCy model
nlp = spacy.load("en_core_web_md")

# Load dataset from CSV
def load_data_from_csv(filename):
    df = pd.read_csv(filename, encoding='utf-8')  # Update encoding if needed
    data = df.to_dict(orient="records")
    return data

# Preprocess questions
def preprocess_questions(data):
    questions = [item["Question"] for item in data]
    return questions
def keys(data):
    p=[d['Keywords'] for d in data]
    return p
# Keyword search
def keyword_search(user_input, questions,keywords):
    filtered_questions = []
    l=''
    for t in user_input.split():
        if re.sub(r'[^\w\s]', '',t).lower() not in stop_words:
            l+=re.sub(r'[^\w\s]', '',t).lower()+' '
    
    for a in range(200):
        for b in l.split():
            if b in keywords[a].split():
                filtered_questions.append(questions[a])
    return filtered_questions

# Semantic similarity
def calculate_similarity(user_input, questions):
    user_input_processed = nlp(user_input)
    similarities = []
    for question in questions:
        question_processed = nlp(question)
        similarity = user_input_processed.similarity(question_processed)
        similarities.append((question, similarity))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities

# Chatbot function
data = load_data_from_csv("Processed.csv")  # Update filename
questions = preprocess_questions(data)
k=keys(data)
matcher = PhraseMatcher(nlp.vocab)
patterns = [nlp(question) for question in questions]
matcher.add("Questions", None, *patterns)
def chatbot(user_input,history):
        if user_input.lower() in ["exit", "quit", "bye"]:
            yield "Goodbye!"
            return
        if user_input.lower() in ["hi", "hello"]:
            yield "Hello! I'm a programming chatbot. Ask me any question."
            return
        # Keyword search
        filtered_questions = keyword_search(user_input, questions,k)
        if filtered_questions:
            # Semantic similarity
            similarities = calculate_similarity(user_input, filtered_questions)
            best_match_question, best_similarity = similarities[0]
            if best_similarity > 0.3:  # Adjust threshold as needed
                for item in data:
                    if item["Question"] == best_match_question:
                        yield item['Answer']
                        break
            else:
                yield "Chatbot: Sorry, I don't understand the question."
        else:
            yield "Chatbot: Sorry, I don't understand the question."





"""
For information on how to customize the ChatInterface, peruse the gradio docs: https://www.gradio.app/docs/chatinterface
"""
demo = gr.ChatInterface(
    chatbot,examples=["Define Encapsulation", "Differenciate between Compilation and interpretation", "what is SOLID"], title="Programmer Bot",stop_btn=None,retry_btn=None,undo_btn=None,theme=gr.themes.Soft()
)


if __name__ == "__main__":
    demo.launch()