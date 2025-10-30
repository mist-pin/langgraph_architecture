import os
import sys
import traceback
import uvicorn
from dotenv import load_dotenv

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from react_agent.fastapi_server import app


# ===============================================
# ====================setup======================
# ===============================================
load_dotenv()
reload = False
host = "0.0.0.0"
port = int(os.environ.get("PORT", 8300))
is_development = os.environ.get("DEVELOPMENT_SERVER",False) == "TRUE"


# ===============================================
# ====================runner=====================
# ===============================================
def main():
    try:

        if is_development:
            app = "react_agent.fastapi_server:app"
            reload = True        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=reload
        )

    except Exception as e:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()