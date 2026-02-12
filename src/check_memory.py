try:
    from langchain.memory import ConversationBufferMemory
    print("Found in langchain.memory")
except ImportError:
    print("Not found in langchain.memory")

try:
    from langchain_community.memory import ConversationBufferMemory
    print("Found in langchain_community.memory")
except ImportError:
    print("Not found in langchain_community.memory")
