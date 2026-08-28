"""
Test script for the Feedback and Explainability endpoints (Prompt 8).
"""

import datetime
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_demo():
    print("="*60)
    print("  FEEDBACK & EXPLAINABILITY DEMO (Prompt 8)")
    print("="*60)
    
    # 1. Trigger ingestion so we have data
    print("\n[1] Triggering weather ingestion to populate risk store...")
    client.post("/api/ingest")
    
    # 2. Test MRI Explainability for Ward 1 (Nagpur)
    print("\n[2] Fetching MRI Explainability for Ward 1...")
    resp = client.get("/api/explain/mri/1")
    if resp.status_code == 200:
        data = resp.json()
        print("\n" + data["explanation_markdown"])
    else:
        print("Failed to fetch explanation:", resp.text)
        
    # 3. Submit Hospital Feedback (Simulating higher than expected admissions)
    print("\n[3] Submitting Hospital Feedback (Ground Truth Data)...")
    feedback_payload = {
        "ward_id": 1,
        "date": datetime.date.today().isoformat(),
        "reported_admissions": 120,
        "expected_admissions": 50,
        "notes": "Unexpected spike in elderly heatstroke cases."
    }
    
    resp = client.post("/api/feedback/hospital", json=feedback_payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Tuning Recommendation: {result['tuning_recommendation']}")
    else:
        print("Failed to submit feedback:", resp.text)
        
    print("\n" + "="*60)

if __name__ == "__main__":
    run_demo()
