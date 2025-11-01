from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import base64

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/images")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images and return base64 encoded strings"""
    try:
        uploaded_images = []
        
        for file in files:
            # Validate file type
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Le fichier {file.filename} n'est pas une image valide"
                )
            
            # Read file content
            content = await file.read()
            
            # Validate file size (max 5MB)
            if len(content) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"Le fichier {file.filename} est trop volumineux (max 5MB)"
                )
            
            # Convert to base64
            base64_image = base64.b64encode(content).decode("utf-8")
            data_url = f"data:{file.content_type};base64,{base64_image}"
            
            uploaded_images.append(data_url)
        
        return {"images": uploaded_images}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du téléchargement: {str(e)}"
        )
