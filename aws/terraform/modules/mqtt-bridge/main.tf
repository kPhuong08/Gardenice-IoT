# ============================================
# MQTT Bridge Module - HiveMQ Webhook Handler
# ============================================

# IAM Role for Lambda
resource "aws_iam_role" "hivemq_processor" {
  name = "${var.lambda_function_name}-role"

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

  tags = var.tags
}

# IAM Policy for S3 Write Access
resource "aws_iam_role_policy" "s3_write_access" {
  name = "s3-write-access"
  role = aws_iam_role.hivemq_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${var.plant_data_bucket_arn}/raw_data/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.plant_data_bucket_arn
      }
    ]
  })
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.hivemq_processor.id

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
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Package Lambda Function
data "archive_file" "hivemq_processor" {
  type        = "zip"
  source_file = var.source_file
  output_path = "${path.module}/hivemq_processor.zip"
}

# Lambda Function
resource "aws_lambda_function" "hivemq_processor" {
  filename         = data.archive_file.hivemq_processor.output_path
  function_name    = var.lambda_function_name
  role            = aws_iam_role.hivemq_processor.arn
  handler         = var.lambda_handler
  source_code_hash = data.archive_file.hivemq_processor.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      PLANT_DATA_BUCKET = var.plant_data_bucket_name
    }
  }

  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "hivemq_processor" {
  name              = "/aws/lambda/${aws_lambda_function.hivemq_processor.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# ============================================
# API Gateway for MQTT Webhook
# ============================================

# REST API
resource "aws_api_gateway_rest_api" "mqtt_bridge" {
  name        = var.api_name
  description = "MQTT Bridge API for HiveMQ Webhook"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# Resource: /mqtt-ingest
resource "aws_api_gateway_resource" "mqtt_ingest" {
  rest_api_id = aws_api_gateway_rest_api.mqtt_bridge.id
  parent_id   = aws_api_gateway_rest_api.mqtt_bridge.root_resource_id
  path_part   = "mqtt-ingest"
}

# Method: POST /mqtt-ingest
resource "aws_api_gateway_method" "post_mqtt_ingest" {
  rest_api_id   = aws_api_gateway_rest_api.mqtt_bridge.id
  resource_id   = aws_api_gateway_resource.mqtt_ingest.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = true
}

# Lambda Integration
resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.mqtt_bridge.id
  resource_id             = aws_api_gateway_resource.mqtt_ingest.id
  http_method             = aws_api_gateway_method.post_mqtt_ingest.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.hivemq_processor.invoke_arn
}

# Lambda Permission
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hivemq_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.mqtt_bridge.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "mqtt_bridge" {
  rest_api_id = aws_api_gateway_rest_api.mqtt_bridge.id

  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]

  lifecycle {
    create_before_destroy = true
  }

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.mqtt_ingest.id,
      aws_api_gateway_method.post_mqtt_ingest.id,
      aws_api_gateway_integration.lambda_integration.id,
    ]))
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "mqtt_bridge" {
  deployment_id = aws_api_gateway_deployment.mqtt_bridge.id
  rest_api_id   = aws_api_gateway_rest_api.mqtt_bridge.id
  stage_name    = var.stage_name

  tags = var.tags
}

# ============================================
# API Key & Usage Plan
# ============================================

# API Key
resource "aws_api_gateway_api_key" "hivemq_key" {
  name    = var.api_key_name
  enabled = true

  tags = var.tags
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "mqtt_bridge" {
  name        = "${var.api_name}-usage-plan"
  description = "Usage plan for MQTT Bridge API"

  api_stages {
    api_id = aws_api_gateway_rest_api.mqtt_bridge.id
    stage  = aws_api_gateway_stage.mqtt_bridge.stage_name
  }

  throttle_settings {
    rate_limit  = var.rate_limit
    burst_limit = var.burst_limit
  }

  quota_settings {
    limit  = 1000000
    period = "MONTH"
  }

  tags = var.tags
}

# Associate API Key with Usage Plan
resource "aws_api_gateway_usage_plan_key" "mqtt_bridge" {
  key_id        = aws_api_gateway_api_key.hivemq_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.mqtt_bridge.id
}
