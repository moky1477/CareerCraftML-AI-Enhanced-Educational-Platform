from flask import Flask, render_template, request , jsonify, session 
from flask_session import Session
from PyPDF2 import PdfReader 
from datetime import datetime
from gtts import gTTS
from tempfile import TemporaryFile
import threading
import sounddevice as sd
import asyncio
import sounddevice as sd
import soundfile as sf
from gtts import gTTS
import numpy as np
import time
import speech_recognition as sr
import PyPDF2 as pdf  
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores.faiss import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
# from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

GOOGLE_API_KEY="YOUR_API_KEY"
# load_dotenv()
google_api_key = os.getenv(GOOGLE_API_KEY)
genai.configure(api_key=os.getenv(GOOGLE_API_KEY))

if google_api_key:
    print("Google API key is set:", google_api_key)
else:
    print("Google API key is not set. Please make sure to set it in your environment variables.")



app = Flask(__name__)


def input_pdf_text_judge(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

input_prompt_judge = """
As a highly successful interviewer within a multinational company, you frequently evaluate resumes across various roles and industries. your expertise lies in providing detailed feedback to help candidates refine their resumes for maximum impact. 
Remember, the evaluation should strictly focus on the resume content without external context. Additionally, analyze the "Technical Skills"/ "Skills" section and suggest relevant skills the student can add. 
Ensure the output is specific, highlighting points from the resume that require improvement and suggesting alternatives.
Give a detailed review of the students resume.

Instructions:

Evaluate the provided resume against industry standards and deliver a detailed assessment in the following format:

Resume Score (Out of 100): Provide a score based on the accuracy and completeness of the resume, including essential details such as experience, skills, etc.

Missing Sections: Identify any absent sections and suggest their inclusion. Specify what is missing and provide guidance on how to incorporate them effectively.

Format Suggestions: Offer recommendations for improving the resume format to enhance readability and visual appeal.

General Recommendations: Provide generalized advice for enhancing the overall quality of the resume, focusing on areas for improvement.

Ensure the resume contains ATS-friendly keywords; if not, provide suggestions for their inclusion.

"""

def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader= PdfReader(pdf)
        for page in pdf_reader.pages:
            text+= page.extract_text()
    return  text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template_new = """
    You have been given a PDF file as an input from the user. Your job is to analyse this file and answer 
    the given question by the user as detailed as possible. The user will also mention the number of words with 
    which he would like the questions to be answered. Be precise with the answer and dont give incorrect answers 
    at any cost.

    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template_new, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    return response["output_text"]


def extract_transcript_details(link):
    try:
        video_id = link.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]

        return transcript

    except Exception as e:
        raise e

prompt = """You are Yotube video summarizer. You will be taking the transcript text
    and summarizing the entire video and providing the important summary 
    within 500 words. Please provide the summary of the text given here: 
 
    """

def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    #print(response.text)
    return response.text

#added new code 
# Gemini Pro response
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

input_prompt_1 = """
**Job Description Evaluation:**

As a highly advanced Application Tracking System (ATS) specializing in the tech field, software engineering, 
data science, data analysis, and big data engineering, your role is to meticulously evaluate resumes in a fiercely competitive job market. 
Provide the best assistance possible for resume enhancement, assigning a percentage match based on the 
job description (JD) and identifying missing keywords with utmost accuracy.

**Instructions:**
Evaluate the provided resume against the given JD and deliver a comprehensive response in the following format:

Evaluation Summary:

- **JD Match**: [%]\n\n
- **Missing Keywords:** []\n
- **Profile Summary:** ""\n


"""
#added new code 

@app.route('/chatpdf')
def chatpdf():
    return render_template('chatpdf.html')

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/summarwise')
def summarwise():
    return render_template('summarize.html', link=" ")

@app.route('/resumescan')
def resumescan():
    return render_template('ATS.html')

@app.route('/resumejudge')
def resumejudge():
    return render_template('resultJob.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/mockinterview')
def mockinterview():
    return render_template('mockinterview.html')


#Summarize youtube video
@app.route('/summarize', methods=['POST'])
def get_detailed_notes():
    link=""
    link = request.form.get('link')
    print(link)
    if not link:
        return "No YouTube video link provided."

    transcript_text = extract_transcript_details(link)
    if not transcript_text:
        return "Failed to retrieve transcript from the provided YouTube video."

    summary = generate_gemini_content(transcript_text, prompt)
    formatted_response = "<p>" + summary.replace("\n", "<br>") + "</p>"
    formatted_response = formatted_response.replace("**", "<b>").replace("**", "</b>")
    return render_template('summarize.html', response=formatted_response,link=link)


@app.route('/process', methods=['POST'])
def process():
    user_question = request.form['question']
    pdf_docs = request.files.getlist('pdf_file')  # Get list of uploaded PDF files
    if not pdf_docs:
        return "No PDF file uploaded."

    # Process the newly uploaded PDF file
    raw_text = get_pdf_text(pdf_docs)
    text_chunks = get_text_chunks(raw_text)
    get_vector_store(text_chunks)

    # Answer the user's question using the newly processed PDF file
    response = user_input(user_question)
    return render_template('chatpdf.html', response=response)
    

@app.route('/submit', methods=['POST'])
def submit():
    jd = request.form['job_description']
    uploaded_file = request.files['resume']

    if uploaded_file is None or jd == "":
        return "Please provide both job description and resume."

    text = input_pdf_text(uploaded_file)
    response = get_gemini_response(input_prompt_1 + jd)
    formatted_response = "<p>" + response.replace("\n", "<br>") + "</p>"
    formatted_response = formatted_response.replace("**", "<b>").replace("**", "</b>")
    return render_template('ATS.html', response=formatted_response)

@app.route('/submitjudge', methods=['POST'])
def submitjudge():
    uploaded_file = request.files['resume']
    if uploaded_file is None :
        return "Please provide resume."

    text = input_pdf_text_judge(uploaded_file)
    response = get_gemini_response(input_prompt_judge)
    formatted_response = "<p>" + response.replace("\n", "<br>") + "</p>"
    formatted_response = formatted_response.replace("**", "<p>").replace("**", "</p>")
    return render_template('resultJob.html', response=formatted_response)

@app.route('/start_interview', methods=['POST'])
def start_interview():
    data = request.json  # Ensure you're parsing JSON data
    user_name = data.get('user_name')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop) 
    
    job_description = data.get('job_description')
    if user_name and job_description:
        questions = generate_questions(job_description)
        return jsonify({'status': 'success', 'questions': questions})
    loop.close()
    return jsonify({'status': 'error', 'message': 'Invalid input'})

@app.route('/record_answer', methods=['POST'])
def record_answer():
    user_answer = speak_and_listen()
    if user_answer:
        return jsonify({'status': 'success', 'answer': user_answer})
    return jsonify({'status': 'error', 'message': 'Failed to record answer'})

@app.route('/complete_interview', methods=['POST'])
def complete_interview():
    data = request.json
    user_name = data.get('user_name')
    job_description = data.get('job_description')
    questions = data.get('questions')
    responses = data.get('responses')
    
    save_interview(user_name, job_description, questions, responses)
    return jsonify({'status': 'success'})

@app.route('/clear_sessions', methods=['GET'])
def clear_sessions():
    # Clear the contents of interview_sessions.txt
    with open("interview_sessions.txt", "w") as file:
        file.write("")
    return jsonify({'status': 'success'})


@app.route('/feedback')
def feedback_page():
    return render_template('feedback.html')


@app.route('/view_feedback', methods=['POST'])
def view_feedback():
    data = request.json
    user_name = data.get('user_name')
    job_description = data.get('job_description')

    # Read the content of interview_sessions.txt
    with open("interview_sessions.txt", "r") as file:
        interview_data = file.read()

    prompt = input_prompt + "\n" + job_description + "\n" + interview_data
    feedback = get_gemini_response(prompt)

    return jsonify({'status': 'success', 'feedback': feedback})

@app.route('/get_feedback', methods=['GET'])
def get_feedback():
    user_name = request.args.get('user_name')
    job_description = request.args.get('job_description')

    # Read the content of interview_sessions.txt
    with open("interview_sessions.txt", "r") as file:
        interview_data = file.read()

    prompt = input_prompt + "\n" + job_description + "\n" + interview_data
    feedback = get_gemini_response(prompt)

    return jsonify({'status': 'success', 'feedback': feedback})




def generate_questions(job_description):
    interview_questions = []
    previous_answers = []
    for _ in range(3):  # Generate 5 questions
        question = ask_question(job_description, previous_answers)
        if question:
            interview_questions.append(question)
            previous_answers.append(question)
        else:
            print("Failed to generate unique question.")
    return interview_questions

def ask_question(job_description, previous_answers):
    model = ChatGoogleGenerativeAI(model="gemini-1.0-pro", google_api_key=GOOGLE_API_KEY)
    prompt_template = f"""
    The job description provided for a certain position includes the following key responsibilities, qualifications, and requirements:
    Job Description:
    {job_description}
    Based on the above description, please ask a question relevant to the candidate's experience, skills, or qualifications:

    Question:
    """
    
    if previous_answers:
        prompt_template += "Based on the above description and your previous answers, please provide further details:\n"
        for index, answer in enumerate(previous_answers):
            prompt_template += f"\nPrevious Answer {index+1}:\n{answer}\n"

    prompt_template += "Please ask a relevant question or provide further details:\n\nQuestion:"

    try:
        response = model.invoke(input=prompt_template)
        question = response.content.strip()
        return question
    except Exception as e:
        print(f"Failed to generate question: {e}")
        return None

def speak_question(question):
    tts = gTTS(text=question, lang='en')
    audio_file = TemporaryFile()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    play_audio(audio_file)
    audio_file.close()

def speak_and_listen():
    speak_now_message = "Speak now... You have 30 seconds to answer."
    tts = gTTS(text=speak_now_message, lang='en')
    audio_file = TemporaryFile()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    play_audio(audio_file)
    audio_file.close()

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Speak now... You have 30 seconds to answer.")
        audio = recognizer.listen(source, timeout=30)
        print("Audio recording complete!")

    try:
        user_answer = recognizer.recognize_google(audio)
        print(f"Your answer: {user_answer}")
        return user_answer
    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None


def save_interview(user_name, job_description, questions, responses):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("interview_sessions.txt", "a") as file:
        file.write("==================================================\n")
        file.write(f"Interview Session for: {user_name}\n")
        file.write(f"Timestamp: {timestamp}\n")
        file.write("==================================================\n")
        file.write("Job Description:\n")
        file.write(job_description)
        file.write("\n\n")
        file.write("--------------------------------------------------\n")
        file.write("Interview Questions and Answers:\n")
        for i, question in enumerate(questions):
            if i < len(responses):
                file.write(f"Question {i+1}:\n{question}\n")
                file.write(f"Answer {i+1}:\n{responses[i]}\n\n")
            else:
                file.write(f"Question {i+1}:\n{question}\n")
                file.write("Answer: Not provided\n\n")
            if i < len(questions) - 1:
                file.write("--------------------------------------------------\n")
        file.write("==================================================\n\n")

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

def play_audio(audio_file):
    data, fs = sf.read(audio_file, dtype='float32')
    sd.play(data, fs)
    sd.wait()

def input_text(uploaded_file):
    return uploaded_file.read().decode("utf-8")

input_prompt = """
**Interview Analysis System:**

You are a job recruiter and a hiring manager, you are taking an interview for a given Job Description that has been given to you by the user.
You are also given a text file which contains responses given by the user corresponding to the questions asked by an AI interview.

The text file has contents in this format:

1. Name of the candidate
2. Date and time of Interview
3. Job Description given by candidate which they are interviewing for
4. Question 1: //Question Asked by AI
   Answer 1: // Answer given by the user

**Instructions:**
Evaluate the user's answers and give feedback on the basis of these points:
1. Technicality of User's answer (How technically correct is the answer)
2. Candidate's confidence in giving the answer (Based on text given to you, classify this as "Under-confident", "Over-confident", "Perfectly Confident", "Nervous")
3. Score on how the Candidate performed (Out of 100) (Based on above components)
4. Useful Tips and Tricks that the user can take to improve in the next interview

**This should be the format for your response:**

Candidate Interview Feedback

Candidate Name: [Candidate's Name]

Technicality of User's Answers:

Answer 1: [Evaluation of technical proficiency and specific examples] (Score: [Score out of 10])
Answer 2: [Evaluation of technical proficiency and specific examples] (Score: [Score out of 10])
Answer 3: [Evaluation of technical proficiency and specific examples] (Score: [Score out of 10])
....
Answer N: [Evaluation of technical proficiency and specific examples] (Score: [Score out of 10])

Candidate's Confidence in Giving the Answers: (All on new lines)
Answer 1: [Confidence level] 
Answer 2: [Confidence level]
Answer 3: [Confidence level]
....
Answer N: [Confidence level]

Score on How the Candidate Performed (Out of 100): [Overall score]

Useful Tips and Tricks for the Candidate:
[Tip 1]
[Tip 2]
[Tip 3]
...
[Tip N]
"""


if __name__ == '__main__':
    app.run(port=8000,debug=True)
