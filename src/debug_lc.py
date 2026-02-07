import sys
import os

try:
    import langchain
    print(f"Langchain path: {langchain.__path__}")
    print(f"Langchain version: {langchain.__version__}")
except Exception as e:
    print(f"Error importing langchain: {e}")

try:
    import langchain.memory
    print("langchain.memory imported successfully")
except Exception as e:
    print(f"Error importing langchain.memory: {e}")

try:
    from langchain.memory import ConversationBufferMemory
    print("ConversationBufferMemory imported")
except Exception as e:
    print(f"Error importing ConversationBufferMemory: {e}")

try:
    import langchain_community
    print(f"Langchain community path: {langchain_community.__path__}")
except:
    print("No langchain_community")
