"""
OpenTelemetry Configuration for Payment System
Provides comprehensive observability for customer message tracking
Simplified version using AWS CloudWatch and X-Ray
"""

import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Simplified observability without complex dependencies
# This version focuses on structured logging and basic tracing

class PaymentSystemObservability:
    """
    Simplified observability for payment system
    Focuses on structured logging and customer journey tracking
    """
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.current_trace_id = None
        self.current_span_id = None
        
    def generate_trace_id(self) -> str:
        """Generate a simple trace ID for customer journey tracking"""
        return f"trace-{int(time.time() * 1000000)}"
    
    def generate_span_id(self) -> str:
        """Generate a simple span ID"""
        return f"span-{int(time.time() * 1000000)}"
    
    def start_customer_trace(self, operation: str, customer_id: str, 
                           message_attributes: Optional[Dict] = None) -> Dict[str, str]:
        """
        Start a customer trace for tracking operations
        
        Args:
            operation: The operation being performed (e.g., 'bank_account_setup')
            customer_id: Unique customer identifier
            message_attributes: Additional message context
        
        Returns:
            Dictionary with trace and span information
        """
        self.current_trace_id = self.generate_trace_id()
        self.current_span_id = self.generate_span_id()
        
        trace_info = {
            "trace_id": self.current_trace_id,
            "span_id": self.current_span_id,
            "operation": operation,
            "customer_id": customer_id,
            "service": self.service_name,
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Add message attributes if provided
        if message_attributes:
            trace_info["message_attributes"] = message_attributes
        
        # Log trace start
        self.record_customer_event(
            event_type="trace_started",
            customer_id=customer_id,
            status="processing",
            details={
                "trace_id": self.current_trace_id,
                "span_id": self.current_span_id,
                "operation": operation
            }
        )
        
        return trace_info
    
    def record_customer_event(self, event_type: str, customer_id: str, 
                            status: str, details: Optional[Dict] = None):
        """
        Record a customer event with structured logging
        
        Args:
            event_type: Type of event (e.g., 'message_received', 'validation_started')
            customer_id: Customer identifier
            status: Event status (success, error, processing)
            details: Additional event details
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "customer_id": customer_id,
            "status": status,
            "service": self.service_name
        }
        
        if details:
            event_data.update(details)
        
        # Log structured event (will be picked up by CloudWatch)
        print(f"CUSTOMER_EVENT: {json.dumps(event_data)}")
        
        # Add trace context if available
        if self.current_trace_id:
            event_data["trace_id"] = self.current_trace_id
            event_data["span_id"] = self.current_span_id
        
        event_data["environment"] = self.environment
    
    def record_processing_duration(self, operation: str, duration_ms: float, 
                                 customer_id: str, status: str):
        """
        Record processing duration metrics
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            customer_id: Customer identifier
            status: Processing status
        """
        duration_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric_type": "processing_duration",
            "operation": operation,
            "duration_ms": duration_ms,
            "customer_id": customer_id,
            "status": status,
            "service": self.service_name,
            "trace_id": self.current_trace_id,
            "environment": self.environment
        }
        
        # Log structured metric (CloudWatch will pick this up)
        print(f"CUSTOMER_METRIC: {json.dumps(duration_data)}")
    
    def record_error(self, error_type: str, customer_id: str, 
                   error_message: str, additional_context: Optional[Dict] = None):
        """
        Record error events with proper categorization
        
        Args:
            error_type: Type of error (validation, external_service, system)
            customer_id: Customer identifier
            error_message: Error description
            additional_context: Additional error context
        """
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "customer_id": customer_id,
            "error_message": error_message,
            "service": self.service_name,
            "trace_id": self.current_trace_id,
            "span_id": self.current_span_id,
            "environment": self.environment
        }
        
        if additional_context:
            error_data.update(additional_context)
        
        # Log structured error (CloudWatch will pick this up)
        print(f"CUSTOMER_ERROR: {json.dumps(error_data)}")
    
    def end_customer_trace(self, customer_id: str, status: str, 
                         duration_ms: Optional[float] = None):
        """
        End the current customer trace
        
        Args:
            customer_id: Customer identifier
            status: Final status (success, error, timeout)
            duration_ms: Total processing duration
        """
        if self.current_trace_id:
            self.record_customer_event(
                event_type="trace_completed",
                customer_id=customer_id,
                status=status,
                details={
                    "trace_id": self.current_trace_id,
                    "span_id": self.current_span_id,
                    "duration_ms": duration_ms,
                    "end_time": datetime.utcnow().isoformat()
                }
            )

# Global observability instances for each service
bank_account_observability = None
payment_observability = None
error_handler_observability = None

def get_bank_account_observability() -> PaymentSystemObservability:
    """Get or create bank account observability instance"""
    global bank_account_observability
    if bank_account_observability is None:
        bank_account_observability = PaymentSystemObservability("bank-account-service")
    return bank_account_observability

def get_payment_observability() -> PaymentSystemObservability:
    """Get or create payment observability instance"""
    global payment_observability
    if payment_observability is None:
        payment_observability = PaymentSystemObservability("payment-service")
    return payment_observability

def get_error_handler_observability() -> PaymentSystemObservability:
    """Get or create error handler observability instance"""
    global error_handler_observability
    if error_handler_observability is None:
        error_handler_observability = PaymentSystemObservability("error-handler-service")
    return error_handler_observability