"""
Test cases for the Insurance Form Processing Workflow - Vector Database Version
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import uuid
from datetime import datetime

# Import the workflow components
from agents.workflow import InsuranceWorkflowTool, extract_agent_response_content
from config.vector_memory import VectorMemoryManager

class TestInsuranceWorkflow(unittest.TestCase):
    """Test cases for the insurance form processing workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.workflow = InsuranceWorkflowTool()
        self.test_pdf_content = b"Test PDF content"
        self.test_user_query = "Extract insurance details"
        
    def test_workflow_initialization(self):
        """Test workflow initialization"""
        self.assertIsNotNone(self.workflow)
        self.assertEqual(len(self.workflow.workflow_steps), 7)
        self.assertIn("ocr_extraction", self.workflow.workflow_steps)
        self.assertIn("language_detection", self.workflow.workflow_steps)
        
    @patch('agents.workflow.extract_text_from_pdf')
    @patch('agents.workflow.language_detector_agent')
    @patch('agents.workflow.field_mapper_agent')
    @patch('agents.workflow.validation_agent')
    @patch('agents.workflow.sanity_agent')
    @patch('agents.workflow.response_agent')
    @patch('agents.workflow.vector_memory')
    def test_successful_workflow(self, mock_vector_memory, mock_response_agent, 
                               mock_sanity_agent, mock_validation_agent, 
                               mock_field_mapper_agent, mock_language_detector_agent,
                               mock_extract_text):
        """Test successful workflow execution"""
        
        # Mock OCR extraction
        mock_extract_text.return_value = {
            "success": True,
            "extracted_text": "Test insurance document text",
            "text_length": 100,
            "word_count": 20,
            "error": None
        }
        
        # Mock agent responses
        mock_language_detector_agent.run.return_value = "English"
        mock_field_mapper_agent.run.return_value = '{"policy_number": "12345"}'
        mock_validation_agent.run.return_value = '{"is_valid": true}'
        mock_sanity_agent.run.return_value = '{"is_sane": true}'
        mock_response_agent.run.return_value = '{"status": "success"}'
        
        # Mock vector memory
        mock_vector_memory.add_processing_memory.return_value = str(uuid.uuid4())
        
        # Execute workflow
        result = self.workflow.process_pdf_content(self.test_pdf_content, self.test_user_query)
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertIn("document_id", result)
        self.assertIn("extracted_text", result)
        self.assertIn("processing_stats", result)
        
        # Verify vector memory was called
        self.assertTrue(mock_vector_memory.add_processing_memory.called)
        
    @patch('agents.workflow.extract_text_from_pdf')
    @patch('agents.workflow.vector_memory')
    def test_ocr_failure(self, mock_vector_memory, mock_extract_text):
        """Test workflow when OCR fails"""
        
        # Mock OCR failure
        mock_extract_text.return_value = {
            "success": False,
            "extracted_text": "",
            "text_length": 0,
            "word_count": 0,
            "error": "PDF could not be processed"
        }
        
        # Mock vector memory
        mock_vector_memory.add_processing_memory.return_value = str(uuid.uuid4())
        
        # Execute workflow
        result = self.workflow.process_pdf_content(self.test_pdf_content, self.test_user_query)
        
        # Verify failure handling
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("OCR failed", result["error"])
        
    def test_workflow_run_returns_json_string(self):
        """Test that workflow.run() returns a JSON string"""
        
        with patch.object(self.workflow, 'process_pdf_content') as mock_process:
            mock_process.return_value = {
                "success": True,
                "document_id": "test-id-123",
                "message": "Test completed"
            }
            
            result = self.workflow.run(self.test_pdf_content, self.test_user_query)
            
            # Verify result is a JSON string
            self.assertIsInstance(result, str)
            
            # Verify it can be parsed as JSON
            parsed_result = json.loads(result)
            self.assertTrue(parsed_result["success"])
            self.assertEqual(parsed_result["document_id"], "test-id-123")
            
    def test_workflow_exception_handling(self):
        """Test workflow exception handling"""
        
        with patch('agents.workflow.extract_text_from_pdf') as mock_extract_text:
            mock_extract_text.side_effect = Exception("Unexpected error")
            
            with patch('agents.workflow.vector_memory') as mock_vector_memory:
                mock_vector_memory.add_processing_memory.return_value = str(uuid.uuid4())
                
                result = self.workflow.run(self.test_pdf_content, self.test_user_query)
                
                # Verify error handling
                parsed_result = json.loads(result)
                self.assertFalse(parsed_result["success"])
                self.assertIn("error", parsed_result)

