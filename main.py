"""
Main FastAPI application for Industrial AI - Quotation Intelligence.
AI Powered Motor Rewinding Quotation Generator.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import config
from database import init_db, get_db_session, Inventory, Quotation, generate_inventory_id, generate_quotation_number
from vision_ai import analyze_nameplate
from engineering import lookup_manufacturer, estimate_engineering
from pricing import get_pricing, update_pricing, calculate_costs
from quotation import generate_quotation, get_quotation, get_all_quotations, delete_quotation
from pdf_generator import generate_pdf
from utils import validate_file, save_upload, optimize_image
from proposal import save_proposal, get_proposal, get_all_proposals, delete_proposal
from graph_db import save_quotation_to_graph, get_quotations_from_graph, get_quotation_from_graph, compare_quotations_graph, is_connected as neo4j_connected, close_driver as close_neo4j

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_TITLE,
    description="AI Powered Motor Rewinding Quotation System",
    version=config.APP_VERSION,
)

# Session middleware for login
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Login credentials
USERS = {
    "admin": hashlib.sha256("coral@2026".encode()).hexdigest(),
    "ramku": hashlib.sha256("motor@123".encode()).hexdigest(),
    "user": hashlib.sha256("user".encode()).hexdigest(),
}

# Create directories
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
os.makedirs(config.QUOTATION_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/quotations", StaticFiles(directory="quotations"), name="quotations")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    # Ensure proposals directory exists
    os.makedirs(os.path.join(config.QUOTATION_DIR, "proposals"), exist_ok=True)
    # Check Neo4j connectivity
    if neo4j_connected():
        print("✅ Neo4j connected - graph features enabled")
    else:
        print("⚠️  Neo4j not available - graph features disabled (quotations still saved as proposals)")


@app.on_event("shutdown")
async def shutdown_event():
    close_neo4j()


# ==================== AUTH HELPERS ====================

def is_authenticated(request: Request) -> bool:
    """Check if user is logged in."""
    return request.session.get("user") is not None


def require_auth(request: Request):
    """Redirect to login if not authenticated."""
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)
    return None


# ==================== AUTH ROUTES ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": config.APP_TITLE,
    })


@app.post("/api/login")
async def api_login(request: Request):
    """Handle login."""
    body = await request.json()
    username = body.get("username", "").strip().lower()
    password = body.get("password", "")

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if username in USERS and USERS[username] == password_hash:
        request.session["user"] = username
        return JSONResponse(content={"success": True, "user": username})
    else:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Invalid username or password"}
        )


@app.get("/logout")
async def logout(request: Request):
    """Logout and redirect to login."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ==================== PAGE ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Render home page with upload and inventory table."""
    auth_redirect = require_auth(request)
    if auth_redirect:
        return auth_redirect
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": config.APP_TITLE,
        "subtitle": config.APP_SUBTITLE,
        "current_date": datetime.utcnow().strftime("%d %B %Y"),
    })


