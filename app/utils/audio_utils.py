"""Utilidades para manejo de archivos de audio"""
import os
import tempfile
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)


async def validate_audio_file(file: UploadFile) -> None:
    """
    Valida el archivo de audio subido
    
    Args:
        file: Archivo subido por el usuario
        
    Raises:
        HTTPException: Si el archivo no es válido
    """
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_formats_list:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido. Use: {', '.join(settings.allowed_formats_list)}"
        )
    
    # Validar tamaño
    file.file.seek(0, 2)  # Ir al final del archivo
    file_size = file.file.tell()
    file.file.seek(0)  # Volver al inicio
    
    if file_size > settings.max_audio_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo: {settings.max_audio_size_mb}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío"
        )
    
    logger.info(f"Archivo validado: {file.filename} ({file_size} bytes)")


async def save_temp_file(file: UploadFile) -> str:
    """
    Guarda el archivo subido en un directorio temporal
    
    Args:
        file: Archivo a guardar
        
    Returns:
        str: Ruta al archivo temporal
    """
    try:
        # Crear directorio temporal si no existe
        temp_dir = Path("temp_audio")
        temp_dir.mkdir(exist_ok=True)
        
        # Crear archivo temporal con extensión apropiada
        file_ext = Path(file.filename).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            dir=temp_dir
        )
        
        # Guardar contenido
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        logger.info(f"Archivo guardado temporalmente: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Error al guardar archivo temporal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al procesar el archivo"
        )


def cleanup_temp_file(file_path: str) -> None:
    """
    Elimina un archivo temporal
    
    Args:
        file_path: Ruta al archivo a eliminar
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Archivo temporal eliminado: {file_path}")
    except Exception as e:
        logger.warning(f"No se pudo eliminar archivo temporal {file_path}: {str(e)}")
