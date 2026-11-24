from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
import shutil
import os


def clear_db():
    
    if os.path.exists("vector_db"):
        shutil.rmtree("vector_db")

def process_pdf(pdf_path):

    loader = PyPDFLoader(pdf_path)

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)
    print(f"Chunks created: {len(chunks)}")

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="vector_db"
    )

    return len(chunks)


def load_full_pdf(pdf_path):
    
    loader = PyPDFLoader(pdf_path)

    documents = loader.load()

    text = "\n\n".join(
        doc.page_content
        for doc in documents
    )

    return text


def is_document_request(question):
    
    question = question.lower()

    keywords = [

        "summarize",
        "summary",
        "describe",
        "overview",
        "document",
        "pdf",
        "report",
        "what is this document",
        "explain this pdf"

    ]

    return any(
        word in question
        for word in keywords
    )


def retrieve_docs(question):
    
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vectordb = Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )

    docs = vectordb.similarity_search(
        question,
        k=3,
        fetch_k=10
    )


    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} ---")
        print(doc.page_content[:500])

    return docs

def ask_pdf(question, pdf_path):
    
    llm = ChatOllama(
        model="llama3.2"
    )

    if is_document_request(question):

        document = load_full_pdf(pdf_path)

        prompt = f"""
You are reading an uploaded PDF.

Answer ONLY using this document.

Document:

{document}

User request:

{question}
"""

        response = llm.invoke(prompt)

        return response.content

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vectordb = Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )

    docs = vectordb.max_marginal_relevance_search(
        question,
        k=3,
        fetch_k=10
    )

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    prompt = f"""
Answer ONLY using the context below.

If the answer is not found, reply exactly:

Information not found in uploaded documents.

Context:

{context}

Question:

{question}
"""

    response = llm.invoke(prompt)

    return response.content