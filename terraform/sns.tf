# SNS Topics

# 1. Main Transaction Processing Topic (FIFO)
resource "aws_sns_topic" "transaction_processing" {
  name                        = "${local.name_prefix}-transaction-processing.fifo"
  fifo_topic                 = true
  content_based_deduplication = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-transaction-processing"
    Type = "transaction-processing"
  })
}

# 2. Subscription Control Topic (Standard)
resource "aws_sns_topic" "subscription_control" {
  name = "${local.name_prefix}-subscription-control"
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-subscription-control"
    Type = "subscription-control"
  })
}

# SNS Topic Policies
resource "aws_sns_topic_policy" "transaction_processing_policy" {
  arn = aws_sns_topic.transaction_processing.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "sns:Publish",
          "sns:Subscribe"
        ]
        Resource = aws_sns_topic.transaction_processing.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_sns_topic_policy" "subscription_control_policy" {
  arn = aws_sns_topic.subscription_control.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "sns:Publish",
          "sns:Subscribe"
        ]
        Resource = aws_sns_topic.subscription_control.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}