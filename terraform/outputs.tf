# Terraform Outputs

# SNS Topic ARNs
output "transaction_processing_topic_arn" {
  description = "ARN of the main Transaction Processing SNS topic (FIFO)"
  value       = aws_sns_topic.transaction_processing.arn
}

output "subscription_control_topic_arn" {
  description = "ARN of the Subscription Control SNS topic"
  value       = aws_sns_topic.subscription_control.arn
}

# SQS Queue URLs
output "bank_account_setup_queue_url" {
  description = "URL of the Bank Account Setup SQS queue"
  value       = aws_sqs_queue.bank_account_setup.url
}

output "payment_processing_queue_url" {
  description = "URL of the Payment Processing SQS queue"
  value       = aws_sqs_queue.payment_processing.url
}

# Lambda Function ARNs
output "bank_account_lambda_arn" {
  description = "ARN of the Bank Account Setup Lambda function"
  value       = aws_lambda_function.bank_account_setup.arn
}

output "payment_lambda_arn" {
  description = "ARN of the Payment Processing Lambda function"
  value       = aws_lambda_function.payment_processing.arn
}

# Lambda Function Names
output "bank_account_lambda_name" {
  description = "Name of the Bank Account Setup Lambda function"
  value       = aws_lambda_function.bank_account_setup.function_name
}

output "payment_lambda_name" {
  description = "Name of the Payment Processing Lambda function"
  value       = aws_lambda_function.payment_processing.function_name
}

# Note: Dead Letter Queues removed as per requirements

# Event Source Mapping IDs
output "bank_account_event_source_mapping_id" {
  description = "ID of the Bank Account SQS event source mapping"
  value       = aws_lambda_event_source_mapping.bank_account_sqs_trigger.uuid
}

output "payment_event_source_mapping_id" {
  description = "ID of the Payment SQS event source mapping"
  value       = aws_lambda_event_source_mapping.payment_sqs_trigger.uuid
}

# Summary output for easy reference
output "system_summary" {
  description = "Summary of the deployed system"
  value = {
    region = var.aws_region
    environment = var.environment
    
    sns_topics = {
      transaction_processing = aws_sns_topic.transaction_processing.arn
      subscription_control = aws_sns_topic.subscription_control.arn
    }
    
    sqs_queues = {
      bank_account_setup = aws_sqs_queue.bank_account_setup.url
      payment_processing = aws_sqs_queue.payment_processing.url
    }
    
    lambda_functions = {
      bank_account_setup = aws_lambda_function.bank_account_setup.function_name
      payment_processing = aws_lambda_function.payment_processing.function_name
    }
  }
}