class TestAgentResponseExtraction(unittest.TestCase):
    """Test cases for agent response content extraction"""
    
    def test_extract_string_response(self):
        """Test extracting content from string response"""
        response = "Test response content"
        result = extract_agent_response_content(response)
        self.assertEqual(result, "Test response content")
        
    def test_extract_object_with_content_attribute(self):
        """Test extracting content from object with content attribute"""
        mock_response = Mock()
        mock_response.content = "Test content from object"
        
        result = extract_agent_response_content(mock_response)
        self.assertEqual(result, "Test content from object")
        
    def test_extract_dict_like_response(self):
        """Test extracting content from dict-like response"""
        mock_response = Mock()
        mock_response.__dict__ = {"content": "Test dict content"}
        
        result = extract_agent_response_content(mock_response)
        self.assertEqual(result, "Test dict content")
        
    def test_extract_fallback_to_str(self):
        """Test fallback to string conversion"""
        mock_response = Mock()
        mock_response.__str__ = Mock(return_value="Fallback string")
        
        result = extract_agent_response_content(mock_response)
        self.assertEqual(result, "Fallback string")
        
    def test_extract_handles_exceptions(self):
        """Test that extraction handles exceptions gracefully"""
        mock_response = Mock()
        mock_response.content = Mock(side_effect=Exception("Access error"))
        mock_response.__dict__ = Mock(side_effect=Exception("Dict error"))
        mock_response.__str__ = Mock(side_effect=Exception("String error"))
        
        result = extract_agent_response_content(mock_response)
        self.assertIn("Agent response extraction failed", result)

class TestVectorMemoryIntegration(unittest.TestCase):
    """Test cases for vector memory integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.workflow = InsuranceWorkflowTool()
        
    @patch('agents.workflow.vector_memory')
    def test_vector_memory_integration(self, mock_vector_memory):
        """Test that workflow integrates with vector memory"""
        
        # Mock vector memory methods
        mock_vector_memory.add_processing_memory.return_value = str(uuid.uuid4())
        
        # Mock successful workflow execution
        with patch('agents.workflow.extract_text_from_pdf') as mock_extract_text:
            mock_extract_text.return_value = {
                "success": True,
                "extracted_text": "Test text",
                "text_length": 100,
                "word_count": 20,
                "error": None
            }
            
            with patch('agents.workflow.language_detector_agent') as mock_lang_agent:
                mock_lang_agent.run.return_value = "English"
                
                with patch('agents.workflow.field_mapper_agent') as mock_field_agent:
                    mock_field_agent.run.return_value = '{"policy_number": "12345"}'
                    
                    with patch('agents.workflow.validation_agent') as mock_validation_agent:
                        mock_validation_agent.run.return_value = '{"is_valid": true}'
                        
                        with patch('agents.workflow.sanity_agent') as mock_sanity_agent:
                            mock_sanity_agent.run.return_value = '{"is_sane": true}'
                            
                            with patch('agents.workflow.response_agent') as mock_response_agent:
                                mock_response_agent.run.return_value = '{"status": "success"}'
                                
                                # Execute workflow
                                result = self.workflow.process_pdf_content(b"test pdf", "test query")
                                
                                # Verify vector memory was called for each step
                                self.assertTrue(mock_vector_memory.add_processing_memory.called)
                                
                                # Check that workflow_start was recorded
                                call_args_list = mock_vector_memory.add_processing_memory.call_args_list
                                workflow_start_calls = [call for call in call_args_list 
                                                      if call[1]['step'] == 'workflow_start']
                                self.assertEqual(len(workflow_start_calls), 1)

if __name__ == '__main__':
    unittest.main()
