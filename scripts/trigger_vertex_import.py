import os
import json
from google.cloud import discoveryengine_v1beta as discoveryengine

# Set your project ID
PROJECT_ID = "487213218407"
LOCATION = "global"
DATA_STORE_ID = "fadebender-knowledge"
BRANCH_ID = "0"  # Usually 0 for the default branch

def import_documents_gcs(project_id, location, data_store_id, branch_id, gcs_uri):
    """Imports documents from Cloud Storage."""
    client = discoveryengine.DocumentServiceClient()

    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch=branch_id,
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri], data_schema="custom"
        ),
        # Options: FULL, INCREMENTAL
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    print(f"Starting import from {gcs_uri}...")
    operation = client.import_documents(request=request)
    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()

    print(f"Imported documents: {response}")

if __name__ == "__main__":
    # Pointing to the specific file we just uploaded to ensure it gets picked up
    # You can also use wildcards like "gs://fadebender-knowledge/fadebender/*.html"
    GCS_URI = "gs://fadebender-knowledge/fadebender/user-guide.html" 
    
    print(f"Ready to import from {GCS_URI} to Data Store: {DATA_STORE_ID}")
    
    # Execute the import
    import_documents_gcs(PROJECT_ID, LOCATION, DATA_STORE_ID, BRANCH_ID, GCS_URI)
