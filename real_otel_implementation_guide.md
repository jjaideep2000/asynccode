# Real OpenTelemetry Implementation for Lambda, SNS, and SQS

## 🎯 Overview
This guide shows how to implement true OpenTelemetry observability across AWS Lambda, SNS, and SQS with proper distributed tracing, context propagation, and vendor-neutral telemetry.

## 🏗️ Architecture Components

### 1. OpenTelemetry Collector (ADOT)
- AWS Distro for OpenTelemetry (ADOT) Lambda Layer
- OTLP exporters for traces, metrics, and logs
- Context propagation across service boundaries

### 2. Instrumentation Libraries
- Auto-instrumentation for boto3 (AWS SDK)
- Manual instrumentation for business logic
- Context injection/extraction for SNS/SQS

### 3. Backend Systems
- AWS X-Ray (native AWS)
- Jaeger (open source)
- Grafana + Tempo + Prometheus
- Datadog, New Relic, etc.

## 📦 Required Dependencies

```python
# requirements.txt for Lambda functions
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation==0.42b0
opentelemetry-instrumentation-boto3sqs==0.42b0
opentelemetry-instrumentation-botocore==0.42b0
opentelemetry-instrumentation-aws-lambda==0.42b0
opentelemetry-exporter-otlp==1.21.0
opentelemetry-exporter-jaeger==1.21.0
opentelemetry-propagator-aws-xray==1.0.1
opentelemetry-propagator-b3==1.21.0
```

## 🔧 Implementation Steps

### Step 1: Lambda Layer Setup

```yaml
# terraform/lambda_layer.tf
resource "aws_lambda_layer_version" "otel_layer" {
  filename         = "otel-layer.zip"
  layer_name       = "opentelemetry-python"
  source_code_hash = filebase64sha256("otel-layer.zip")
  
  compatible_runtimes = ["python3.11"]
  description        = "OpenTelemetry Python instrumentation"
}

# Use AWS ADOT Layer (recommended)
resource "aws_lambda_function" "payment_processor" {
  layers = [
    "arn:aws:lambda:us-east-2:901920570463:layer:aws-otel-python-amd64-ver-1-20-0:1"
  ]
  
  environment {
    variables = {
      AWS_LAMBDA_EXEC_WRAPPER = "/opt/otel-instrument"
      OTEL_PROPAGATORS = "tracecontext,baggage,xray"
      OTEL_PYTHON_DISABLED_INSTRUMENTATIONS = "urllib3"
    }
  }
}
```

### Step 2: True OpenTelemetry Configuration

```python
# src/shared/real_otel_config.py
"""
Real OpenTelemetry Configuration
Proper OTEL setup with multiple exporters and auto-instrumentation
"""

import os
from opentelemetry import trace, metrics, baggage
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

# Exporters
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Propagators
from opentelemetry.propagators.aws import AwsXRayPropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagate import set_global_textmap

# Auto-instrumentation
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor
from opentelemetry.instrumentation.aws_lambda import AwsLambdaInstrumentor

class RealOTelConfig:
    """Real OpenTelemetry configuration with proper setup"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.setup_otel()
    
    def setup_otel(self):
        """Setup OpenTelemetry with proper exporters and instrumentation"""
        
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "dev"),
            "cloud.provider": "aws",
            "cloud.platform": "aws_lambda",
            "faas.name": os.getenv("AWS_LAMBDA_FUNCTION_NAME", self.service_name),
            "aws.region": os.getenv("AWS_REGION", "us-east-2")
        })
        
        # Setup tracing with multiple exporters
        trace_provider = TracerProvider(resource=resource)
        
        # OTLP Exporter (for Jaeger, Grafana, etc.)
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:14250"),
            insecure=True
        )
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Jaeger Exporter (direct)
        if os.getenv("JAEGER_ENDPOINT"):
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
                agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
            )
            trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        trace.set_tracer_provider(trace_provider)
        
        # Setup metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", 
                                 "http://prometheus:9090/api/v1/otlp/v1/metrics")
            ),
            export_interval_millis=30000
        )
        
        metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(metrics_provider)
        
        # Setup propagators for context propagation
        set_global_textmap(
            AwsXRayPropagator() | B3MultiFormat()
        )
        
        # Auto-instrument AWS services
        BotocoreInstrumentor().instrument()
        Boto3SQSInstrumentor().instrument()
        AwsLambdaInstrumentor().instrument()
        
        self.tracer = trace.get_tracer(self.service_name)
        self.meter = metrics.get_meter(self.service_name)

# Global instance
otel_config = None

def get_otel_config(service_name: str = None) -> RealOTelConfig:
    global otel_config
    if otel_config is None:
        service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "utility-service")
        otel_config = RealOTelConfig(service_name)
    return otel_config
```

