"""
RAG (Retrieval Augmented Generation) Implementation
Uses ChromaDB for vector storage and retrieval of clinic FAQ information
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings


class FAQRagSystem:
    """RAG system for clinic FAQ information"""
    
    def __init__(
        self,
        clinic_info_path: str = "data/clinic_info.json",
        chroma_db_path: str = "chroma_db",
        collection_name: str = "clinic_faq"
    ):
        self.clinic_info_path = clinic_info_path
        self.chroma_db_path = chroma_db_path
        self.collection_name = collection_name
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.collection = self.client.create_collection(name=self.collection_name)
            print(f"Created new collection: {self.collection_name}")
            self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Load and index clinic information"""
        print("Initializing knowledge base...")
        
        # Load clinic info
        with open(self.clinic_info_path, 'r') as f:
            clinic_data = json.load(f)
        
        # Convert structured data to text documents
        documents = []
        metadatas = []
        
        # Process each section
        for section_name, section_data in clinic_data.items():
            docs, metas = self._process_section(section_name, section_data)
            documents.extend(docs)
            metadatas.extend(metas)
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        split_documents = []
        split_metadatas = []
        
        for doc, meta in zip(documents, metadatas):
            chunks = text_splitter.split_text(doc)
            for chunk in chunks:
                split_documents.append(chunk)
                split_metadatas.append(meta)
        
        # Generate embeddings and add to ChromaDB
        print(f"Adding {len(split_documents)} document chunks to vector store...")
        
        # Generate embeddings
        embeddings_list = self.embeddings.embed_documents(split_documents)
        
        # Add to ChromaDB
        ids = [f"doc_{i}" for i in range(len(split_documents))]
        
        self.collection.add(
            documents=split_documents,
            embeddings=embeddings_list,
            metadatas=split_metadatas,
            ids=ids
        )
        
        print(f"Knowledge base initialized with {len(split_documents)} chunks")
    
    def _process_section(self, section_name: str, section_data) -> tuple:
        """Process a section of clinic data into documents"""
        documents = []
        metadatas = []
        
        if isinstance(section_data, dict):
            # Handle nested dictionaries
            for key, value in section_data.items():
                if isinstance(value, (str, int, float)):
                    doc = f"{section_name.replace('_', ' ').title()} - {key.replace('_', ' ').title()}: {value}"
                    documents.append(doc)
                    metadatas.append({
                        "section": section_name,
                        "subsection": key,
                        "type": "info"
                    })
                elif isinstance(value, list):
                    if key == "accepted_insurance":
                        doc = f"Accepted Insurance: We accept {', '.join(value)}"
                        documents.append(doc)
                        metadatas.append({
                            "section": section_name,
                            "subsection": key,
                            "type": "list"
                        })
                    elif key == "payment_methods":
                        doc = f"Payment Methods: We accept {', '.join(value)}"
                        documents.append(doc)
                        metadatas.append({
                            "section": section_name,
                            "subsection": key,
                            "type": "list"
                        })
                    else:
                        doc = f"{key.replace('_', ' ').title()}: {', '.join(str(item) for item in value)}"
                        documents.append(doc)
                        metadatas.append({
                            "section": section_name,
                            "subsection": key,
                            "type": "list"
                        })
                elif isinstance(value, dict):
                    # Handle nested objects (like appointment types)
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict):
                            doc_parts = [f"{key.replace('_', ' ').title()} - {sub_key.replace('_', ' ').title()}"]
                            for k, v in sub_value.items():
                                doc_parts.append(f"{k.replace('_', ' ').title()}: {v}")
                            doc = "\n".join(doc_parts)
                            documents.append(doc)
                            metadatas.append({
                                "section": section_name,
                                "subsection": key,
                                "item": sub_key,
                                "type": "nested_info"
                            })
        elif isinstance(section_data, list):
            # Handle lists (like FAQs)
            for item in section_data:
                if isinstance(item, dict):
                    if "question" in item and "answer" in item:
                        doc = f"Q: {item['question']}\nA: {item['answer']}"
                        documents.append(doc)
                        metadatas.append({
                            "section": section_name,
                            "type": "faq"
                        })
                    else:
                        doc = json.dumps(item, indent=2)
                        documents.append(doc)
                        metadatas.append({
                            "section": section_name,
                            "type": "structured_data"
                        })
        
        return documents, metadatas
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search for relevant FAQ information
        
        Args:
            query: User's question
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching FAQ: {e}")
            return []
    
    def get_context_for_query(self, query: str, n_results: int = 3) -> str:
        """
        Get formatted context for a query
        
        Args:
            query: User's question
            n_results: Number of results to retrieve
            
        Returns:
            Formatted context string
        """
        results = self.search(query, n_results)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}]\n{result['content']}")
        
        return "\n\n".join(context_parts)
    
    def reset_knowledge_base(self):
        """Delete and reinitialize the knowledge base"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            self._initialize_knowledge_base()
            print("Knowledge base reset successfully")
        except Exception as e:
            print(f"Error resetting knowledge base: {e}")


# Global instance
def get_rag_system() -> FAQRagSystem:
    """Get or create RAG system instance"""
    return FAQRagSystem()
