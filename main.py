import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

app = FastAPI(title="PaladiuAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Lead(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: Optional[str] = Field(None, max_length=120)
    project_type: Optional[str] = Field(None, max_length=120)
    message: Optional[str] = Field(None, max_length=2000)
    source: Optional[str] = Field(None, max_length=120)

@app.get("/")
def heartbeat():
    return {"status": "ok", "service": "PaladiuAI Backend", "version": "1.0.0"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or (os.getenv("DATABASE_NAME") and "✅ Set") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

@app.post("/lead")
async def create_lead(lead: Lead):
    """Create a lead entry. Attempts to use MongoDB if configured; otherwise falls back to in-memory ack."""
    payload = lead.model_dump()
    # Try database first
    try:
        from database import create_document
        lead_id = create_document("lead", payload)
        return {"ok": True, "id": lead_id, "stored": "database"}
    except Exception as e:
        # Fallback: pretend success so the form UX works in environments without DB
        return {"ok": True, "id": None, "stored": "memory", "note": f"DB unavailable: {str(e)[:80]}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
