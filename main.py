"""
Insurance Form Processing Application - Complete Fixed Version
Streamlit interface with vector-only storage and LangChain conversation memory
"""

import streamlit as st
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Agno and AI components
from agno.utils.log import logger

# Project components - updated imports
from config.vector_memory import vector_memory
from agents.workflow import workflow_tool
from utils.exception_handling import setup_openai_exception_suppression

# Setup exception suppression at startup
setup_openai_exception_suppression()

# Page configuration
st.set_page_config(
    page_title="BTAS Insurance Form Processor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/JEEVITHA2512/BTAS-Insurance-Project/help',
        'Report a Bug': 'https://github.com/JEEVITHA2512/BTAS-Insurance-Project/issues',
        'About': """
        # BTAS Insurance Processor 🛡️
        
        A powerful AI-driven insurance form processing system with:
        - Multi-method OCR extraction
        - Language detection (English/Malay)
        - Field mapping and validation
        - Vector-based memory system
        - Dark theme UI
        
        Built with Streamlit, Agno AI, and ChromaDB.
        """
    }
)

# Custom CSS
def load_css():
    """Load custom CSS styling for dark theme - Default styles only"""
    # Default dark theme CSS (removed external file loading)
    dark_theme_css = """
    <style>
    /* Dark theme enhancements */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1f1f23 0%, #2d2d35 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border: 1px solid #333;
    }
    
    /* Card styling */
    .stContainer > div {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #404040;
    }
    
    /* Metrics styling */
    .metric-container {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3a 100%);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #444;
        margin: 0.5rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #FF6B6B 0%, #FF5252 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #FF5252 0%, #FF4444 100%);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
        transform: translateY(-2px);
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        background-color: #262730;
        border: 2px dashed #444;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
    }
    
    .stFileUploader > div:hover {
        border-color: #FF6B6B;
        background-color: #2d2d35;
    }
    
    /* Tab styling */
    .stTabs > div > div > div > div {
        background-color: #262730;
        border-radius: 8px;
        border: 1px solid #404040;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background-color: rgba(0, 255, 0, 0.1);
        border: 1px solid #00ff00;
        border-radius: 8px;
    }
    
    .stError {
        background-color: rgba(255, 0, 0, 0.1);
        border: 1px solid #ff0000;
        border-radius: 8px;
    }
    
    .stInfo {
        background-color: rgba(0, 123, 255, 0.1);
        border: 1px solid #007bff;
        border-radius: 8px;
    }
    
    .stWarning {
        background-color: rgba(255, 193, 7, 0.1);
        border: 1px solid #ffc107;
        border-radius: 8px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1e1e2e;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background-color: #262730;
        border: 1px solid #444;
        border-radius: 8px;
        color: #FAFAFA;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #262730;
        border: 1px solid #444;
        border-radius: 8px;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #FF6B6B 0%, #FF5252 100%);
    }
    
    /* JSON display */
    .stJson {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
    }
    </style>
    """
    st.markdown(dark_theme_css, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'current_document' not in st.session_state:
        st.session_state.current_document = None
    
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0
        }

def display_header():
    """Display application header with logos and title - Dark theme optimized"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if os.path.exists("assets/beeonix 1.png"):
            st.image("assets/beeonix 1.png", width=100)
    
    with col2:
        st.markdown("""
            <div class='main-header' style='text-align: center;'>
                <h1 style='color: #FF6B6B; margin-bottom: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'>
                    🛡️ BTAS Insurance Processor
                </h1>
                <p style='color: #B0B0B0; font-size: 18px; margin-top: 0.5rem; font-weight: 300;'>
                    AI-Powered Insurance Form Processing with Vector Memory
                </p>
                <div style='height: 3px; background: linear-gradient(90deg, #FF6B6B 0%, #FF5252 100%); border-radius: 2px; margin-top: 1rem;'></div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if os.path.exists("assets/Bigtapplogo 1.png"):
            st.image("assets/Bigtapplogo 1.png", width=100)

def display_sidebar():
    """Display sidebar with controls and information"""
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        
        # Processing statistics
        stats = vector_memory.get_processing_stats()
        st.markdown("### 📊 System Stats")
        st.metric("Processing Memories", stats.get('total_processing_memories', 0))
        st.metric("Conversations", stats.get('total_conversations', 0))
        st.info(f"Storage: {stats.get('storage_type', 'Unknown')}")
        st.info(f"Memory: {stats.get('langchain_memory', 'Unknown')}")
        
        # Memory management
        st.markdown("### 🧠 Memory Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Processing"):
                vector_memory.clear_processing_memory()
                st.success("Processing memory cleared!")
                st.rerun()
        
        with col2:
            if st.button("Clear Conversations"):
                vector_memory.clear_conversation_memory()
                st.session_state.conversation_history = []
                st.success("Conversations cleared!")
                st.rerun()
        
        # Session statistics
        st.markdown("### 📈 Session Stats")
        st.metric("Documents Uploaded", st.session_state.stats['total_processed'])
        st.metric("Successful", st.session_state.stats['successful_extractions'])
        st.metric("Failed", st.session_state.stats['failed_extractions'])

