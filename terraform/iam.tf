# IAM Roles and Policies for Lambda Functions

# Bank Account Setup Lambda Role
resource "aws_iam_role" "bank_account_lambda_role" {
  name = "${local.name_prefix}-bank-account-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Payment Processing Lambda Role
resource "aws_iam_role" "payment_lambda_role" {
  name = "${local.name_prefix}-payment-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Basic Lambda execution policy
resource "aws_iam_policy" "lambda_basic_execution" {
  name        = "${local.name_prefix}-lambda-basic-execution"
  description = "Basic execution policy for Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# SQS and SNS access policy
resource "aws_iam_policy" "lambda_sqs_sns_policy" {
  name        = "${local.name_prefix}-lambda-sqs-sns-policy"
  description = "Policy for Lambda to access SQS and SNS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = [
          aws_sqs_queue.bank_account_setup.arn,
          aws_sqs_queue.payment_processing.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Subscribe",
          "sns:Unsubscribe",
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.transaction_processing.arn,
          aws_sns_topic.subscription_control.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:ListEventSourceMappings",
          "lambda:UpdateEventSourceMapping",
          "lambda:GetEventSourceMapping"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch metrics policy for OpenTelemetry
resource "aws_iam_policy" "lambda_cloudwatch_policy" {
  name        = "${local.name_prefix}-lambda-cloudwatch-policy"
  description = "Policy for Lambda to publish CloudWatch metrics"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:CreateLogGroup",
          "cloudwatch:CreateLogStream",
          "cloudwatch:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach policies to Bank Account Lambda role
resource "aws_iam_role_policy_attachment" "bank_account_basic_execution" {
  role       = aws_iam_role.bank_account_lambda_role.name
  policy_arn = aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy_attachment" "bank_account_sqs_sns" {
  role       = aws_iam_role.bank_account_lambda_role.name
  policy_arn = aws_iam_policy.lambda_sqs_sns_policy.arn
}

resource "aws_iam_role_policy_attachment" "bank_account_cloudwatch" {
  role       = aws_iam_role.bank_account_lambda_role.name
  policy_arn = aws_iam_policy.lambda_cloudwatch_policy.arn
}

# Attach policies to Payment Lambda role
resource "aws_iam_role_policy_attachment" "payment_basic_execution" {
  role       = aws_iam_role.payment_lambda_role.name
  policy_arn = aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy_attachment" "payment_sqs_sns" {
  role       = aws_iam_role.payment_lambda_role.name
  policy_arn = aws_iam_policy.lambda_sqs_sns_policy.arn
}

resource "aws_iam_role_policy_attachment" "payment_cloudwatch" {
  role       = aws_iam_role.payment_lambda_role.name
  policy_arn = aws_iam_policy.lambda_cloudwatch_policy.arn
}