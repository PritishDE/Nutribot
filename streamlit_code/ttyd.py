# Import python packages
import streamlit as st

from snowflake.snowpark.context import get_active_session


import json  # To handle JSON data


from typing import Dict, List, Optional, Tuple

import _snowflake  # For interacting with Snowflake-specific APIs


# Each path points to a YAML file defining a semantic model
AVAILABLE_SEMANTIC_MODELS_PATH = "model_path.yaml"  # Update with your actual path
API_ENDPOINT = "/api/v2/cortex/analyst/message"
API_TIMEOUT = 50000  # in milliseconds

# Initialize a Snowpark session for executing queries
session = get_active_session()

# Set page config
st.set_page_config(
    page_title="Your Nutri Buddy",
    page_icon="🥗",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .main-header {
        background: linear-gradient(135deg, #2E8B57 0%, #3CB371 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
    }
    .expander-header {
        font-weight: 600;
        color: #2E8B57;
    }
    .suggestion-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stButton button {
        background-color: #2E8B57;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


def get_analyst_response(prompt) -> Tuple[Dict, Optional[str]]:
    """
    Send chat to the Cortex Analyst API and return the response.
    """
    # Prepare the request body with the user's prompt
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "semantic_model_file": AVAILABLE_SEMANTIC_MODELS_PATH,
    }

    resp = _snowflake.send_snow_api_request(
        "POST",  # method
        API_ENDPOINT,  # path
        {},  # headers
        {},  # params
        request_body,  # body
        None,  # request_guid
        API_TIMEOUT,  # timeout in milliseconds
    )

    # Content is a string with serialized JSON object
    parsed_content = json.loads(resp["content"])
    
    # Check if the response is successful
    if resp["status"] < 400:
        # Return the content of the response as a JSON object
        return parsed_content, None
    else:
        # Craft readable error message
        error_msg = f"""
🚨 An Analyst API error has occurred 🚨

* response code: `{resp['status']}`
* request-id: `{parsed_content['request_id']}`
* error code: `{parsed_content['error_code']}`

Message:
```
{parsed_content['message']}
```
        """
        return parsed_content, error_msg

def summarize_output(query, table_output):
    # Create summarization prompt
    summarization_prompt = f"""Given the question: "{query}"
    And the following table of results:
    
    {table_output}
    
    Write a human-tone like summary of the above. Only answer what is asked.
    """
    # st.write(summarization_prompt)
    summary_query = """
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large',
        :1) AS summary;
    """
    result = session.sql(summary_query,params=[summarization_prompt]).collect()
    summary_text = result[0]['SUMMARY']
    st.markdown("### 🤖 Sure! Here's what I found:")
    st.write(summary_text)

def display_content(
    content: List[Dict[str, str]],
    prompt: str,
    request_id: Optional[str] = None
) -> None:
    """Displays a content item for a message."""
    text_displayed = False
    table_output = None
    # Move request details to the end
    if request_id:
        with st.expander("🔍 Request Details", expanded=False):
            st.code(f"Request ID: {request_id}", language="plaintext")
    for item in content:
        if item["type"] == "text" and not text_displayed:
            st.markdown(f"💡 {item['text']}")
            text_displayed = True
        elif item["type"] == "suggestions":
            with st.expander("✨ Suggested Questions", expanded=True):
                for suggestion_index, suggestion in enumerate(item["suggestions"]):
                    st.code(suggestion)
        elif item["type"] == "sql":
            with st.expander("🔧 SQL Query", expanded=False):
                st.code(item["statement"], language="sql")
            
            with st.spinner("📊 Processing results..."):
                try:
                    query = item["statement"]
                    table_output = session.sql(query)
                    
                    with st.expander("📈 Detailed Results", expanded=False):
                        st.dataframe(
                            table_output.collect(),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    summarize_output(prompt, table_output.toPandas().to_markdown(index=False))
                except Exception as e:
                    st.error("❌ Failed to execute SQL query. Please try again.")
    
    


# Main Streamlit App Logic
def main():
    # Main header
    st.markdown("""
        <div class="main-header">
            <h1>🥗 Your Nutri Buddy</h1>
            <p style="font-size: 1.2rem; margin-top: 0.5rem;">
                Your AI-powered nutrition assistant
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Welcome message and instructions
    if "messages" not in st.session_state:
        st.session_state.messages = []
        

    # Display chat messages
    for message in st.session_state.messages:
        message_class = "user-message" if message["role"] == "user" else "assistant-message"
        with st.chat_message(message["role"]):
            st.markdown(f'{message_class}', unsafe_allow_html=True)
            if message["role"] == "user":
                st.markdown(f"🤔 {message['content']}")
            else:
                display_content(
                    message['content'].get('output_content'),
                    message['content'].get('prompt'),
                    message['content'].get('request_id')
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    prompt = st.chat_input("Ask your nutrition question here...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(f'🤔 {prompt}', unsafe_allow_html=True)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Analyzing your question..."):
                response, error_msg = get_analyst_response(prompt)
                request_id = response["request_id"]
                output_content = response["message"]["content"]
                
            st.session_state.messages.append({
                "role": "assistant",
                "content": {
                    'request_id': request_id,
                    'output_content': output_content,
                    'prompt': prompt
                }
            })

            display_content(output_content, prompt, request_id)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()