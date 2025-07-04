"""Vector Memory Manager - ChromaDB only with LangChain Conversation Buffer Memory"""

import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from agno.utils.log import logger
import atexit
import os
from pathlib import Path

class VectorMemoryManager:
    """Vector-only memory manager with LangChain conversation buffer"""
    
    def __init__(self, persist_directory: str = "tmp/vector_store"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.chroma_client = None
        self.processing_collection = None
        self.conversation_collection = None
        self.conversation_memory = None
        
        self._initialize_chromadb()
        self._initialize_conversation_memory()
        
        # Register cleanup
        atexit.register(self.cleanup)
        logger.info("Vector Memory Manager initialized with LangChain conversation buffer")
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB with proper configuration"""
        try:
            # Initialize ChromaDB with persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collections
            self.processing_collection = self.chroma_client.get_or_create_collection(
                name="insurance_processing_memories",
                metadata={"description": "Insurance form processing memories"}
            )
            
            self.conversation_collection = self.chroma_client.get_or_create_collection(
                name="conversation_memories", 
                metadata={"description": "Conversation history and context"}
            )
            
            logger.info("ChromaDB collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _initialize_conversation_memory(self):
        """Initialize LangChain conversation buffer memory"""
        try:
            self.conversation_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
                output_key="output"
            )
            logger.info("LangChain conversation memory initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize conversation memory: {e}")
            raise
    
    def add_processing_memory(self, document_id: str, step: str, input_data: str, 
                            output_data: str, metadata: Optional[Dict] = None) -> str:
        """Add processing memory to vector store"""
        try:
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Prepare metadata
            memory_metadata = {
                "document_id": document_id,
                "step": step,
                "timestamp": timestamp,
                "memory_id": memory_id,
                **(metadata or {})
            }
            
            # Create document content for embedding
            content = f"Step: {step}\nInput: {input_data[:500]}\nOutput: {output_data[:500]}"
            
            # Add to ChromaDB
            self.processing_collection.add(
                documents=[content],
                metadatas=[memory_metadata],
                ids=[memory_id]
            )
            
            logger.info(f"Added processing memory {memory_id} for step {step}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add processing memory: {e}")
            return ""
    
    def add_conversation_turn(self, user_input: str, ai_response: str, 
                           context: Optional[Dict] = None):
        """Add conversation turn to both LangChain memory and vector store"""
        try:
            # Add to LangChain memory
            self.conversation_memory.save_context(
                inputs={"input": user_input},
                outputs={"output": ai_response}
            )
            
            # Also store in vector database for searchability
            conversation_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            metadata = {
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "type": "conversation_turn",
                **(context or {})
            }
            
            # Create searchable content
            content = f"User: {user_input}\nAI: {ai_response}"
            
            self.conversation_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[conversation_id]
            )
            
            logger.info(f"Added conversation turn {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to add conversation turn: {e}")
            return ""
    
    def get_conversation_history(self, limit: int = 10) -> List[BaseMessage]:
        """Get conversation history from LangChain memory"""
        try:
            # Get messages from LangChain memory
            memory_variables = self.conversation_memory.load_memory_variables({})
            messages = memory_variables.get("chat_history", [])
            
            # Return last N messages
            return messages[-limit:] if messages else []
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def search_processing_memories(self, query: str, document_id: Optional[str] = None, 
                                 limit: int = 5) -> List[Dict]:
        """Search processing memories by content"""
        try:
            # Build where clause
            where = {}
            if document_id:
                where["document_id"] = document_id
            
            # Search in ChromaDB
            results = self.processing_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where if where else None
            )
            
            # Format results
            memories = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    memory = {
                        "id": results["ids"][0][i],
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None
                    }
                    memories.append(memory)
            
            logger.info(f"Found {len(memories)} processing memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search processing memories: {e}")
            return []
    
    def search_conversation_history(self, query: str, limit: int = 5) -> List[Dict]:
        """Search conversation history by content"""
        try:
            results = self.conversation_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            conversations = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    conversation = {
                        "id": results["ids"][0][i],
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None
                    }
                    conversations.append(conversation)
            
            logger.info(f"Found {len(conversations)} conversations for query: {query}")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            processing_count = self.processing_collection.count()
            conversation_count = self.conversation_collection.count()
            
            return {
                "total_processing_memories": processing_count,
                "total_conversations": conversation_count,
                "storage_type": "ChromaDB Vector Store",
                "langchain_memory": "ConversationBufferMemory"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_processing_memories": 0,
                "total_conversations": 0,
                "storage_type": "ChromaDB Vector Store (Error)",
                "langchain_memory": "ConversationBufferMemory (Error)"
            }
    
    def clear_processing_memory(self, document_id: Optional[str] = None):
        """Clear processing memories"""
        try:
            if document_id:
                # Delete specific document memories
                results = self.processing_collection.get(
                    where={"document_id": document_id}
                )
                if results["ids"]:
                    self.processing_collection.delete(ids=results["ids"])
                    logger.info(f"Cleared processing memories for document {document_id}")
            else:
                # Clear all processing memories
                self.chroma_client.delete_collection("insurance_processing_memories")
                self.processing_collection = self.chroma_client.create_collection(
                    name="insurance_processing_memories",
                    metadata={"description": "Insurance form processing memories"}
                )
                logger.info("Cleared all processing memories")
                
        except Exception as e:
            logger.error(f"Failed to clear processing memory: {e}")
    
    def clear_conversation_memory(self):
        """Clear conversation memory"""
        try:
            # Clear LangChain memory
            self.conversation_memory.clear()
            
            # Clear vector store
            self.chroma_client.delete_collection("conversation_memories")
            self.conversation_collection = self.chroma_client.create_collection(
                name="conversation_memories",
                metadata={"description": "Conversation history and context"}
            )
            
            logger.info("Cleared conversation memory")
            
        except Exception as e:
            logger.error(f"Failed to clear conversation memory: {e}")
    
    def clear_memory(self):
        """Clear all memories"""
        try:
            self.clear_processing_memory()
            self.clear_conversation_memory()
            logger.info("All memories cleared")
            
        except Exception as e:
            logger.error(f"Failed to clear all memory: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # ChromaDB handles its own cleanup
            logger.info("Vector memory manager cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")

# Global instance
vector_memory = VectorMemoryManager()
