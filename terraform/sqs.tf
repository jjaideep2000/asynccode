# SQS Queues (FIFO)

# 1. Bank Account Setup Queue (FIFO)
resource "aws_sqs_queue" "bank_account_setup" {
  name                        = "${local.name_prefix}-bank-account-setup.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 300
  message_retention_seconds   = 1209600  # 14 days
  max_message_size           = 262144   # 256 KB
  delay_seconds              = 0
  receive_wait_time_seconds  = 20       # Long polling

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-bank-account-setup"
    Type = "bank-account-setup"
  })
}

# 2. Payment Processing Queue (FIFO)
resource "aws_sqs_queue" "payment_processing" {
  name                        = "${local.name_prefix}-payment-processing.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 300
  message_retention_seconds   = 1209600  # 14 days
  max_message_size           = 262144   # 256 KB
  delay_seconds              = 0
  receive_wait_time_seconds  = 20       # Long polling

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-payment-processing"
    Type = "payment-processing"
  })
}

# SQS Queue Policies
resource "aws_sqs_queue_policy" "bank_account_setup_policy" {
  queue_url = aws_sqs_queue.bank_account_setup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.bank_account_setup.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.transaction_processing.arn
          }
        }
      }
    ]
  })
}

resource "aws_sqs_queue_policy" "payment_processing_policy" {
  queue_url = aws_sqs_queue.payment_processing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = "sqs:SendMessage"
        Resource = aws_sqs_queue.payment_processing.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.transaction_processing.arn
          }
        }
      }
    ]
  })
}

# SNS to SQS Subscriptions with Message Filtering
resource "aws_sns_topic_subscription" "bank_account_setup_subscription" {
  topic_arn = aws_sns_topic.transaction_processing.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.bank_account_setup.arn
  
  # Filter messages by transaction_type
  filter_policy = jsonencode({
    transaction_type = ["bank_account_setup"]
  })
}

resource "aws_sns_topic_subscription" "payment_processing_subscription" {
  topic_arn = aws_sns_topic.transaction_processing.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.payment_processing.arn
  
  # Filter messages by transaction_type
  filter_policy = jsonencode({
    transaction_type = ["payment"]
  })
}