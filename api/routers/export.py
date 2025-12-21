"""
Export API endpoints - CSV, JSON, Excel
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
import csv
import json
import io
from datetime import datetime

from storage.repo import GPURepository
from api.dependencies import get_db
from core.logging import get_logger

router = APIRouter()
logger = get_logger("api.export")


@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    """
    Export all listings as CSV
    """
    try:
        logger.info("Exporting data as CSV")
        
        with GPURepository(db) as repo:
            listings = repo.get_all_listings()
            
            if not listings:
                raise HTTPException(status_code=404, detail="No data to export")
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['ID', 'Model', 'Price (BGN)', 'Source', 'Date'])
            
            # Data
            for listing in listings:
                writer.writerow([
                    listing.id,
                    listing.model,
                    listing.price,
                    listing.source,
                    datetime.now().strftime('%Y-%m-%d')
                ])
            
            # Prepare response
            output.seek(0)
            filename = f"gpu_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            logger.info(f"CSV export successful: {len(listings)} rows")
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
            
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/json")
def export_json(db: Session = Depends(get_db)):
    """
    Export all data as JSON
    """
    try:
        logger.info("Exporting data as JSON")
        
        with GPURepository(db) as repo:
            # Get listings
            listings = repo.get_all_listings()
            
            # Get statistics
            models = repo.get_models()
            stats = {
                model: repo.get_price_stats(model) 
                for model in models
            }
            
            # Build export object
            export_data = {
                "export_date": datetime.now().isoformat(),
                "total_listings": len(listings),
                "total_models": len(models),
                "listings": [
                    {
                        "id": listing.id,
                        "model": listing.model,
                        "price": listing.price,
                        "source": listing.source
                    }
                    for listing in listings
                ],
                "statistics": stats
            }
            
            # Convert to JSON
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            filename = f"gpu_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            logger.info(f"JSON export successful: {len(listings)} listings")
            
            return Response(
                content=json_str,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
            
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/stats/csv")
def export_stats_csv(db: Session = Depends(get_db)):
    """
    Export statistics as CSV
    """
    try:
        logger.info("Exporting statistics as CSV")
        
        with GPURepository(db) as repo:
            models = repo.get_models()
            
            if not models:
                raise HTTPException(status_code=404, detail="No statistics to export")
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Model', 'Count', 'Min Price', 'Max Price', 
                'Median Price', 'Mean Price', '25th Percentile'
            ])
            
            # Data
            for model in sorted(models):
                stats = repo.get_price_stats(model)
                if stats:
                    writer.writerow([
                        model,
                        stats['count'],
                        f"{stats['min']:.2f}",
                        f"{stats['max']:.2f}",
                        f"{stats['median']:.2f}",
                        f"{stats['mean']:.2f}",
                        f"{stats['percentile_25']:.2f}"
                    ])
            
            output.seek(0)
            filename = f"gpu_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            logger.info(f"Statistics CSV export successful: {len(models)} models")
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
            
    except Exception as e:
        logger.error(f"Statistics CSV export error: {e}")
        raise HTTPException(status_code=500, detail="Export failed")