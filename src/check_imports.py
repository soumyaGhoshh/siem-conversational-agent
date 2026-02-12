try:
    from langchain.memory import ConversationBufferMemory
    print("langchain.memory.ConversationBufferMemory: Success")
except Exception as e:
    print(f"langchain.memory.ConversationBufferMemory: Failed - {e}")

try:
    from langchain_community.memory import ConversationBufferMemory
    print("langchain_community.memory.ConversationBufferMemory: Success")
except Exception as e:
    print(f"langchain_community.memory.ConversationBufferMemory: Failed - {e}")
