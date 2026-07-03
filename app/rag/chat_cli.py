import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.rag.rag_pipeline import RAGPipeline


def chat():
    rag = RAGPipeline()

    print("\n🚀 GraphRAG Chat CLI Started")
    print("Type 'exit' to quit\n")

    while True:

        query = input("🧑 You: ")

        if query.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        print("\n🔍 Thinking...\n")

        try:
            answer = rag.ask(query)

            print("\n🤖 Assistant:\n")
            print(answer)
            print("\n" + "-" * 60)

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    chat()