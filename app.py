from flask import Flask, render_template, request
from Backend.helper import download_hugging_face_embeddings
from langchain_pinecone import Pinecone
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from Backend.prompt import *
from waitress import serve
import os

app = Flask(__name__, static_folder="Frontend/static", template_folder="Frontend/templates")

load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

embeddings = download_hugging_face_embeddings()


index_name = "meditrain"

# Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = Pinecone.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})

model_name = "llama3-8b-8192" 
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=model_name, temperature=0.4, max_tokens=500)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)


# Routes
@app.route("/")
def home():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

# Chat | Get
@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    input = msg
    print(input)
    response = rag_chain.invoke({"input": msg})
    print("Response : ", response["answer"])
    return str(response["answer"])




if __name__ == '__main__':
    serve(app, host="0.0.0.0", port= 1000)