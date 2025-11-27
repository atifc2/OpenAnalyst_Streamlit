"""
Quick test script to verify Qdrant Vector DB integration
"""

from utils.vector_db import get_vector_store

def test_connection():
    """Test basic connection to Qdrant"""
    print("🔗 Testing Qdrant connection...")
    vector_store = get_vector_store()
    
    if vector_store.test_connection():
        print("✅ Connected to Qdrant successfully!")
        return True
    else:
        print("❌ Failed to connect to Qdrant")
        return False

def test_store_and_search():
    """Test storing and searching messages"""
    print("\n📝 Testing store and search...")
    vector_store = get_vector_store()
    
    # Store some test messages
    test_messages = [
        ("user", "What are the sales trends for Q1?", "sales_data.csv"),
        ("assistant", "Based on the analysis, Q1 sales show a 15% increase compared to last year.", "sales_data.csv"),
        ("user", "Show me customer satisfaction scores", "customer_survey.csv"),
        ("assistant", "Customer satisfaction averaged 4.2 out of 5, with highest scores in product quality.", "customer_survey.csv"),
    ]
    
    print("Storing test messages...")
    for role, content, dataset in test_messages:
        success = vector_store.store_chat_message(role, content, dataset)
        if success:
            print(f"  ✅ Stored {role} message")
        else:
            print(f"  ❌ Failed to store {role} message")
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    queries = [
        "sales performance",
        "customer feedback",
        "revenue growth"
    ]
    
    for query in queries:
        print(f"\n  Query: '{query}'")
        results = vector_store.search_similar_messages(query, limit=2, min_score=0.5)
        if results:
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"    {i}. Score: {result['score']:.3f} | {result['role']}: {result['content'][:60]}...")
        else:
            print("  No results found")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Qdrant Vector DB Integration Test")
    print("=" * 60)
    
    if test_connection():
        test_store_and_search()
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
    else:
        print("\n❌ Connection test failed. Check your credentials in .env")

if __name__ == "__main__":
    main()