def process_document(uploaded_file, user_query: str = "") -> Optional[Dict[str, Any]]:
    """Process uploaded document through the workflow"""
    try:
        # Read file content
        pdf_content = uploaded_file.read()
        
        logger.info(f"Processing document: {uploaded_file.name}")
        
        # Process through workflow - this now returns JSON string
        workflow_result_json = workflow_tool.run(pdf_content, user_query)
        
        # Parse the JSON result
        try:
            workflow_result = json.loads(workflow_result_json)
        except json.JSONDecodeError:
            # Fallback - treat as error message
            workflow_result = {
                "success": False,
                "error": f"Invalid JSON response: {workflow_result_json}",
                "document_id": "unknown"
            }
        
        # Update session statistics
        st.session_state.stats['total_processed'] += 1
        if workflow_result.get('success', False):
            st.session_state.stats['successful_extractions'] += 1
        else:
            st.session_state.stats['failed_extractions'] += 1
        
        # Add to processing history
        processing_record = {
            'timestamp': datetime.now().isoformat(),
            'filename': uploaded_file.name,
            'file_size': len(pdf_content),
            'user_query': user_query,
            'result': workflow_result,
            'document_id': workflow_result.get('document_id', 'unknown')
        }
        
        st.session_state.processing_history.append(processing_record)
        st.session_state.current_document = processing_record
        
        # Add to conversation memory
        if user_query:
            ai_response = json.dumps(workflow_result, indent=2)
            vector_memory.add_conversation_turn(
                user_input=f"Process document {uploaded_file.name}: {user_query}",
                ai_response=ai_response,
                context={
                    "document_id": workflow_result.get('document_id'),
                    "filename": uploaded_file.name
                }
            )
        
        return workflow_result
        
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(error_msg)
        
        st.session_state.stats['total_processed'] += 1
        st.session_state.stats['failed_extractions'] += 1
        
        return {
            "success": False,
            "error": error_msg,
            "document_id": "error"
        }

def display_results(result: Dict[str, Any]):
    """Display processing results"""
    if not result:
        return
    
    if result.get('success', False):
        st.success("✅ Document processed successfully!")
        
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "📝 Extracted Text", "🔍 Analysis", "📊 Details"])
        
        with tab1:
            st.markdown("### Processing Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Document ID", result.get('document_id', 'Unknown'))
                stats = result.get('processing_stats', {})
                st.metric("Text Length", stats.get('text_length', 0))
                st.metric("Word Count", stats.get('word_count', 0))
            
            with col2:
                st.metric("Steps Completed", stats.get('steps_completed', 0))
                if result.get('language_detection'):
                    st.info(f"Language: {result['language_detection']}")
        
        with tab2:
            st.markdown("### Extracted Text")
            extracted_text = result.get('extracted_text', '')
            if extracted_text:
                st.text_area("Extracted Content", extracted_text, height=300)
            else:
                st.warning("No text was extracted from the document.")
        
        with tab3:
            st.markdown("### Field Analysis")
            
            # Field Mapping
            if result.get('field_mapping'):
                st.markdown("#### 🗂️ Field Mapping")
                st.text(result['field_mapping'])
            
            # Validation Results
            if result.get('validation'):
                st.markdown("#### ✅ Validation")
                st.text(result['validation'])
            
            # Sanity Check
            if result.get('sanity_check'):
                st.markdown("#### 🧠 Sanity Check")
                st.text(result['sanity_check'])
        
        with tab4:
            st.markdown("### Complete Results")
            st.json(result)
    
    else:
        st.error("❌ Document processing failed!")
        error_msg = result.get('error', 'Unknown error occurred')
        st.error(f"Error: {error_msg}")
        
        # Show partial results if available
        if result.get('document_id'):
            st.info(f"Document ID: {result['document_id']}")

def display_conversation_history():
    """Display conversation history using LangChain memory"""
    with st.expander("💬 Conversation History", expanded=False):
        try:
            # Get conversation history from LangChain memory
            messages = vector_memory.get_conversation_history(limit=10)
            
            if messages:
                for i, message in enumerate(messages):
                    if hasattr(message, 'content'):
                        if message.__class__.__name__ == 'HumanMessage':
                            st.markdown(f"**👤 User:** {message.content}")
                        elif message.__class__.__name__ == 'AIMessage':
                            st.markdown(f"**🤖 AI:** {message.content}")
                    else:
                        st.markdown(f"**Message {i+1}:** {str(message)}")
            else:
                st.info("No conversation history available.")
                
        except Exception as e:
            st.error(f"Error loading conversation history: {e}")

def main():
    """Main application function"""
    
    # Load styling
    load_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display sidebar
    display_sidebar()
    
    # Main content area
    st.markdown("### 📄 Upload Insurance Document")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload an insurance form in PDF format for processing"
    )
    
    # User query input
    user_query = st.text_area(
        "Additional Instructions (Optional)",
        placeholder="Enter any specific instructions or questions about the document...",
        help="Provide context or specific requirements for processing"
    )
    
    # Process button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        process_button = st.button(
            "🚀 Process Document",
            disabled=not uploaded_file,
            help="Process the uploaded document through the AI workflow"
        )
    
    # Process document when button is clicked
    if process_button and uploaded_file:
        with st.spinner("Processing document... This may take a few moments."):
            result = process_document(uploaded_file, user_query)
            display_results(result)
    
    # Display current document results if available
    elif st.session_state.current_document:
        st.markdown("### 📋 Current Document Results")
        display_results(st.session_state.current_document['result'])
    
    # Display conversation history
    display_conversation_history()
    
    # Processing history
    if st.session_state.processing_history:
        with st.expander("📚 Processing History", expanded=False):
            for i, record in enumerate(reversed(st.session_state.processing_history[-10:])):
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{record['filename']}**")
                        st.caption(f"Processed: {record['timestamp']}")
                    
                    with col2:
                        status = "✅ Success" if record['result'].get('success') else "❌ Failed"
                        st.markdown(status)
                    
                    with col3:
                        if st.button(f"View Details", key=f"view_{i}"):
                            st.session_state.current_document = record
                            st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Main application error: {e}")