"""Insurance Form Processing Workflow - Completely Serialization Safe"""

from pathlib import Path
import uuid
import json
from typing import Dict, Any, Optional, Union
from agno.utils.log import logger
from config.vector_memory import vector_memory
from utils.exception_handling import setup_openai_exception_suppression

# Import only the functions we need, not the agents
from .ocr_agent import extract_text_from_pdf
from langdetect import detect

# Setup exception suppression
setup_openai_exception_suppression()

def detect_language_simple(text: str) -> str:
    """Simple language detection without agents"""
    try:
        logger.info("Running simple language detection")
        code = detect(text.strip().replace('\n', ' ')[:1000])  # Use first 1000 chars
        lang_map = {'en': 'english', 'ms': 'malay', 'id': 'malay'}
        result = lang_map.get(code, 'english')
        logger.info(f"Detected language: {result}")
        return result
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return "english"

def extract_fields_simple(text: str) -> str:
    """Simple field extraction without agents"""
    try:
        logger.info("Running simple field extraction")
        
        # Simple regex-based field extraction
        import re
        
        fields = {}
        
        # Policy number patterns
        policy_patterns = [
            r'policy\s*(?:no|number|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'pol\s*no\s*:?\s*([A-Z0-9\-]+)',
            r'(?:policy|pol)\s*([A-Z0-9\-]{5,})'
        ]
        
        for pattern in policy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['policy_number'] = match.group(1).strip()
                break
        
        # Name patterns
        name_patterns = [
            r'(?:policy\s*holder|insured|name)\s*:?\s*([A-Za-z\s]+)',
            r'name\s*:?\s*([A-Za-z\s]{2,30})',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['policy_holder_name'] = match.group(1).strip()
                break
        
        # Age patterns
        age_patterns = [
            r'age\s*:?\s*(\d{1,3})',
            r'(\d{1,3})\s*years?\s*old'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 <= age <= 120:
                    fields['age'] = age
                break
        
        # Premium patterns
        premium_patterns = [
            r'premium\s*:?\s*\$?([0-9,]+\.?\d*)',
            r'amount\s*:?\s*\$?([0-9,]+\.?\d*)'
        ]
        
        for pattern in premium_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    fields['premium_amount'] = amount
                    break
                except ValueError:
                    continue
        
        result = json.dumps(fields, indent=2)
        logger.info(f"Extracted fields: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Field extraction error: {e}")
        return json.dumps({"error": f"Field extraction failed: {str(e)}"})

def validate_fields_simple(fields_json: str) -> str:
    """Simple field validation without agents"""
    try:
        logger.info("Running simple field validation")
        
        fields = json.loads(fields_json) if isinstance(fields_json, str) else fields_json
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate policy number
        if 'policy_number' in fields:
            policy_num = fields['policy_number']
            if len(policy_num) < 3:
                validation_result["errors"].append("Policy number too short")
                validation_result["is_valid"] = False
        else:
            validation_result["warnings"].append("Policy number not found")
        
        # Validate age
        if 'age' in fields:
            age = fields['age']
            if age < 0 or age > 120:
                validation_result["errors"].append("Invalid age range")
                validation_result["is_valid"] = False
        
        # Validate premium
        if 'premium_amount' in fields:
            premium = fields['premium_amount']
            if premium < 0:
                validation_result["errors"].append("Negative premium amount")
                validation_result["is_valid"] = False
        
        result = json.dumps(validation_result, indent=2)
        logger.info(f"Validation result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return json.dumps({
            "is_valid": False,
            "errors": [f"Validation failed: {str(e)}"],
            "warnings": []
        })

def sanity_check_simple(validation_json: str) -> str:
    """Simple sanity check without agents"""
    try:
        logger.info("Running simple sanity check")
        
        validation_data = json.loads(validation_json) if isinstance(validation_json, str) else validation_json
        
        sanity_result = {
            "is_sane": True,
            "flags": []
        }
        
        # Check if validation passed
        if not validation_data.get("is_valid", True):
            sanity_result["flags"].append("Failed basic validation")
        
        # Check error count
        error_count = len(validation_data.get("errors", []))
        if error_count > 3:
            sanity_result["flags"].append("Too many validation errors")
            sanity_result["is_sane"] = False
        
        result = json.dumps(sanity_result, indent=2)
        logger.info(f"Sanity check result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Sanity check error: {e}")
        return json.dumps({
            "is_sane": False,
            "flags": [f"Sanity check failed: {str(e)}"]
        })

def generate_response_simple(language: str, fields: str, validation: str, sanity: str) -> str:
    """Simple response generation without agents"""
    try:
        logger.info("Running simple response generation")
        
        # Parse the inputs
        try:
            fields_data = json.loads(fields) if isinstance(fields, str) else fields
            validation_data = json.loads(validation) if isinstance(validation, str) else validation
            sanity_data = json.loads(sanity) if isinstance(sanity, str) else sanity
        except json.JSONDecodeError:
            fields_data = {}
            validation_data = {"is_valid": False}
            sanity_data = {"is_sane": False}
        
        # Generate final response
        final_response = {
            "processing_status": "completed",
            "detected_language": language,
            "extracted_fields": fields_data,
            "validation_passed": validation_data.get("is_valid", False),
            "sanity_passed": sanity_data.get("is_sane", False),
            "total_errors": len(validation_data.get("errors", [])),
            "total_warnings": len(validation_data.get("warnings", [])),
            "processing_flags": sanity_data.get("flags", []),
            "confidence_score": 0.8 if validation_data.get("is_valid", False) else 0.4
        }
        
        result = json.dumps(final_response, indent=2)
        logger.info(f"Generated response: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return json.dumps({
            "processing_status": "failed",
            "error": f"Response generation failed: {str(e)}"
        })

