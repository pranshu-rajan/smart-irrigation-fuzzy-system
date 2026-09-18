"""Reports and Export Router."""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from backend.app.schemas.allocation import ReportGenerateRequest, ReportResponse
from backend.app.services.report_service import ReportService
from backend.app.database.client import DatabaseRepository, get_db_repository

router = APIRouter(prefix="/reports", tags=["Reports"])
report_service = ReportService()


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    req: ReportGenerateRequest,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Generate a comprehensive engineering audit PDF report with ReportLab."""
    try:
        return report_service.generate_pdf_report(req, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")


@router.post("/simulation/{simulation_id}", response_model=ReportResponse)
def generate_report_for_simulation(
    simulation_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Generate audit PDF report directly from simulation ID."""
    try:
        req = ReportGenerateRequest(simulation_id=simulation_id, include_charts=True)
        return report_service.generate_pdf_report(req, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")


@router.get("/{report_id}")
def get_report_metadata(
    report_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Get metadata for a generated PDF report."""
    rec = db.get_report_metadata(report_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return rec



@router.get("/download/{report_id}")
def download_pdf_report(
    report_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Download the generated publication-grade PDF report."""
    rec = db.get_report_metadata(report_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    file_path = Path(rec["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report PDF file missing from disk")

    return FileResponse(
        path=str(file_path),
        filename=rec["filename"],
        media_type="application/pdf",
    )


@router.get("/csv/{simulation_id}")
def export_simulation_csv(
    simulation_id: str,
    db: DatabaseRepository = Depends(get_db_repository),
):
    """Export raw simulation step telemetry as a CSV file."""
    try:
        csv_data = report_service.export_csv_summary(simulation_id, db=db)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=simulation_{simulation_id}.csv"},
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export error: {str(e)}")
