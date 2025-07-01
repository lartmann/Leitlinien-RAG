import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI
import dotenv
import json
from datetime import datetime
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables
dotenv.load_dotenv()

# Title
st.title("Leitlinien Suchmaschine")

# --- Cache-heavy resources ---
@st.cache_resource
def load_llm():
    api_key = os.getenv("MISTRAL_API_KEY")
    return ChatMistralAI(api_key=api_key)

@st.cache_resource
def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large-instruct"
    )
    return Chroma(
        collection_name="guidelines",
        embedding_function=embeddings,
        persist_directory="/Volumes/FESTPLATTE/sma_project/chroma_langchain_db_dentistry",
    )

@st.cache_resource
def load_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", "Du bist ein Assistent, der Fragen zu medizinischen Leitlinien beantwortet. "
                   #"Deine Antworten stützen sich auf den Kontext, mit dem du die Frage beantworten kannst. "),
                   "Fasse den Kontext in Hinblick auf die Frage zusammen. Wenn die Frage nicht durch den Kontext beantwortet werden kann, dann schreibe \"Ich kann Ihnen dabei nicht helfen.\""),
        ("user", "Kontext: {context} \n\n Frage: {question}")
    ])

llm = load_llm()
vector_store = load_vectorstore()
prompt = load_prompt()

# --- Define state for LangGraph ---
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

# --- Define LangGraph nodes ---
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"], k=10)
    #retrived_docs = [f"{doc.metadata['title']}: {doc['page_content']}" for doc in retrieved_docs]
    return {"question": state["question"], "context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(f"{doc.metadata['title']}: {doc.page_content}" for doc in state["context"])
    
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {
        "question": state["question"],
        "context": state["context"],
        "answer": getattr(response, "content", str(response))
    }

# --- Cache compiled graph ---
if "graph" not in st.session_state:
    graph_builder = StateGraph(State)
    graph_builder.add_node("retrieve", retrieve)
    graph_builder.add_node("generate", generate)
    graph_builder.set_entry_point("retrieve")
    graph_builder.add_edge("retrieve", "generate")
    st.session_state.graph = graph_builder.compile()

graph = st.session_state.graph

# --- UI for query ---
col1, col2 = st.columns([6, 1], vertical_alignment="bottom")
with col1:
    search_query = st.text_input("Frage", placeholder="z.B. \"Was ist die empfohlene Nachsorge bei einer Weisheitszahn-OP?\"")

with col2:
    search_button = st.button("Suchen")

# filters
# load metadata.json

def get_set_from_metadata(metadata, key):
    elements = []
    with open("metadata.json", "r") as f:
        metadata = json.load(f)
    for k in metadata.keys():
        if key == "Federführende Fachgesellschaft(en)":
            elements.extend(metadata[k].get(key, []).split("(Visitenkarte)"))
        else:
            try: 
                #print(metadata[k][key])
                elements.extend(metadata[k][key].split(","))
            except:
                continue
    return list(set(elements))

@st.cache_resource
def load_filters():
    with open("metadata.json", "r") as f:
        metadata = json.load(f)
    fachgesellschaften = get_set_from_metadata(metadata, "Federführende Fachgesellschaft(en)") + get_set_from_metadata(metadata, "Beteiligung weiterer AWMF-Fachgesellschaften")
    keywords = get_set_from_metadata(metadata, "Schl\u00fcsselw\u00f6rter")
    return fachgesellschaften, keywords

#fachgesellschaften, keyws = load_filters()

# with st.expander("Filter"):
#     fachgesellschaft = st.selectbox("Fachgesellschaft", fachgesellschaften, index=0)
#     keywords = st.multiselect("Stichworte", keyws)


# --- Search handling ---
if search_button:
    if not search_query:
        st.warning("Bitte geben Sie einen Suchbegriff ein.")
    else:
        with st.spinner("Suche ..."):
            state = graph.invoke({"question": search_query})
            context = state.get("context", [])
            answer = state.get("answer", "Keine Antwort gefunden.")


            st.subheader("Antwort")
            st.write(answer)
            
            st.subheader("Quellen")
            for doc in context:
                valid_until_str = doc.metadata.get('G\u00fcltig bis', None)
                if valid_until_str:
                    try:
                        # Adjust the format string to match the actual date format in the metadata
                        valid_until_date = datetime.strptime(valid_until_str, "%d.%m.%Y")  # Example format: '31.12.2003'
                    except ValueError as e:
                        #print(f"Error parsing date: {e}")
                        valid_until_date = None
                else:
                    valid_until_date = None
                with st.expander(f"**[{doc.metadata['Registiernummer']} - {doc.metadata['title']}]({doc.metadata['pdf_links']}) Seite {doc.metadata['page']}**"):
                    if valid_until_date is not None and valid_until_date < datetime.now():
                        st.warning(f"Dokument abgelaufen: {doc.metadata['G\u00fcltig bis']}")
                    st.write("..." + doc.page_content + "...")
                    st.write(f"**Stand**: {doc.metadata['Stand']}, **Gültig bis:** {doc.metadata['G\u00fcltig bis']}")