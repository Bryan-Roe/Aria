"""
RAG (Retrieval-Augmented Generation) Pipeline
Combines document retrieval with fine-tuned model generation
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch
from dataclasses import dataclass
from transformers import AutoModelForCausalLM, AutoTokenizer
import yaml


@dataclass
class RAGConfig:
    """RAG pipeline configuration"""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 3
    max_context_length: int = 2048
    retrieval_threshold: float = 0.7
    

class DocumentStore:
    """Vector store for document retrieval"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.embedding_model = None
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to store"""
        self.documents.extend(documents)
        print(f"Added {len(documents)} documents. Total: {len(self.documents)}")
    
    def load_from_directory(self, directory: str, extensions: List[str] = [".txt", ".md", ".json"]):
        """Load all documents from directory"""
        dir_path = Path(directory)
        loaded = 0
        
        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    chunks = self._chunk_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        self.documents.append({
                            "content": chunk,
                            "source": str(file_path),
                            "chunk_id": i,
                            "metadata": {"file_type": ext}
                        })
                    loaded += 1
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        print(f"Loaded {loaded} files, {len(self.documents)} chunks")
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.config.chunk_size - self.config.chunk_overlap):
            chunk = " ".join(words[i:i + self.config.chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def build_index(self):
        """Build vector index for retrieval"""
        print("Building vector index...")
        
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
            
            texts = [doc["content"] for doc in self.documents]
            self.embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            print(f"✓ Index built with {len(self.embeddings)} embeddings")
            
        except ImportError:
            print("⚠ sentence-transformers not installed. Using simple keyword matching.")
            self.embedding_model = None
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve most relevant documents for query"""
        if top_k is None:
            top_k = self.config.top_k_retrieval
        
        if self.embedding_model is not None:
            return self._semantic_retrieve(query, top_k)
        else:
            return self._keyword_retrieve(query, top_k)
    
    def _semantic_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Semantic retrieval using embeddings"""
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)[0]
        
        # Compute cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] >= self.config.retrieval_threshold:
                doc = self.documents[idx].copy()
                doc["score"] = float(similarities[idx])
                results.append(doc)
        
        return results
    
    def _keyword_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Simple keyword-based retrieval"""
        query_words = set(query.lower().split())
        scores = []
        
        for doc in self.documents:
            doc_words = set(doc["content"].lower().split())
            overlap = len(query_words & doc_words)
            scores.append(overlap / len(query_words) if query_words else 0)
        
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            doc = self.documents[idx].copy()
            doc["score"] = float(scores[idx])
            results.append(doc)
        
        return results
    
    def save_index(self, path: str):
        """Save document store and index"""
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save documents
        with open(save_path / "documents.json", "w") as f:
            json.dump(self.documents, f, indent=2)
        
        # Save embeddings if available
        if self.embeddings is not None:
            np.save(save_path / "embeddings.npy", self.embeddings)
        
        print(f"✓ Index saved to {save_path}")
    
    def load_index(self, path: str):
        """Load document store and index"""
        load_path = Path(path)
        
        with open(load_path / "documents.json") as f:
            self.documents = json.load(f)
        
        embeddings_file = load_path / "embeddings.npy"
        if embeddings_file.exists():
            self.embeddings = np.load(embeddings_file)
            
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(self.config.embedding_model)
            except ImportError:
                pass
        
        print(f"✓ Index loaded from {load_path}")


class RAGPipeline:
    """Complete RAG pipeline with retrieval and generation"""
    
    def __init__(
        self,
        model_path: str,
        document_store: DocumentStore,
        config: RAGConfig = None
    ):
        self.config = config or RAGConfig()
        self.document_store = document_store
        
        print(f"Loading model from {model_path}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def query(
        self,
        question: str,
        return_context: bool = False,
        max_new_tokens: int = 256
    ) -> Dict[str, Any]:
        """
        Query the RAG pipeline
        
        Args:
            question: User question
            return_context: Whether to return retrieved context
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with answer and optionally context
        """
        # Retrieve relevant documents
        retrieved_docs = self.document_store.retrieve(question)
        
        # Build context
        context = self._build_context(retrieved_docs)
        
        # Generate answer
        prompt = self._build_prompt(question, context)
        answer = self._generate(prompt, max_new_tokens)
        
        result = {
            "question": question,
            "answer": answer,
            "num_sources": len(retrieved_docs)
        }
        
        if return_context:
            result["context"] = retrieved_docs
        
        return result
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source = Path(doc["source"]).name if "source" in doc else f"Document {i}"
            content = doc["content"][:500]  # Truncate if needed
            context_parts.append(f"[Source {i}: {source}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt for generation"""
        prompt = f"""Answer the following question based on the provided context.

Context:
{context}

Question: {question}

Answer:"""
        return prompt
    
    def _generate(self, prompt: str, max_new_tokens: int) -> str:
        """Generate answer from prompt"""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_context_length
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
        
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated answer
        answer = full_text[len(prompt):].strip()
        return answer


def main():
    """CLI for RAG pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Pipeline")
    parser.add_argument("--model", type=str, required=True, help="Path to model")
    parser.add_argument("--docs", type=str, required=True, help="Path to documents directory")
    parser.add_argument("--index-dir", type=str, default="data_out/rag_index", help="Index directory")
    parser.add_argument("--query", type=str, help="Query to run")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild index")
    
    args = parser.parse_args()
    
    # Setup document store
    config = RAGConfig()
    doc_store = DocumentStore(config)
    
    index_path = Path(args.index_dir)
    if args.rebuild_index or not index_path.exists():
        print("Building new index...")
        doc_store.load_from_directory(args.docs)
        doc_store.build_index()
        doc_store.save_index(args.index_dir)
    else:
        print("Loading existing index...")
        doc_store.load_index(args.index_dir)
    
    # Setup RAG pipeline
    rag = RAGPipeline(args.model, doc_store, config)
    
    if args.interactive:
        print("\n=== RAG Interactive Mode ===")
        print("Enter your questions (or 'quit' to exit):\n")
        
        while True:
            question = input("Q: ").strip()
            if question.lower() in ["quit", "exit", "q"]:
                break
            
            if not question:
                continue
            
            result = rag.query(question, return_context=True)
            print(f"\nA: {result['answer']}")
            print(f"(Used {result['num_sources']} sources)\n")
    
    elif args.query:
        result = rag.query(args.query, return_context=True)
        print(f"\nQuestion: {result['question']}")
        print(f"Answer: {result['answer']}")
        print(f"\nSources used: {result['num_sources']}")


if __name__ == "__main__":
    main()
