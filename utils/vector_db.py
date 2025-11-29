"""
Minimal Vector Store for semantic search over chat history.
Uses Qdrant Cloud and Gemini's free embedding-001 model.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini for embeddings (uses same API key)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class VectorStore:
    """Manages vector embeddings for semantic search over chat history"""
    
    def __init__(self):
        """Initialize connection to Qdrant Cloud"""
        try:
            self.client = QdrantClient(
                url=os.getenv('QDRANT_URL'),
                api_key=os.getenv('QDRANT_API_KEY')
            )
            self.collection_name = "openanalyst_chat_history"
            self._ensure_collection_exists()
            logger.info("VectorStore initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")
            self.client = None
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        if not self.client:
            return
            
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Gemini embedding-001 produces 768-dimensional vectors
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
            
            # Ensure payload indexes exist for filtered searches
            self._ensure_payload_indexes()
            
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
    
    def _ensure_payload_indexes(self):
        """Create payload indexes for efficient filtering"""
        if not self.client:
            return
            
        try:
            from qdrant_client.models import PayloadSchemaType
            
            # Create indexes for commonly filtered fields
            index_fields = {
                "tier": PayloadSchemaType.KEYWORD,
                "domain": PayloadSchemaType.KEYWORD,
                "user_id": PayloadSchemaType.KEYWORD,
                "role": PayloadSchemaType.KEYWORD,
            }
            
            for field_name, field_type in index_fields.items():
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=field_type
                    )
                    logger.info(f"Created payload index for field: {field_name}")
                except Exception as index_error:
                    # Index might already exist, that's OK
                    if "already exists" not in str(index_error).lower():
                        logger.debug(f"Index for {field_name} might exist: {index_error}")
                        
        except Exception as e:
            logger.warning(f"Error creating payload indexes: {e}")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Gemini's free text-embedding-004 model.
        This model has better quota limits than embedding-001.
        
        Args:
            text: Text to embed
            
        Returns:
            768-dimensional embedding vector
        """
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def store_chat_message(
        self, 
        role: str, 
        content: str, 
        dataset_name: Optional[str] = None,
        domain: Optional[str] = None,
        schema_signature: Optional[str] = None,
        query_type: Optional[str] = None,
        tier: Optional[str] = None,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> bool:
        """
        Store a chat message with its embedding and HYBRID MODEL metadata.
        
        HYBRID B2C/B2B MODEL:
        - tier="public": Community templates (visible to all)
        - tier="user": Personal workspace (user_id isolation)
        - tier="team": Team collaboration (team_id isolation)
        
        Args:
            role: 'user' or 'assistant'
            content: The message content
            dataset_name: Optional dataset context
            domain: Data domain (sales/marketing/hr/financial/survey/product/business/operations/general)
            schema_signature: Column schema pattern
            query_type: Type of query (simple/complex/chart/aggregation/etc)
            tier: Access tier ('public'/'user'/'team')
            user_id: User identifier for user tier
            team_id: Team identifier for team tier
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            # Create text representation for embedding
            text_for_embedding = f"{role}: {content}"
            
            embedding = self._generate_embedding(text_for_embedding)
            if not embedding:
                return False
            
            # Generate unique ID
            point_id = str(uuid.uuid4())
            
            # Create point with HYBRID MODEL metadata
            payload = {
                "role": role,
                "content": content,
                "dataset": dataset_name or "unknown",
                "timestamp": datetime.now().isoformat(),
                "type": "chat_message",
                "tier": tier or "user",  # Default to user tier
                "usage_count": 0  # Track how many times this analysis is used
            }
            
            # Add optional domain-aware metadata
            if domain:
                payload["domain"] = domain
            if schema_signature:
                payload["schema_signature"] = schema_signature
            if query_type:
                payload["query_type"] = query_type
            
            # Add namespace isolation
            if user_id:
                payload["user_id"] = user_id
            if team_id:
                payload["team_id"] = team_id
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Stored {role} message in vector DB (domain: {domain})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing chat message: {e}")
            return False
    
    def search_similar_messages(
        self, 
        query_text: str, 
        limit: int = 3,
        min_score: float = 0.7
    ) -> List[Dict]:
        """
        Find similar past messages based on semantic similarity.
        
        Args:
            query_text: The query to search for
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of similar messages with scores
        """
        if not self.client:
            return []
            
        try:
            query_embedding = self._generate_embedding(query_text)
            if not query_embedding:
                return []
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Filter by minimum score and format results
            similar_messages = []
            for hit in results:
                if hit.score >= min_score:
                    similar_messages.append({
                        "score": hit.score,
                        "role": hit.payload.get("role"),
                        "content": hit.payload.get("content"),
                        "dataset": hit.payload.get("dataset"),
                        "timestamp": hit.payload.get("timestamp")
                    })
            
            logger.info(f"Found {len(similar_messages)} similar messages for query")
            return similar_messages
            
        except Exception as e:
            logger.error(f"Error searching similar messages: {e}")
            return []
    
    def get_relevant_context(
        self, 
        query_text: str, 
        limit: int = 3
    ) -> Optional[str]:
        """
        Get relevant past context for current query as formatted string.
        
        Args:
            query_text: Current user query
            limit: Max number of past messages to include
            
        Returns:
            Formatted context string or None
        """
        similar = self.search_similar_messages(query_text, limit=limit)
        
        if not similar:
            return None
        
        context_parts = []
        for msg in similar:
            role_label = "User" if msg['role'] == 'user' else "Assistant"
            context_parts.append(
                f"[Past {role_label} ({msg['dataset']}): {msg['content'][:200]}...]"
            )
        
        return "\n".join(context_parts)
    
    def test_connection(self) -> bool:
        """Test if connection to Qdrant is working"""
        if not self.client:
            return False
            
        try:
            collections = self.client.get_collections()
            logger.info(f"Successfully connected to Qdrant. Collections: {len(collections.collections)}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global instance (lazy initialization)
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get or create the global VectorStore instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance


# Add these methods to VectorStore class by monkey-patching
def _search_by_domain(self, query_text: str, domain: str, limit: int = 5, min_score: float = 0.7) -> List[Dict]:
    """Search for similar analyses filtered by domain"""
    if not self.client:
        return []
        
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_embedding = self._generate_embedding(query_text)
        if not query_embedding:
            return []
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(must=[FieldCondition(key="domain", match=MatchValue(value=domain))]),
            limit=limit
        )
        
        similar_analyses = []
        for hit in results:
            if hit.score >= min_score:
                similar_analyses.append({
                    "score": hit.score,
                    "content": hit.payload.get("content"),
                    "domain": hit.payload.get("domain"),
                    "query_type": hit.payload.get("query_type"),
                    "dataset": hit.payload.get("dataset"),
                    "timestamp": hit.payload.get("timestamp")
                })
        
        return similar_analyses
        
    except Exception as e:
        logger.error(f"Error searching by domain: {e}")
        return []

def _seed_example_analyses(self, examples: List[Dict]) -> bool:
    """Pre-populate vector DB with COMMUNITY EXPERT TEMPLATES (200+)"""
    if not self.client:
        return False
        
    try:
        points = []
        for example in examples:
            embedding = self._generate_embedding(example['content'])
            if not embedding:
                continue
            
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "role": "example",
                    "content": example['content'],
                    "domain": example.get('domain', 'general'),
                    "query_type": example.get('query_type', 'analysis'),
                    "dataset": "community",
                    "timestamp": datetime.now().isoformat(),
                    "type": "example_analysis",
                    "tier": example.get('tier', 'public'),  # Community templates are public
                    "usage_count": 0,  # Will grow organically
                    "is_verified": True,  # Expert-curated templates
                    "is_seed": True
                }
            )
            points.append(point)
        
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"Seeded {len(points)} COMMUNITY expert templates 🚀")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error seeding examples: {e}")
        return False

def _search_by_tier(self, query_text: str, tier: str, domain: Optional[str] = None, user_id: Optional[str] = None, limit: int = 10, min_score: float = 0.6) -> List[Dict]:
    """
    Search analyses filtered by HYBRID MODEL tier (public/user/team).
    
    Args:
        query_text: Query to search for
        tier: 'public' (community) or 'user' (personal) or 'team' (collaboration)
        domain: Optional domain filter
        user_id: Required for user/team tier to filter by ownership
        limit: Max results
        min_score: Minimum similarity score
        
    Returns:
        List of similar analyses with metadata
    """
    if not self.client:
        return []
        
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_embedding = self._generate_embedding(query_text)
        if not query_embedding:
            return []
        
        # Build filter conditions
        filter_conditions = [FieldCondition(key="tier", match=MatchValue(value=tier))]
        
        # Add domain filter if specified
        if domain:
            filter_conditions.append(FieldCondition(key="domain", match=MatchValue(value=domain)))
        
        # Add user isolation for non-public tiers
        if tier != "public" and user_id:
            filter_conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(must=filter_conditions),
            limit=limit
        )
        
        similar_analyses = []
        for hit in results:
            if hit.score >= min_score:
                similar_analyses.append({
                    "score": hit.score,
                    "content": hit.payload.get("content"),
                    "domain": hit.payload.get("domain"),
                    "query_type": hit.payload.get("query_type"),
                    "tier": hit.payload.get("tier"),
                    "usage_count": hit.payload.get("usage_count", 0),
                    "is_verified": hit.payload.get("is_verified", False),
                    "timestamp": hit.payload.get("timestamp")
                })
        
        logger.info(f"Found {len(similar_analyses)} analyses (tier={tier}, domain={domain})")
        return similar_analyses
        
    except Exception as e:
        logger.error(f"Error searching by tier: {e}")
        return []

def _increment_usage_count(self, point_id: str) -> bool:
    """Increment usage counter when an analysis is used"""
    # This would need point_id to be stored and tracked - simplified for now
    # In production, we'd track point IDs and update usage_count
    return True

# Monkey-patch the methods onto VectorStore class
VectorStore.search_by_domain = _search_by_domain
VectorStore.seed_example_analyses = _seed_example_analyses
VectorStore.search_by_tier = _search_by_tier
VectorStore.increment_usage_count = _increment_usage_count


def index_sample_dataset(dataset_name: str, df, vector_store: VectorStore) -> bool:
    """
    Pre-index a sample dataset with common insights for instant responses.
    
    Args:
        dataset_name: Name of the dataset (e.g., "E-commerce Sales")
        df: pandas DataFrame with the data
        vector_store: VectorStore instance
        
    Returns:
        True if indexing succeeded, False otherwise
    """
    try:
        import pandas as pd
        
        # Generate common insights based on dataset type
        insights = []
        
        # Basic stats that apply to all datasets
        insights.append({
            "question": f"What's the shape of the {dataset_name} dataset?",
            "answer": f"The {dataset_name} dataset has {len(df):,} rows and {len(df.columns)} columns."
        })
        
        insights.append({
            "question": f"What columns are in the {dataset_name} dataset?",
            "answer": f"Columns: {', '.join(df.columns.tolist())}"
        })
        
        # Dataset-specific insights
        if "sales" in dataset_name.lower() or "ecommerce" in dataset_name.lower():
            # E-commerce insights
            if 'total_sales' in df.columns or 'revenue' in df.columns:
                rev_col = 'total_sales' if 'total_sales' in df.columns else 'revenue'
                total_revenue = df[rev_col].sum()
                insights.append({
                    "question": "What is the total revenue?",
                    "answer": f"Total revenue across all transactions is ${total_revenue:,.2f}"
                })
            
            if 'product' in df.columns or 'product_name' in df.columns:
                prod_col = 'product' if 'product' in df.columns else 'product_name'
                top_products = df[prod_col].value_counts().head(5)
                insights.append({
                    "question": "What are the top selling products?",
                    "answer": f"Top 5 products: {', '.join([f'{prod} ({count} sales)' for prod, count in top_products.items()])}"
                })
        
        elif "survey" in dataset_name.lower() or "satisfaction" in dataset_name.lower():
            # Survey insights
            if 'satisfaction_score' in df.columns or 'rating' in df.columns:
                score_col = 'satisfaction_score' if 'satisfaction_score' in df.columns else 'rating'
                avg_score = df[score_col].mean()
                insights.append({
                    "question": "What is the average satisfaction score?",
                    "answer": f"Average satisfaction score is {avg_score:.2f} out of 5"
                })
            
            if 'feedback' in df.columns or 'comments' in df.columns:
                insights.append({
                    "question": "How much feedback data is available?",
                    "answer": f"There are {len(df)} customer feedback entries in this dataset"
                })
        
        elif "financial" in dataset_name.lower() or "metrics" in dataset_name.lower():
            # Financial insights
            if 'revenue' in df.columns and 'expenses' in df.columns:
                total_profit = (df['revenue'] - df['expenses']).sum()
                insights.append({
                    "question": "What is the net profit?",
                    "answer": f"Net profit is ${total_profit:,.2f}"
                })
            
            if 'month' in df.columns or 'date' in df.columns:
                insights.append({
                    "question": "What time period does this data cover?",
                    "answer": f"Financial data covering {len(df)} time periods"
                })
        
        # Store all insights in vector DB
        success_count = 0
        for insight in insights:
            # Store question-answer pairs
            q_stored = vector_store.store_chat_message(
                role="user",
                content=insight["question"],
                dataset_name=dataset_name
            )
            a_stored = vector_store.store_chat_message(
                role="assistant",
                content=insight["answer"],
                dataset_name=dataset_name
            )
            if q_stored and a_stored:
                success_count += 1
        
        logger.info(f"Indexed {success_count} insights for {dataset_name}")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Failed to index sample dataset {dataset_name}: {e}")
        return False


def index_all_sample_datasets() -> Dict[str, bool]:
    """
    Index all available sample datasets for instant responses.
    
    Returns:
        Dict mapping dataset names to indexing success status
    """
    results = {}
    vector_store = get_vector_store()
    
    if not vector_store or not vector_store.client:
        logger.warning("Vector store not available, skipping sample dataset indexing")
        return results
    
    sample_files = {
        "E-commerce Sales": "Sample_Datasets/sample_ecommerce_sales.csv",
        "Customer Survey": "Sample_Datasets/sample_customer_survey.csv",
        "Financial Metrics": "Sample_Datasets/sample_financial_metrics.csv"
    }
    
    for name, filename in sample_files.items():
        try:
            import pandas as pd
            import os
            
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                success = index_sample_dataset(name, df, vector_store)
                results[name] = success
            else:
                logger.warning(f"Sample file not found: {filename}")
                results[name] = False
                
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            results[name] = False
    
    return results


# Flag to track if sample datasets have been indexed
VECTOR_DB_ENABLED = True
_samples_indexed = False

def ensure_samples_indexed():
    """Ensure sample datasets are indexed (call once on app startup)"""
    global _samples_indexed
    if not _samples_indexed and VECTOR_DB_ENABLED:
        try:
            results = index_all_sample_datasets()
            _samples_indexed = any(results.values())
            if _samples_indexed:
                logger.info(f"Sample datasets indexed: {results}")
        except Exception as e:
            logger.error(f"Failed to index samples: {e}")
