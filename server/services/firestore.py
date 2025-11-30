from google.cloud import firestore
import os
import logging

_db = None
logger = logging.getLogger(__name__)

def get_db():
    global _db
    if _db is None:
        project_id = os.getenv("FIRESTORE_PROJECT", os.getenv("GCP_PROJECT"))
        try:
            if project_id:
                _db = firestore.Client(project=project_id)
            else:
                # Fallback: relies on GOOGLE_APPLICATION_CREDENTIALS or gcloud auth
                _db = firestore.Client()
            logger.info(f"Firestore client initialized (project={_db.project})")
        except Exception as e:
            logger.warning(f"Could not init Firestore: {e}")
            return None
    return _db
