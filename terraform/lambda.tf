# Lambda Functions

# Bank Account Setup Lambda
resource "aws_lambda_function" "bank_account_setup" {
  filename         = "../deploy/bank-account-setup.zip"
  function_name    = "${local.name_prefix}-bank-account-setup"
  role            = aws_iam_role.bank_account_lambda_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      ENVIRONMENT                    = var.environment
      BANK_ACCOUNT_QUEUE_URL        = aws_sqs_queue.bank_account_setup.url
      SUBSCRIPTION_CONTROL_TOPIC_ARN = aws_sns_topic.subscription_control.arn
      TRANSACTION_TOPIC_ARN          = aws_sns_topic.transaction_processing.arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.bank_account_basic_execution,
    aws_iam_role_policy_attachment.bank_account_sqs_sns,
    aws_iam_role_policy_attachment.bank_account_cloudwatch,
  ]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-bank-account-setup"
    Type = "bank-account-lambda"
  })
}

# Payment Processing Lambda
resource "aws_lambda_function" "payment_processing" {
  filename         = "../deploy/payment-processing.zip"
  function_name    = "${local.name_prefix}-payment-processing"
  role            = aws_iam_role.payment_lambda_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      ENVIRONMENT                    = var.environment
      PAYMENT_QUEUE_URL             = aws_sqs_queue.payment_processing.url
      SUBSCRIPTION_CONTROL_TOPIC_ARN = aws_sns_topic.subscription_control.arn
      TRANSACTION_TOPIC_ARN          = aws_sns_topic.transaction_processing.arn
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.payment_basic_execution,
    aws_iam_role_policy_attachment.payment_sqs_sns,
    aws_iam_role_policy_attachment.payment_cloudwatch,
  ]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-payment-processing"
    Type = "payment-lambda"
  })
}

# Lambda Event Source Mappings (SQS triggers)
resource "aws_lambda_event_source_mapping" "bank_account_sqs_trigger" {
  event_source_arn = aws_sqs_queue.bank_account_setup.arn
  function_name    = aws_lambda_function.bank_account_setup.arn
  batch_size       = 10
  enabled          = true

  # FIFO queues don't support batching windows
  
  depends_on = [aws_lambda_function.bank_account_setup]
}

resource "aws_lambda_event_source_mapping" "payment_sqs_trigger" {
  event_source_arn = aws_sqs_queue.payment_processing.arn
  function_name    = aws_lambda_function.payment_processing.arn
  batch_size       = 10
  enabled          = true

  # FIFO queues don't support batching windows
  
  depends_on = [aws_lambda_function.payment_processing]
}

# SNS Subscriptions for Subscription Control
resource "aws_sns_topic_subscription" "bank_account_subscription_control" {
  topic_arn = aws_sns_topic.subscription_control.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.bank_account_setup.arn
}

resource "aws_sns_topic_subscription" "payment_subscription_control" {
  topic_arn = aws_sns_topic.subscription_control.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.payment_processing.arn
}

# Lambda permissions for SNS to invoke functions
resource "aws_lambda_permission" "bank_account_sns_permission" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bank_account_setup.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.subscription_control.arn
}

resource "aws_lambda_permission" "payment_sns_permission" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.payment_processing.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.subscription_control.arn
}