"""
Comprehensive integration tests for agent_personas package.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from agent_personas.exceptions import PersonaValidationError, PersonaNotFoundError
from agent_personas.validation import validate_persona_traits, validate_conversation_history
from agent_personas.security import sanitize_input, RateLimiter
from agent_personas.monitoring import PerformanceMonitor
from agent_personas.utils import deep_merge_dict, safe_json_loads


class TestFullIntegration:
    """Test full integration scenarios."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_persona_data = {
            "name": "Test Assistant",
            "traits": {
                "personality": {
                    "extroversion": 0.7,
                    "openness": 0.8,
                    "conscientiousness": 0.6,
                    "agreeableness": 0.8,
                    "neuroticism": 0.3
                },
                "communication_style": "friendly",
                "knowledge_areas": ["technology", "science", "general"]
            },
            "version": "1.0"
        }
    
    def test_persona_creation_workflow(self):
        """Test complete persona creation and validation workflow."""
        # Step 1: Validate persona name
        from agent_personas.validation import validate_persona_name
        
        assert validate_persona_name(self.test_persona_data["name"]) == True
        
        # Step 2: Validate traits
        assert validate_persona_traits(self.test_persona_data["traits"]) == True
        
        # Step 3: Sanitize input data
        from agent_personas.security import sanitize_input
        clean_name = sanitize_input(self.test_persona_data["name"])
        assert clean_name == "Test Assistant"
        
        # Step 4: Check trait compatibility
        from agent_personas.validation import validate_trait_compatibility
        assert validate_trait_compatibility(self.test_persona_data["traits"]) == True
    
    def test_conversation_flow_integration(self):
        """Test conversation processing with security and validation."""
        conversation = [
            {"role": "user", "content": "Hello there!", "timestamp": 1000.0},
            {"role": "assistant", "content": "Hello! How can I help you?", "timestamp": 1001.0},
            {"role": "user", "content": "Tell me about AI", "timestamp": 1002.0}
        ]
        
        # Validate conversation structure
        assert validate_conversation_history(conversation) == True
        
        # Sanitize each message
        for message in conversation:
            clean_content = sanitize_input(message["content"])
            assert len(clean_content) > 0
            assert clean_content == message["content"]  # Should be unchanged for clean input
    
    def test_security_validation_pipeline(self):
        """Test complete security validation pipeline."""
        # Test safe content
        safe_text = "Hello, how are you today?"
        clean_text = sanitize_input(safe_text)
        
        from agent_personas.security import validate_safe_content
        assert validate_safe_content(clean_text) == True
        
        # Test potentially unsafe content
        unsafe_text = "<script>alert('xss')</script>Hello"
        clean_text = sanitize_input(unsafe_text, remove_html=True)
        assert "<script>" not in clean_text
        assert validate_safe_content(clean_text) == True
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring with actual operations."""
        monitor = PerformanceMonitor()
        
        # Record some metrics
        monitor.record_metric("test_metric", 5.5)
        monitor.record_execution("test_function", 0.123)
        
        # Get statistics
        stats = monitor.get_stats("test_metric")
        assert stats["count"] == 1
        assert stats["avg"] == 5.5
        
        exec_stats = monitor.get_execution_stats()
        assert "test_function" in exec_stats
        assert exec_stats["test_function"]["total_calls"] == 1
    
    def test_rate_limiting_integration(self):
        """Test rate limiting in realistic scenarios."""
        limiter = RateLimiter(strategy='token_bucket', default_limit=5)
        
        user_id = "test_user"
        
        # Should allow first 5 requests
        for i in range(5):
            assert limiter.is_allowed(user_id) == True
        
        # Should deny 6th request
        assert limiter.is_allowed(user_id) == False
        
        # Check rate limit info
        info = limiter.get_info(user_id)
        assert info.remaining == 0
    
    def test_utility_functions_integration(self):
        """Test utility functions working together."""
        # Test deep merging configuration
        base_config = {
            "traits": {"personality": {"extroversion": 0.5}},
            "settings": {"debug": False}
        }
        
        override_config = {
            "traits": {"personality": {"openness": 0.8}},
            "settings": {"log_level": "INFO"}
        }
        
        merged = deep_merge_dict(base_config, override_config)
        
        assert merged["traits"]["personality"]["extroversion"] == 0.5
        assert merged["traits"]["personality"]["openness"] == 0.8
        assert merged["settings"]["debug"] == False
        assert merged["settings"]["log_level"] == "INFO"
        
        # Test safe JSON operations
        json_str = '{"test": "value"}'
        data = safe_json_loads(json_str)
        assert data["test"] == "value"
        
        # Test with invalid JSON
        invalid_json = '{"test": invalid}'
        data = safe_json_loads(invalid_json, default={"error": True})
        assert data["error"] == True
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test validation error propagation
        with pytest.raises(PersonaValidationError):
            validate_persona_traits({})  # Missing required fields
        
        # Test input sanitization with extreme cases
        very_long_text = "x" * 20000
        clean_text = sanitize_input(very_long_text, max_length=1000)
        assert len(clean_text) == 1000
        
        # Test rate limiter with invalid key
        limiter = RateLimiter()
        # Should not raise exception with any key
        assert isinstance(limiter.is_allowed("any_key"), bool)
    
    @patch('agent_personas.monitoring.psutil.virtual_memory')
    @patch('agent_personas.monitoring.psutil.cpu_percent')
    def test_system_monitoring_integration(self, mock_cpu, mock_memory):
        """Test system resource monitoring."""
        # Mock system metrics
        mock_memory.return_value = Mock(percent=45.5, available=8000000000, used=4000000000)
        mock_cpu.return_value = 25.3
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring(interval=0.1)
        
        # Let it collect some data
        import time
        time.sleep(0.2)
        
        monitor.stop_monitoring()
        
        # Check system stats
        system_stats = monitor.get_system_stats()
        
        # Memory stats should be available
        if 'memory' in system_stats:
            assert system_stats['memory']['current_percent'] > 0
            assert system_stats['memory']['available_mb'] > 0
    
    def test_logging_integration(self):
        """Test logging configuration and context."""
        from agent_personas.logging_config import setup_logging, ContextLogger
        
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            # Setup logging with file output
            logger = setup_logging(
                level="DEBUG",
                log_file=log_file,
                console_output=False
            )
            
            assert isinstance(logger, ContextLogger)
            
            # Test context logging
            logger.set_context(persona_id="test", operation="test")
            logger.info("Test message")
            logger.clear_context()
            
            # Check that log file was created and has content
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
                
        finally:
            # Cleanup
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_data_flow_integration(self):
        """Test complete data processing flow."""
        # Simulate incoming user data
        raw_data = {
            "user_message": "  Hello <b>world</b>!  ",
            "user_id": "user_123", 
            "context": {"session_id": "sess_456"}
        }
        
        # Step 1: Sanitize input
        clean_message = sanitize_input(
            raw_data["user_message"],
            remove_html=True,
            max_length=1000
        )
        assert clean_message == "Hello world!"
        
        # Step 2: Validate safe content
        from agent_personas.security import validate_safe_content
        assert validate_safe_content(clean_message) == True
        
        # Step 3: Apply rate limiting
        limiter = RateLimiter(default_limit=100)
        assert limiter.is_allowed(raw_data["user_id"]) == True
        
        # Step 4: Process with monitoring
        monitor = PerformanceMonitor()
        start_time = time.time()
        
        # Simulate processing
        import time
        time.sleep(0.01)  # Minimal delay
        
        execution_time = time.time() - start_time
        monitor.record_execution("process_message", execution_time)
        
        # Step 5: Validate results
        stats = monitor.get_execution_stats()
        assert "process_message" in stats
        assert stats["process_message"]["total_calls"] == 1
    
    def test_concurrent_operations(self):
        """Test thread-safe operations."""
        import threading
        import time
        
        limiter = RateLimiter(default_limit=10)
        monitor = PerformanceMonitor()
        results = []
        
        def worker_thread(thread_id):
            """Worker function for threading test."""
            # Test rate limiter thread safety
            allowed = limiter.is_allowed(f"user_{thread_id}")
            results.append(allowed)
            
            # Test performance monitor thread safety
            monitor.record_metric(f"thread_{thread_id}", thread_id)
            
            # Small delay to increase chance of race conditions
            time.sleep(0.001)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should have succeeded without errors
        assert len(results) == 5
        assert all(isinstance(result, bool) for result in results)
        
        # Check monitor collected data from all threads
        stats = monitor.get_stats()
        thread_metrics = [key for key in stats.keys() if key.startswith('thread_')]
        assert len(thread_metrics) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])