### Step 3: SNS Context Propagation

```python
# src/shared/sns_instrumentation.py
"""
SNS Instrumentation with Context Propagation
Inject trace context into SNS messages for distributed tracing
"""

import json
import boto3
from typing import Dict, Any
from opentelemetry import trace, propagate
from opentelemetry.trace import Status, StatusCode

class InstrumentedSNSClient:
    """SNS client with OpenTelemetry instrumentation"""
    
    def __init__(self):
        self.sns_client = boto3.client('sns')
        self.tracer = trace.get_tracer(__name__)
    
    def publish_with_tracing(self, topic_arn: str, message: Dict[str, Any], 
                           message_group_id: str = None, 
                           message_deduplication_id: str = None) -> str:
        """Publish SNS message with trace context injection"""
        
        with self.tracer.start_as_current_span("sns.publish") as span:
            try:
                # Set span attributes
                span.set_attributes({
                    "messaging.system": "aws_sns",
                    "messaging.destination": topic_arn.split(':')[-1],
                    "messaging.destination_kind": "topic",
                    "messaging.operation": "publish",
                    "aws.sns.topic_arn": topic_arn
                })
                
                # Inject trace context into message attributes
                carrier = {}
                propagate.inject(carrier)
                
                message_attributes = {
                    'customer_id': {
                        'DataType': 'String',
                        'StringValue': message.get('customer_id', 'unknown')
                    }
                }
                
                # Add trace context to message attributes
                for key, value in carrier.items():
                    message_attributes[f'otel_{key}'] = {
                        'DataType': 'String',
                        'StringValue': value
                    }
                
                # Publish message
                publish_args = {
                    'TopicArn': topic_arn,
                    'Message': json.dumps(message),
                    'MessageAttributes': message_attributes
                }
                
                if message_group_id:
                    publish_args['MessageGroupId'] = message_group_id
                if message_deduplication_id:
                    publish_args['MessageDeduplicationId'] = message_deduplication_id
                
                response = self.sns_client.publish(**publish_args)
                
                # Add response attributes
                span.set_attributes({
                    "messaging.message_id": response['MessageId'],
                    "aws.sns.message_id": response['MessageId']
                })
                
                span.set_status(Status(StatusCode.OK))
                return response['MessageId']
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

# Usage
sns_client = InstrumentedSNSClient()
message_id = sns_client.publish_with_tracing(
    topic_arn="arn:aws:sns:us-east-2:123456789:my-topic",
    message={"customer_id": "cust-123", "amount": 100.00},
    message_group_id="cust-123"
)
```

### Step 4: SQS Context Extraction

