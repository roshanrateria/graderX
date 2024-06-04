import google.generativeai as genai
import os
import gradio as gr
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configure the Gemini API
api = os.getenv("API_KEY")
genai.configure(api_key=api)

# Set up the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# Function to generate interview question
def generate_question(company, question_type):
    prompt = f"Act as an interviewer from {company} for {question_type} round. Give me a probable Question ONLY"
    response = model.generate_content(prompt)
    return response.text

# Function to evaluate answer
def evaluate_answer(question, answer):
    prompt = f"Question: {question}\nAnswer: {answer}\nProvide a score(as an Int Out of 100) and feedback on the answer in the below format:\n Score: \n Feedback :"
    response = model.generate_content(prompt)
    return response.text

# Function to create a countdown timer donut chart
def create_timer_chart(time_left):
    percentage = (time_left / 300) * 100
    if percentage>=80:
        fig = go.Figure(data=[go.Pie(
        values=[time_left, 300 - time_left],
        hole=0.7,
        marker=dict(colors=['green', 'lightgray']),
        textinfo='none'
    )])
    elif percentage>=60:
        fig = go.Figure(data=[go.Pie(
        values=[time_left, 300 - time_left],
        hole=0.7,
        marker=dict(colors=['#FFD700', 'lightgray']),
        textinfo='none'
    )])
    elif percentage>=40:
        fig = go.Figure(data=[go.Pie(
        values=[time_left, 300 - time_left],
        hole=0.7,
        marker=dict(colors=['orange', 'lightgray']),
        textinfo='none'
    )])
    else:
        fig = go.Figure(data=[go.Pie(
        values=[time_left, 300 - time_left],
        hole=0.7,
        marker=dict(colors=['red', 'lightgray']),
        textinfo='none'
    )])
    
    fig.update_layout(
        annotations=[dict(text=f'{int(time_left // 60)}:{int(time_left % 60):02d}', x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=False,
        margin=dict(l=20, r=20, t=10, b=10),
        width=100,
        height=100
    )
    return fig

# Define the Gradio interface functions
def start_interview(company, question_type,end_time):
    question = generate_question(company, question_type)
    end_time[0] = datetime.now() + timedelta(minutes=5)
    timer_chart = create_timer_chart(300)
    return question, end_time, timer_chart

def submit_answer(question, answer,end_time):
    end_time[0]=0
    feedback = evaluate_answer(question, answer)
    try:
        feedback_text = '\n'.join(feedback.split('\n')[1:])
        score = int(feedback.split('\n')[0].split(':')[1].strip())
    except:
        score=0
    
    if score >= 80:
        score_color = "green"
    elif score >= 50:
        score_color = "orange"
    else:
        score_color = "red"
    
    fig = go.Figure(data=[go.Pie(
        values=[score, 100 - score],
        hole=0.7,
        marker=dict(colors=[score_color, 'lightgray']),
        textinfo='none'
    )])
    fig.update_layout(
        annotations=[dict(text=f'{score}%', x=0.5, y=0.5, font_size=20, showarrow=False)],
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0)
    )

    return fig, feedback_text,end_time



def update_timer(end_time):
    if end_time[0]!=0:
        time_left = (end_time[0] - datetime.now()).total_seconds()
    else:
        time_left=300
    if time_left < 0:
        time_left = 0
    timer_chart = create_timer_chart(time_left)
    return timer_chart, gr.update(visible=time_left > 0 and time_left!=300),end_time

# Define a function to be called when the button is clicked
def open_chatbot():
    return




with gr.Blocks(theme=gr.themes.Soft()) as interface:
  end_time_state = gr.State([0])
  with gr.Row():
   with gr.Column(scale=3):
    with gr.Row():
        company_dropdown = gr.Dropdown(['TCS', 'Wipro'], label="Company")
        question_type_dropdown = gr.Dropdown(['Technical', 'HR'], label="Type of Question")
        start_button = gr.Button("Start", variant="primary")
        timer_display = gr.Plot(label="Time Left")
    with gr.Row():
        question_display = gr.Markdown(label="Question")
    with gr.Row():
        answer_textbox = gr.Textbox(lines=5, label="Answer")
    with gr.Row():
        submit_button = gr.Button("Submit", variant="primary")
    with gr.Row():
        score_display = gr.Plot(label="Score")
        feedback_display = gr.Markdown(label="Feedback")

   with gr.Column(scale=2):
      gr.HTML("""
       <iframe
	src="https://roar777-assist.hf.space"
	frameborder="0"
	width="100%"
	height="700px"
></iframe>

    """)

    # Define interaction logic
  start_button.click(start_interview, [company_dropdown, question_type_dropdown,end_time_state], [question_display, end_time_state, timer_display])
  submit_button.click(submit_answer, [question_display, answer_textbox,end_time_state], [score_display, feedback_display,end_time_state])
  interface.load(update_timer, inputs=[end_time_state], outputs=[timer_display, submit_button,end_time_state], every=1)




# Add custom JavaScript to create and open a modal
interface.launch(share=True)
