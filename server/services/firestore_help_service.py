"""
Firestore-backed help service for instant factual queries
Uses structured data from Firestore instead of expensive RAG for simple queries
"""

import os
import logging
from typing import Dict, List, Any, Optional
from google.cloud import firestore

logger = logging.getLogger(__name__)


class FirestoreHelpService:
    """Fast help responses using Firestore structured data"""

    def __init__(self):
        project_id = os.getenv('FIRESTORE_PROJECT_ID', 'fadebender')
        database_id = os.getenv('FIRESTORE_DATABASE_ID', 'dev-display-value')

        self.db = firestore.Client(
            project=project_id,
            database=database_id
        )

        logger.info(f"[FirestoreHelp] Initialized with project={project_id}, database={database_id}")

    def get_preset_count(self, device_name: str) -> Optional[int]:
        """Get count of presets for a device using document ID prefix"""
        try:
            # Query by document ID prefix: reverb_ to reverb_~
            device_lower = device_name.lower()

            # Get all presets and filter by ID prefix in memory
            # This is efficient for small datasets (<1000 docs)
            presets = self.db.collection('presets').stream()

            prefix = f'{device_lower}_'
            count = sum(1 for preset in presets if preset.id.startswith(prefix))

            logger.info(f"[FirestoreHelp] Found {count} presets for {device_name}")
            return count if count > 0 else None

        except Exception as e:
            logger.error(f"[FirestoreHelp] Error counting presets: {e}")
            return None

    def list_all_presets(self, device_name: str, include_ids: bool = False) -> Optional[List[Dict[str, str]]]:
        """List all presets for a device using document ID prefix"""
        try:
            # Query by document ID prefix: reverb_ to reverb_~
            device_lower = device_name.lower()
            prefix = f'{device_lower}_'

            # Get all presets and filter by ID prefix in memory
            presets_ref = self.db.collection('presets').stream()

            presets = []
            for preset in presets_ref:
                doc_id = preset.id
                if not doc_id.startswith(prefix):
                    continue

                # Extract preset name from document ID (e.g., reverb_cathedral -> Cathedral)
                preset_name = doc_id.split('_', 1)[1] if '_' in doc_id else doc_id
                # Capitalize first letter of each word
                preset_name = ' '.join(word.capitalize() for word in preset_name.replace('_', ' ').split())

                preset_info = {
                    'name': preset_name,
                }
                if include_ids:
                    preset_info['id'] = doc_id
                presets.append(preset_info)

            logger.info(f"[FirestoreHelp] Listed {len(presets)} presets for {device_name}")
            return presets if presets else None

        except Exception as e:
            logger.error(f"[FirestoreHelp] Error listing presets: {e}")
            return None

    def get_device_parameters(self, device_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get list of parameters for a device from device_mappings"""
        try:
            # Query device_mappings collection for parameter metadata
            device_lower = device_name.lower()

            # Try to get device mapping document
            mappings_ref = self.db.collection('device_mappings') \
                .where('device_type', '==', device_lower) \
                .limit(1) \
                .stream()

            for mapping in mappings_ref:
                data = mapping.to_dict()
                params_meta = data.get('params_meta', [])

                if params_meta and isinstance(params_meta, list):
                    # Extract parameter info from list structure
                    param_info = []
                    for param in params_meta:
                        if isinstance(param, dict):
                            param_info.append({
                                'name': param.get('name', 'Unknown'),
                                'min': param.get('min'),
                                'max': param.get('max'),
                                'unit': param.get('unit'),
                                'control_type': param.get('control_type')
                            })

                    logger.info(f"[FirestoreHelp] Found {len(param_info)} parameters for {device_name}")
                    return param_info if param_info else None

            return None

        except Exception as e:
            logger.error(f"[FirestoreHelp] Error getting parameters: {e}")
            return None

    def get_preset_by_name(self, device_name: str, preset_name: str) -> Optional[Dict[str, Any]]:
        """Get specific preset details by document ID"""
        try:
            # Try direct document ID lookup first
            device_lower = device_name.lower()
            preset_lower = preset_name.lower().replace(' ', '_')
            doc_id = f'{device_lower}_{preset_lower}'

            try:
                doc_ref = self.db.collection('presets').document(doc_id)
                doc = doc_ref.get()
                if doc.exists:
                    logger.info(f"[FirestoreHelp] Found preset {preset_name} for {device_name} by direct ID")
                    return doc.to_dict()
            except:
                pass

            # Fall back to prefix search
            start_id = f'{device_lower}_'
            end_id = f'{device_lower}_~'
            presets_ref = self.db.collection('presets') \
                .where(firestore.FieldPath.document_id(), '>=', start_id) \
                .where(firestore.FieldPath.document_id(), '<', end_id) \
                .stream()

            # Search for matching preset (case-insensitive)
            preset_name_lower = preset_name.lower()
            for preset in presets_ref:
                doc_id = preset.id
                if preset_name_lower in doc_id.lower():
                    logger.info(f"[FirestoreHelp] Found preset {preset_name} for {device_name}")
                    return preset.to_dict()

            return None

        except Exception as e:
            logger.error(f"[FirestoreHelp] Error getting preset: {e}")
            return None

    def search_presets_by_parameter(
        self,
        device_name: str,
        param_name: str,
        operator: str,  # 'less_than', 'greater_than', 'equals'
        value: float
    ) -> Optional[List[Dict[str, Any]]]:
        """Search presets by parameter constraint using document ID prefix"""
        try:
            # Get all presets for device
            device_lower = device_name.lower()
            prefix = f'{device_lower}_'

            presets_ref = self.db.collection('presets').stream()

            matching_presets = []
            for preset in presets_ref:
                doc_id = preset.id
                if not doc_id.startswith(prefix):
                    continue

                data = preset.to_dict()
                # Check both parameter_values and parameter_display_values
                param_values = data.get('parameter_values', {})
                param_display_values = data.get('parameter_display_values', {})

                param_value = None
                if param_name in param_values:
                    param_value = param_values[param_name]
                elif param_name in param_display_values:
                    try:
                        param_value = float(param_display_values[param_name])
                    except (ValueError, TypeError):
                        continue

                if param_value is not None:
                    match = False
                    if operator == 'less_than' and param_value < value:
                        match = True
                    elif operator == 'greater_than' and param_value > value:
                        match = True
                    elif operator == 'equals' and abs(param_value - value) < 0.01:
                        match = True

                    if match:
                        # Extract preset name from document ID
                        preset_name = doc_id.split('_', 1)[1] if '_' in doc_id else doc_id
                        preset_name = ' '.join(word.capitalize() for word in preset_name.replace('_', ' ').split())

                        matching_presets.append({
                            'name': preset_name,
                            'id': doc_id,
                            f'{param_name}_value': param_value
                        })

            logger.info(f"[FirestoreHelp] Found {len(matching_presets)} presets matching {param_name} {operator} {value}")
            return matching_presets if matching_presets else None

        except Exception as e:
            logger.error(f"[FirestoreHelp] Error searching by parameter: {e}")
            return None


# Singleton instance
_firestore_help_service = None

def get_firestore_help_service() -> FirestoreHelpService:
    """Get or create FirestoreHelpService singleton"""
    global _firestore_help_service
    if _firestore_help_service is None:
        _firestore_help_service = FirestoreHelpService()
    return _firestore_help_service
