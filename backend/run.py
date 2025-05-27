from dotenv import load_dotenv
load_dotenv()

from backend.app import app

if __name__ == '__main__':
    import os
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