```python
# src/shared/sqs_instrumentation.py
"""
SQS Instrumentation with Context Extraction
Extract trace context from SQS messages for distributed tracing
"""

import json
from typing import Dict, Any
from opentelemetry import trace, propagate, context
from opentelemetry.trace import Status, StatusCode

class SQSMessageProcessor:
    """Process SQS messages with OpenTelemetry context extraction"""
    
    def __init__(self, service_name: str):
        self.tracer = trace.get_tracer(service_name)
    
    def process_message_with_tracing(self, sqs_record: Dict[str, Any], 
                                   processor_func: callable) -> Any:
        """Process SQS message with trace context extraction"""
        
        # Extract message details
        message_body = json.loads(sqs_record['body'])
        message_attributes = sqs_record.get('messageAttributes', {})
        
        # Extract trace context from message attributes
        carrier = {}
        for key, attr in message_attributes.items():
            if key.startswith('otel_'):
                otel_key = key[5:]  # Remove 'otel_' prefix
                carrier[otel_key] = attr['stringValue']
        
        # Extract context and set as current
        extracted_context = propagate.extract(carrier)
        
        with context.use_context(extracted_context):
            with self.tracer.start_as_current_span("sqs.process") as span:
                try:
                    # Set span attributes
                    span.set_attributes({
                        "messaging.system": "aws_sqs",
                        "messaging.source": self.extract_queue_name(sqs_record),
                        "messaging.operation": "process",
                        "messaging.message_id": sqs_record.get('messageId'),
                        "aws.sqs.message_id": sqs_record.get('messageId'),
                        "aws.sqs.receipt_handle": sqs_record.get('receiptHandle', '')[:20]
                    })
                    
                    # Add customer context
                    customer_id = message_body.get('customer_id', 'unknown')
                    span.set_attribute("customer.id", customer_id)
                    
                    # Process the message
                    result = processor_func(message_body, sqs_record)
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
    
    def extract_queue_name(self, sqs_record: Dict[str, Any]) -> str:
        """Extract queue name from SQS record"""
        event_source_arn = sqs_record.get('eventSourceARN', '')
        return event_source_arn.split(':')[-1] if event_source_arn else 'unknown'

# Usage in Lambda handler
def lambda_handler(event, context):
    processor = SQSMessageProcessor("payment-service")
    
    for record in event.get('Records', []):
        if record.get('eventSource') == 'aws:sqs':
            processor.process_message_with_tracing(
                record, 
                process_payment_message
            )
```

### Step 5: Lambda Handler with Full Instrumentation