@app.get("/inventory/{inventory_id}", response_class=HTMLResponse)
async def inventory_detail_page(request: Request, inventory_id: str):
    """Render inventory detail page."""
    auth_redirect = require_auth(request)
    if auth_redirect:
        return auth_redirect
    db = get_db_session()
    try:
        inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Inventory not found")

        extracted_data = json.loads(inv.extracted_data) if inv.extracted_data else {}
        engineering_data = json.loads(inv.engineering_data) if inv.engineering_data else {}

        # Get extracted fields (handle nested structure)
        extracted = extracted_data.get("extracted", extracted_data)

        return templates.TemplateResponse("inventory_detail.html", {
            "request": request,
            "title": config.APP_TITLE,
            "inventory": {
                "inventory_id": inv.inventory_id,
                "image_path": inv.image_path,
                "manufacturer": inv.manufacturer,
                "model": inv.model,
                "status": inv.status,
                "created_date": inv.created_date.strftime("%d %B %Y, %H:%M") if inv.created_date else "",
            },
            "extracted": extracted,
            "engineering": engineering_data,
        })
    finally:
        db.close()


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Render quotation history page."""
    auth_redirect = require_auth(request)
    if auth_redirect:
        return auth_redirect
    return templates.TemplateResponse("history.html", {
        "request": request,
        "title": config.APP_TITLE,
    })


@app.get("/quotation/{quotation_number}", response_class=HTMLResponse)
async def quotation_preview_page(request: Request, quotation_number: str):
    """Render quotation preview page."""
    quotation_data = get_quotation(quotation_number)
    if not quotation_data:
        raise HTTPException(status_code=404, detail="Quotation not found")

    return templates.TemplateResponse("quotation_preview.html", {
        "request": request,
        "title": config.APP_TITLE,
        "quotation": quotation_data,
        "company": {
            "name": config.COMPANY_NAME,
            "address": config.COMPANY_ADDRESS,
            "phone": config.COMPANY_PHONE,
            "email": config.COMPANY_EMAIL,
            "website": config.COMPANY_WEBSITE,
        },
    })


# ==================== API ROUTES ====================

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload motor nameplate image, create inventory entry, and analyze."""
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file
        is_valid, error_msg = validate_file(file.filename, file_size)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": error_msg}
            )

        # Save file
        file_path = save_upload(content, file.filename)

        # Optimize image
        optimize_image(file_path)

        # Create inventory record
        db = get_db_session()
        try:
            inventory_id = generate_inventory_id(db)
            inventory = Inventory(
                inventory_id=inventory_id,
                image_name=file.filename,
                image_path=file_path,
                status="Processing",
            )
            db.add(inventory)
            db.commit()
        finally:
            db.close()

        # Analyze nameplate (uses stored data for now, LLM later)
        try:
            vision_result = await analyze_nameplate(file_path)
        except Exception as e:
            db = get_db_session()
            try:
                inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
                if inv:
                    inv.status = "Error"
                    db.commit()
            finally:
                db.close()
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Analysis Error: {str(e)}"}
            )

        # Extract data from vision result
        extracted = vision_result.get("extracted", vision_result)

        # Manufacturer lookup
        manufacturer = extracted.get("manufacturer", "")
        power = extracted.get("power") or extracted.get("kva") or ""
        mfr_data = lookup_manufacturer(manufacturer, power)

        # Engineering estimation
        engineering_data = estimate_engineering(extracted, mfr_data)

        # Update inventory record with all extracted data
        db = get_db_session()
        try:
            inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
            if inv:
                inv.manufacturer = extracted.get("manufacturer")
                inv.model = extracted.get("model") or extracted.get("equipment_type")
                inv.serial_number = extracted.get("serial_number")
                inv.frame_number = extracted.get("frame_number")
                inv.equipment_type = extracted.get("equipment_type")
                inv.power = extracted.get("power") or extracted.get("kva")
                inv.voltage = extracted.get("voltage")
                inv.current = extracted.get("current") or extracted.get("amps")
                inv.rpm = extracted.get("rpm")
                inv.frequency = extracted.get("frequency")
                inv.power_factor = extracted.get("power_factor")
                inv.phase = extracted.get("phase")
                inv.duty = extracted.get("duty")
                inv.insulation_class = extracted.get("insulation_class")
                inv.connection = extracted.get("connection")
                inv.bearing_number = extracted.get("bearing_number")
                inv.cooling = extracted.get("cooling")
                inv.protection = extracted.get("protection")
                inv.weight = extracted.get("weight")
                inv.country = extracted.get("country")
                inv.manufacturer_address = extracted.get("manufacturer_address")
                inv.extracted_data = json.dumps(vision_result)
                inv.engineering_data = json.dumps(engineering_data)
                inv.status = "Completed"
                db.commit()
        finally:
            db.close()

        return JSONResponse(content={
            "success": True,
            "inventory_id": inventory_id,
            "image_path": file_path,
            "manufacturer": extracted.get("manufacturer"),
            "model": extracted.get("model") or extracted.get("equipment_type"),
            "power": extracted.get("power") or extracted.get("kva"),
            "status": "Completed",
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/inventory-list")
async def api_inventory_list():
    """Get all inventory records for the table."""
    db = get_db_session()
    try:
        records = db.query(Inventory).order_by(Inventory.created_date.desc()).all()
        inventory = []
        for inv in records:
            inventory.append({
                "inventory_id": inv.inventory_id,
                "image_path": inv.image_path,
                "manufacturer": inv.manufacturer,
                "model": inv.model,
                "power": inv.power,
                "voltage": inv.voltage,
                "rpm": inv.rpm,
                "status": inv.status,
                "created_date": inv.created_date.strftime("%d %b %Y, %H:%M") if inv.created_date else "",
            })
        return JSONResponse(content={"success": True, "inventory": inventory})
    finally:
        db.close()


@app.get("/api/inventory/{inventory_id}")
async def api_get_inventory(inventory_id: str):
    """Get inventory details by ID."""
    db = get_db_session()
    try:
        inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
        if not inv:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Inventory not found"}
            )

        return JSONResponse(content={
            "success": True,
            "inventory": {
                "inventory_id": inv.inventory_id,
                "image_path": inv.image_path,
                "manufacturer": inv.manufacturer,
                "model": inv.model,
                "power": inv.power,
                "voltage": inv.voltage,
                "current": inv.current,
                "rpm": inv.rpm,
                "frequency": inv.frequency,
                "status": inv.status,
                "created_date": inv.created_date.strftime("%Y-%m-%d %H:%M") if inv.created_date else "",
                "extracted_data": json.loads(inv.extracted_data) if inv.extracted_data else {},
                "engineering_data": json.loads(inv.engineering_data) if inv.engineering_data else {},
            }
        })
    finally:
        db.close()


@app.post("/api/generate-quotation")
async def api_generate_quotation(request: Request):
    """Generate quotation with optional engineering overrides."""
    try:
        body = await request.json()
        inventory_id = body.get("inventory_id")
        engineering_overrides = body.get("engineering_overrides", {})

        if not inventory_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "inventory_id is required"}
            )

        # Generate quotation
        quotation_data = generate_quotation(inventory_id, engineering_overrides)

        # Generate PDF
        pdf_path = generate_pdf(quotation_data)

        # Update quotation with PDF path
        db = get_db_session()
        try:
            qt = db.query(Quotation).filter(
                Quotation.quotation_number == quotation_data["quotation_number"]
            ).first()
            if qt:
                qt.pdf_path = pdf_path
                db.commit()
        finally:
            db.close()

        quotation_data["pdf_path"] = pdf_path

        # Save proposal JSON (source of truth for Quotation screen & Compare)
        proposal_path = save_proposal(quotation_data)

        # Save to Neo4j graph (non-blocking, graceful fallback)
        save_quotation_to_graph(quotation_data, proposal_path)

        return JSONResponse(content={
            "success": True,
            "quotation": quotation_data,
            "proposal_path": proposal_path,
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/quotations")
async def api_get_quotations():
    """Get all quotations for history page. Uses proposals as source of truth, falls back to DB."""
    try:
        # Primary: Load from proposal JSON files (persistent across DB resets)
        proposals = get_all_proposals()
        if proposals:
            return JSONResponse(content={"success": True, "quotations": proposals})

        # Fallback: Load from SQLite database
        quotations = get_all_quotations()
        return JSONResponse(content={"success": True, "quotations": quotations})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/quotation/{quotation_number}")
async def api_get_quotation(quotation_number: str):
    """Get a specific quotation. Checks proposal files first, then DB."""
    try:
        # Check proposal file first (survives DB resets)
        proposal_data = get_proposal(quotation_number)
        if proposal_data:
            return JSONResponse(content={"success": True, "quotation": proposal_data})

        # Fallback to database
        quotation_data = get_quotation(quotation_number)
        if not quotation_data:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Quotation not found"}
            )
        return JSONResponse(content={"success": True, "quotation": quotation_data})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.delete("/api/quotation/{quotation_number}")
async def api_delete_quotation(quotation_number: str):
    """Delete a quotation from DB and proposal file."""
    try:
        # Delete from DB
        success = delete_quotation(quotation_number)
        # Delete proposal file
        delete_proposal(quotation_number)

        if not success:
            # If DB didn't have it but proposal existed, still success
            proposal_existed = delete_proposal(quotation_number)
            if not proposal_existed:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": "Quotation not found"}
                )
        return JSONResponse(content={"success": True, "message": "Quotation deleted"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/download/{quotation_number}")
async def download_quotation(quotation_number: str):
    """Download quotation PDF."""
    db = get_db_session()
    try:
        quotation = db.query(Quotation).filter(
            Quotation.quotation_number == quotation_number
        ).first()

        if not quotation or not quotation.pdf_path:
            raise HTTPException(status_code=404, detail="PDF not found")

        if not os.path.exists(quotation.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file missing")

        return FileResponse(
            quotation.pdf_path,
            media_type="application/pdf",
            filename=f"{quotation_number}.pdf",
        )
    finally:
        db.close()


@app.get("/api/pricing")
async def api_get_pricing():
    """Get current pricing."""
    return JSONResponse(content={"success": True, "pricing": get_pricing()})


@app.get("/api/neo4j/status")
async def api_neo4j_status():
    """Check Neo4j connectivity status."""
    connected = neo4j_connected()
    return JSONResponse(content={
        "success": True,
        "connected": connected,
        "message": "Neo4j connected" if connected else "Neo4j not available"
    })


@app.get("/api/neo4j/quotations")
async def api_neo4j_quotations():
    """Get all quotations from Neo4j graph."""
    quotations = get_quotations_from_graph()
    return JSONResponse(content={"success": True, "quotations": quotations, "source": "neo4j"})


@app.get("/api/neo4j/compare/{qt1}/{qt2}")
async def api_neo4j_compare(qt1: str, qt2: str):
    """Compare two quotations using Neo4j graph relationships."""
    comparison = compare_quotations_graph(qt1, qt2)
    if comparison is None:
        # Fallback: compare using proposals
        p1 = get_proposal(qt1)
        p2 = get_proposal(qt2)
        if p1 and p2:
            return JSONResponse(content={"success": True, "comparison": {"quotation_1": p1, "quotation_2": p2}, "source": "proposals"})
        return JSONResponse(status_code=404, content={"success": False, "error": "One or both quotations not found"})
    return JSONResponse(content={"success": True, "comparison": comparison, "source": "neo4j"})


@app.put("/api/pricing")
async def api_update_pricing(request: Request):
    """Update pricing."""
    try:
        body = await request.json()
        updated = update_pricing(body)
        return JSONResponse(content={"success": True, "pricing": updated})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