class InsuranceWorkflowTool:
    """Tool for coordinating insurance form processing workflow - Serialization Safe"""
    name = "insurance_workflow"
    description = "Processes insurance PDF forms through the complete workflow using simple functions"

    def __init__(self):
        self.workflow_steps = [
            "workflow_start",
            "ocr_extraction", 
            "language_detection",
            "field_mapping",
            "validation",
            "sanity_check",
            "response_generation"
        ]

    def process_pdf_content(self, pdf_content: bytes, user_query: str = "") -> Dict[str, Any]:
        """
        Process PDF content through the workflow - completely serialization safe
        """
        document_id = str(uuid.uuid4())
        
        try:
            logger.info("Starting serialization-safe insurance form processing workflow")
            
            # Add workflow start memory
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="workflow_start",
                input_data=f"User query: {user_query}",
                output_data="Workflow initiated with simple functions"
            )
            
            # Step 1: OCR Extraction - Use serializable function
            logger.info(f"Step 1: OCR Extraction for document {document_id}")
            ocr_result = extract_text_from_pdf(pdf_content)
            
            if not ocr_result["success"]:
                error_msg = f"OCR failed: {ocr_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "document_id": document_id
                }
            
            extracted_text = ocr_result["extracted_text"]
            
            # Add OCR memory
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="ocr_extraction",
                input_data="PDF content",
                output_data=extracted_text[:500],
                metadata={
                    "text_length": ocr_result["text_length"],
                    "word_count": ocr_result["word_count"]
                }
            )
            
            # Step 2: Language Detection - Use simple function
            logger.info(f"Step 2: Language Detection for document {document_id}")
            language_response = detect_language_simple(extracted_text)
            
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="language_detection",
                input_data=extracted_text[:200],
                output_data=language_response
            )
            
            # Step 3: Field Mapping - Use simple function
            logger.info(f"Step 3: Field Mapping for document {document_id}")
            mapping_response = extract_fields_simple(extracted_text)
            
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="field_mapping",
                input_data=extracted_text[:200],
                output_data=mapping_response[:500]
            )
            
            # Step 4: Validation - Use simple function
            logger.info(f"Step 4: Validation for document {document_id}")
            validation_response = validate_fields_simple(mapping_response)
            
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="validation",
                input_data=mapping_response[:200],
                output_data=validation_response[:500]
            )
            
            # Step 5: Sanity Check - Use simple function
            logger.info(f"Step 5: Sanity Check for document {document_id}")
            sanity_response = sanity_check_simple(validation_response)
            
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="sanity_check",
                input_data=validation_response[:200],
                output_data=sanity_response[:500]
            )
            
            # Step 6: Response Generation - Use simple function
            logger.info(f"Step 6: Response Generation for document {document_id}")
            final_response = generate_response_simple(
                language_response, mapping_response, validation_response, sanity_response
            )
            
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="response_generation",
                input_data="All processed data",
                output_data=final_response[:500]
            )
            
            # Prepare final result - all strings are serializable
            result = {
                "success": True,
                "document_id": document_id,
                "extracted_text": extracted_text,
                "language_detection": language_response,
                "field_mapping": mapping_response,
                "validation": validation_response,
                "sanity_check": sanity_response,
                "final_response": final_response,
                "processing_stats": {
                    "text_length": ocr_result["text_length"],
                    "word_count": ocr_result["word_count"],
                    "steps_completed": len(self.workflow_steps)
                }
            }
            
            logger.info(f"Serialization-safe workflow completed successfully for document {document_id}")
            return result
            
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            logger.error(error_msg)
            
            # Add error memory
            vector_memory.add_processing_memory(
                document_id=document_id,
                step="workflow_error",
                input_data=user_query,
                output_data=error_msg
            )
            
            return {
                "success": False,
                "error": error_msg,
                "document_id": document_id
            }

    def run(self, pdf_content: bytes, user_query: str = "") -> str:
        """Main workflow runner that returns serializable string results"""
        try:
            result = self.process_pdf_content(pdf_content, user_query)
            
            # Convert to JSON string for serialization safety
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "document_id": "unknown"
            }
            return json.dumps(error_result, indent=2)

# Create workflow tool instance
workflow_tool = InsuranceWorkflowTool()

# Note: Removed the lead_agent to eliminate all threading issues
# The workflow tool can be used directly by main.py