```python
# src/lambdas/payment/real_otel_handler.py
"""
Payment Lambda with Real OpenTelemetry Instrumentation
"""

import json
import time
from typing import Dict, Any
from opentelemetry import trace, metrics, baggage
from opentelemetry.trace import Status, StatusCode

from real_otel_config import get_otel_config
from sqs_instrumentation import SQSMessageProcessor

# Initialize OpenTelemetry
otel = get_otel_config("payment-processing")
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create metrics
payment_counter = meter.create_counter(
    "payments_processed_total",
    description="Total number of payments processed"
)

payment_duration = meter.create_histogram(
    "payment_processing_duration_seconds",
    description="Payment processing duration"
)

def lambda_handler(event, context):
    """Lambda handler with full OpenTelemetry instrumentation"""
    
    with tracer.start_as_current_span("lambda.handler") as span:
        span.set_attributes({
            "faas.execution": context.aws_request_id,
            "faas.id": context.function_name,
            "cloud.account.id": context.invoked_function_arn.split(':')[4]
        })
        
        processor = SQSMessageProcessor("payment-processing")
        results = []
        
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:sqs':
                result = processor.process_message_with_tracing(
                    record, 
                    process_payment_with_tracing
                )
                results.append(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'processed': len(results)})
        }

def process_payment_with_tracing(message_body: Dict[str, Any], 
                               sqs_record: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment with detailed tracing"""
    
    with tracer.start_as_current_span("payment.process") as span:
        start_time = time.time()
        customer_id = message_body.get('customer_id', 'unknown')
        amount = message_body.get('amount', 0)
        
        try:
            # Set baggage for context propagation
            baggage.set_baggage("customer.id", customer_id)
            baggage.set_baggage("payment.amount", str(amount))
            
            # Set span attributes
            span.set_attributes({
                "payment.customer_id": customer_id,
                "payment.amount": amount,
                "payment.currency": message_body.get('currency', 'USD'),
                "payment.method": message_body.get('payment_method', 'unknown')
            })
            
            # Validate payment
            with tracer.start_as_current_span("payment.validate") as validate_span:
                validate_payment(message_body)
                validate_span.set_status(Status(StatusCode.OK))
            
            # Process payment with external service
            with tracer.start_as_current_span("payment.external_call") as ext_span:
                ext_span.set_attributes({
                    "http.method": "POST",
                    "http.url": "https://payment-gateway.example.com/process",
                    "service.name": "payment-gateway"
                })
                
                result = call_payment_gateway(message_body)
                
                ext_span.set_attributes({
                    "http.status_code": 200,
                    "payment.transaction_id": result.get('transaction_id')
                })
            
            # Record metrics
            duration = time.time() - start_time
            payment_counter.add(1, {"status": "success", "customer_id": customer_id})
            payment_duration.record(duration, {"status": "success"})
            
            span.set_status(Status(StatusCode.OK))
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            payment_counter.add(1, {"status": "error", "customer_id": customer_id})
            payment_duration.record(duration, {"status": "error"})
            
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

def validate_payment(payment_data: Dict[str, Any]):
    """Validate payment with tracing"""
    with tracer.start_as_current_span("payment.validate.fields") as span:
        required_fields = ['customer_id', 'amount', 'payment_method']
        missing = [f for f in required_fields if not payment_data.get(f)]
        
        if missing:
            span.set_attribute("validation.missing_fields", missing)
            raise ValueError(f"Missing fields: {missing}")
        
        span.set_attribute("validation.fields_checked", len(required_fields))

def call_payment_gateway(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate payment gateway call with tracing"""
    with tracer.start_as_current_span("payment_gateway.process") as span:
        # Simulate processing
        time.sleep(0.1)
        
        transaction_id = f"txn_{int(time.time())}"
        span.set_attribute("payment.transaction_id", transaction_id)
        
        return {
            'transaction_id': transaction_id,
            'status': 'completed',
            'amount': payment_data['amount']
        }
```

### Step 6: Infrastructure Setup

```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14250:14250"
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yml"]
    volumes:
      - ./otel-collector-config.yml:/etc/otel-collector-config.yml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP HTTP receiver
    depends_on:
      - jaeger
      - prometheus
```

```yaml
# otel-collector-config.yml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

## 🎯 Key Benefits of Real OpenTelemetry

### 1. **True Distributed Tracing**
- Traces span across SNS → SQS → Lambda
- Context propagation maintains trace relationships
- End-to-end visibility of message flow

### 2. **Vendor Neutrality**
- Export to any OpenTelemetry-compatible backend
- Switch between Jaeger, Zipkin, Datadog, etc.
- No vendor lock-in

### 3. **Automatic Instrumentation**
- boto3/botocore auto-instrumented
- HTTP calls automatically traced
- Database queries traced (if using RDS)

### 4. **Rich Context**
- Baggage propagation for business context
- Correlation IDs across services
- Customer journey tracking

### 5. **Standardized Metrics**
- OpenTelemetry semantic conventions
- Consistent naming across services
- Industry-standard observability

## 🚀 Deployment Considerations

### Lambda Cold Starts
- ADOT layer adds ~200ms to cold starts
- Use provisioned concurrency for critical functions
- Consider sampling strategies

### Cost Implications
- Additional Lambda execution time
- Network egress for telemetry data
- Backend storage costs (Jaeger, Prometheus)

### Performance Impact
- ~5-10% overhead for instrumentation
- Batch processing reduces network calls
- Sampling reduces data volume

This is what **real OpenTelemetry** looks like - proper context propagation, vendor-neutral exporters, and true distributed tracing across your entire AWS infrastructure!