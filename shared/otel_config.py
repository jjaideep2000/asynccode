"""
OpenTelemetry configuration for utility customer system
AWS Lambda optimized configuration with CloudWatch integration
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    import boto3
    OTEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenTelemetry not available: {e}")
    OTEL_AVAILABLE = False

class OTelConfig:
    """OpenTelemetry configuration and setup for AWS Lambda"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = None
        self.meter = None
        self.otel_enabled = OTEL_AVAILABLE
        self._setup_otel()
    
    def _setup_otel(self):
        """Setup OpenTelemetry tracing and metrics"""
        
        if not self.otel_enabled:
            logger.info("OpenTelemetry not available, using no-op implementations")
            self.tracer = NoOpTracer()
            self.meter = NoOpMeter()
            return
        
        try:
            # Initialize CloudWatch client for custom metrics
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=os.getenv("AWS_REGION", "us-east-2"))
            self.metrics_namespace = "OTEL/UtilityCustomer/Enhanced"
            
            # Create resource with service information
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": "1.0.0",
                "deployment.environment": os.getenv("ENVIRONMENT", "dev"),
                "cloud.provider": "aws",
                "cloud.platform": "aws_lambda",
                "faas.name": os.getenv("AWS_LAMBDA_FUNCTION_NAME", self.service_name)
            })
            
            # Setup tracing - use existing provider if available (from OTEL layer)
            try:
                self.tracer = trace.get_tracer(self.service_name)
                logger.info(f"Using existing tracer for {self.service_name}")
            except Exception:
                # Fallback: create our own tracer provider
                tracer_provider = TracerProvider(resource=resource)
                trace.set_tracer_provider(tracer_provider)
                self.tracer = trace.get_tracer(self.service_name)
                logger.info(f"Created new tracer for {self.service_name}")
            
            # Setup metrics - use simple approach with boto3 CloudWatch client
            try:
                # Try to use existing meter provider first
                self.meter = metrics.get_meter(self.service_name)
                logger.info(f"Using existing meter for {self.service_name}")
            except Exception:
                # Create simple meter provider
                meter_provider = MeterProvider(resource=resource)
                metrics.set_meter_provider(meter_provider)
                self.meter = metrics.get_meter(self.service_name)
                logger.info(f"Created meter for {self.service_name}")
            
            logger.info(f"OpenTelemetry initialized successfully for service: {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            # Fallback to no-op implementations
            self.tracer = NoOpTracer()
            self.meter = NoOpMeter()
    
    def create_counter(self, name: str, description: str = "", unit: str = ""):
        """Create a counter metric"""
        if not self.otel_enabled:
            return NoOpCounter()
        
        try:
            # Return CloudWatch-enabled counter
            return CloudWatchCounter(name, self)
        except Exception as e:
            logger.error(f"Failed to create counter {name}: {e}")
            return NoOpCounter()
    
    def create_histogram(self, name: str, description: str = "", unit: str = ""):
        """Create a histogram metric"""
        if not self.otel_enabled:
            return NoOpHistogram()
        
        try:
            # Return CloudWatch-enabled histogram
            return CloudWatchHistogram(name, self)
        except Exception as e:
            logger.error(f"Failed to create histogram {name}: {e}")
            return NoOpHistogram()
    
    def create_gauge(self, name: str, description: str = "", unit: str = ""):
        """Create a gauge metric"""
        if not self.otel_enabled:
            return NoOpCounter()
        
        try:
            # Return CloudWatch-enabled counter for gauge
            return CloudWatchCounter(name, self)
        except Exception as e:
            logger.error(f"Failed to create gauge {name}: {e}")
            return NoOpCounter()
    
    def start_span(self, name: str, attributes: Dict[str, Any] = None):
        """Start a new span"""
        if not self.otel_enabled:
            return NoOpSpan()
        
        try:
            return self.tracer.start_span(name, attributes=attributes or {})
        except Exception as e:
            logger.error(f"Failed to start span {name}: {e}")
            return NoOpSpan()
    
    def add_span_attributes(self, span, attributes: Dict[str, Any]):
        """Add attributes to a span"""
        if not self.otel_enabled or isinstance(span, NoOpSpan):
            return
        
        try:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        except Exception as e:
            logger.error(f"Failed to add span attributes: {e}")
    
    def record_exception(self, span, exception: Exception):
        """Record an exception in a span"""
        if not self.otel_enabled or isinstance(span, NoOpSpan):
            return
        
        try:
            span.record_exception(exception)
            if OTEL_AVAILABLE:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
        except Exception as e:
            logger.error(f"Failed to record exception: {e}")
    
    def put_metric(self, metric_name: str, value: float, unit: str = "Count", dimensions: Dict[str, str] = None):
        """Put a custom metric to CloudWatch"""
        if not self.otel_enabled:
            return
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch_client.put_metric_data(
                Namespace=self.metrics_namespace,
                MetricData=[metric_data]
            )
            
        except Exception as e:
            logger.error(f"Failed to put metric {metric_name}: {e}")


# No-op implementations for when OpenTelemetry is not available
class NoOpSpan:
    """No-op span implementation"""
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_attribute(self, key, value):
        pass
    
    def record_exception(self, exception):
        pass
    
    def set_status(self, status):
        pass


class NoOpTracer:
    """No-op tracer implementation"""
    def start_span(self, name, attributes=None):
        return NoOpSpan()


class CloudWatchCounter:
    """CloudWatch counter implementation"""
    def __init__(self, name: str, otel_config: 'OTelConfig'):
        self.name = name
        self.otel_config = otel_config
    
    def add(self, amount, attributes=None):
        dimensions = attributes or {}
        self.otel_config.put_metric(self.name, amount, "Count", dimensions)


class CloudWatchHistogram:
    """CloudWatch histogram implementation"""
    def __init__(self, name: str, otel_config: 'OTelConfig'):
        self.name = name
        self.otel_config = otel_config
    
    def record(self, amount, attributes=None):
        dimensions = attributes or {}
        self.otel_config.put_metric(self.name, amount, "Seconds", dimensions)


class NoOpCounter:
    """No-op counter implementation"""
    def add(self, amount, attributes=None):
        pass


class NoOpHistogram:
    """No-op histogram implementation"""
    def record(self, amount, attributes=None):
        pass


class NoOpMeter:
    """No-op meter implementation"""
    def create_counter(self, name, description="", unit=""):
        return NoOpCounter()
    
    def create_histogram(self, name, description="", unit=""):
        return NoOpHistogram()
    
    def create_up_down_counter(self, name, description="", unit=""):
        return NoOpCounter()

# Global OTEL instance
_otel_instance = None

def get_otel_config(service_name: str = None) -> OTelConfig:
    """Get or create OTEL configuration instance"""
    global _otel_instance
    
    if _otel_instance is None:
        if service_name is None:
            service_name = os.getenv("OTEL_SERVICE_NAME", "utility-customer-service")
        _otel_instance = OTelConfig(service_name)
    
    return _otel_instance

def create_metrics_for_service(service_name: str):
    """Create standard metrics for a service"""
    otel = get_otel_config(service_name)
    
    metrics = {
        'messages_processed': otel.create_counter(
            name="messages_processed_total",
            description="Total number of messages processed",
            unit="1"
        ),
        'processing_duration': otel.create_histogram(
            name="processing_duration_seconds",
            description="Time taken to process messages",
            unit="s"
        ),
        'errors_total': otel.create_counter(
            name="errors_total",
            description="Total number of errors",
            unit="1"
        ),
        'subscription_status': otel.create_gauge(
            name="subscription_status",
            description="Current subscription status (1=active, 0=inactive)",
            unit="1"
        ),
        'queue_depth': otel.create_gauge(
            name="queue_depth",
            description="Current queue depth",
            unit="1"
        )
    }
    
    return metrics