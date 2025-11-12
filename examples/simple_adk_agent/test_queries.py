"""Test queries to exercise agent capabilities and build evaluation dataset."""

import time
from agent import create_agent


# Test queries covering different aspects
TEST_QUERIES = [
    # Simple factual questions (no tools needed)
    "What is Python?",
    "Explain what an API is",
    "What does HTTP stand for?",
    # Search tool queries
    "Search for the latest Python releases",
    "Find information about machine learning frameworks",
    "Look up best practices for REST APIs",
    # Calculator tool queries
    "Calculate 25 * 48",
    "What is 1024 divided by 16?",
    "Compute 15 + 37 * 2",
    # Complex queries (may use tools)
    "Search for Python tutorials and tell me the top 3 topics",
    "Calculate the area of a circle with radius 5",
    "Find the latest news about artificial intelligence",
    # Conversational queries
    "How can I improve my coding skills?",
    "What's the difference between a list and a tuple in Python?",
    "Explain recursion with a simple example",
    # Edge cases
    "Hello!",
    "Thanks for your help",
    "Can you help me?",
]


def run_test_queries():
    """Run all test queries and collect responses."""
    print("=" * 70)
    print("Running Test Queries")
    print("=" * 70)
    print(f"\nTotal queries: {len(TEST_QUERIES)}")
    print("This will generate a dataset for evaluation.\n")

    agent, wrapper = create_agent()

    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Query: {query}")

        try:
            start = time.time()
            response = agent.generate_content(query)
            duration = (time.time() - start) * 1000

            response_text = (
                response.text if hasattr(response, "text") else str(response)
            )
            print(f"Response: {response_text[:100]}...")
            print(f"⏱️  {duration:.0f}ms")

            results.append(
                {
                    "query": query,
                    "response": response_text,
                    "duration_ms": duration,
                    "success": True,
                }
            )

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(
                {
                    "query": query,
                    "response": None,
                    "duration_ms": 0,
                    "success": False,
                    "error": str(e),
                }
            )

        # Small delay to avoid rate limits
        time.sleep(1)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    avg_duration = (
        sum(r["duration_ms"] for r in results if r["success"]) / successful
        if successful > 0
        else 0
    )

    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"⏱️  Average response time: {avg_duration:.0f}ms")

    # Clean shutdown before script ends
    wrapper.shutdown()

    print("\n" + "=" * 70)
    print("✅ Test complete! Dataset ready for evaluation.")
    print("📊 View data in GCP Console (Logs, Traces, BigQuery)")
    print("=" * 70)


if __name__ == "__main__":
    run_test_queries()
