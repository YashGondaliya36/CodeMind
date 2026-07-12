import time
import httpx

# ── Configuration ─────────────────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000"
REPO_NAME = "codemind-backend"
# We will analyze our own backend directory!
LOCAL_PATH = r"F:\Data_Science_Project\OKF\backend"


def main():
    print("🚀 Starting End-to-End OKF Pipeline Verification")
    print(f"Backend Server: {BACKEND_URL}")
    print(f"Target Directory: {LOCAL_PATH}")
    print(f"Target Bundle Name: {REPO_NAME}")
    print("-" * 60)

    with httpx.Client(timeout=30.0) as client:
        # ── Step 1: Health check ──────────────────────────────────────────────
        print("\nStep 1: Verifying Backend and Gemini API status...")
        try:
            health_resp = client.get(f"{BACKEND_URL}/health")
            health_data = health_resp.json()
            print(f"Status: {health_resp.status_code} OK")
            print(f"Gemini Status: {health_data['gemini']['status'].upper()}")
            print(f"Model In Use: {health_data['gemini'].get('model', 'Unknown')}")
            if health_data['gemini']['status'] != "ok":
                print(f"❌ Gemini API Error: {health_data['gemini'].get('message', 'No details provided')}")
                print("Please check your .env API key and model settings.")
                return
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            print("Please make sure your FastAPI server is running (e.g., uvicorn main:app --reload)")
            return

        # ── Step 2: Trigger Analysis ──────────────────────────────────────────
        print("\nStep 2: Triggering codebase analysis (Producer)...")
        analyze_payload = {
            "source": LOCAL_PATH,
            "repo_name": REPO_NAME,
            "languages": ["python"]
        }
        
        try:
            analyze_resp = client.post(f"{BACKEND_URL}/repo/analyze", json=analyze_payload)
            if analyze_resp.status_code != 202:
                print(f"❌ Failed to start analysis: {analyze_resp.status_code}")
                print(analyze_resp.text)
                return
            
            job = analyze_resp.json()
            job_id = job["job_id"]
            print(f"Analysis successfully queued! Job ID: {job_id}")
        except Exception as e:
            print(f"❌ Error triggering analysis: {e}")
            return

        # ── Step 3: Poll Progress ──────────────────────────────────────────────
        print("\nStep 3: Polling analysis job progress...")
        while True:
            try:
                status_resp = client.get(f"{BACKEND_URL}/repo/status/{job_id}")
                status_data = status_resp.json()
                
                status = status_data["status"]
                progress = status_data["progress"]
                msg = status_data["message"]
                processed = status_data["files_processed"]
                total = status_data["total_files"]
                
                print(f"[{progress:3}%] Status: {status.upper()} | {msg} ({processed}/{total} files)")
                
                if status == "done":
                    print("\n🎉 OKF Bundle generated successfully!")
                    print(f"Saved to: {status_data['bundle_path']}")
                    break
                elif status == "error":
                    print(f"\n❌ Job failed with error: {status_data['error_detail']}")
                    return
                
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error polling job: {e}")
                time.sleep(2)

        # ── Step 4: Explore Bundle Index ──────────────────────────────────────
        print("\nStep 4: Fetching generated OKF file list (Bundle index)...")
        try:
            files_resp = client.get(f"{BACKEND_URL}/bundle/{REPO_NAME}/files")
            files_data = files_resp.json()
            print(f"Total OKF documentation files: {files_data['total_files']}")
            for idx, f in enumerate(files_data["files"], start=1):
                print(f"  {idx}. [{f['type'].upper()}] {f['title']} ({f['filename']})")
        except Exception as e:
            print(f"❌ Error listing files: {e}")

        # ── Step 5: Test Selective Retrieval Chat Agent ────────────────────────
        print("\nStep 5: Testing Chat Agent with selective context retrieval...")
        chat_payload = {
            "repo_name": REPO_NAME,
            "question": "How does the health check endpoint verify Gemini connectivity?",
            "max_files": 3
        }
        
        print(f"Question: \"{chat_payload['question']}\"")
        try:
            chat_resp = client.post(f"{BACKEND_URL}/chat/ask", json=chat_payload)
            chat_data = chat_resp.json()
            
            print("\n🤖 CodeMind Agent Answer:")
            print("-" * 60)
            print(chat_data["answer"])
            print("-" * 60)
            
            print("\n📂 Sources Used (Selective Context Retrieval):")
            for source in chat_data["sources_used"]:
                print(f"  📄 File: {source['filename']} (Relevance Score: {source['relevance_score']:.2f})")
            print(f"\nTotal files scanned: {chat_data['files_scanned']}")
            if chat_data['tokens_used']:
                print(f"Tokens consumed: {chat_data['tokens_used']}")
        except Exception as e:
            print(f"❌ Error during agent chat: {e}")


if __name__ == "__main__":
    main()
