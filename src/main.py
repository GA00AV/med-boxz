import streamlit as st
from backend import GRAPH, INITIAL_VALUE, return_output_from_ai_message
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="MED-BOXZ", page_icon="🩺", layout="centered")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state = INITIAL_VALUE

st.title("🩺MED-BOXZ")

# Display existing messages using Streamlit's native chat UI
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    if isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("ai"):
            st.write(return_output_from_ai_message(msg.content))

# Chat input box
user_input = st.chat_input("Type your query...")

if user_input:
    # Add user message
    st.session_state.messages.append(HumanMessage(user_input))
    # Display immediately
    with st.chat_message("user"):
        st.write(user_input)

    # Generate response
    try:
        response = GRAPH.invoke(st.session_state)
        reply = return_output_from_ai_message(response['messages'][-1].content)
        st.session_state.messages = response['messages']
        with st.chat_message("ai"):
            st.write(reply)
    except Exception as e:
        reply = f"Error: {e}"

