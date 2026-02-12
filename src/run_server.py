import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Ensure PYTHONPATH includes src
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
