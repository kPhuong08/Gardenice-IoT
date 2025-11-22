output "api_id" {
  description = "MQTT Bridge API Gateway ID"
  value       = aws_api_gateway_rest_api.mqtt_bridge.id
}

output "api_endpoint" {
  description = "MQTT Bridge API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.mqtt_bridge.invoke_url}/mqtt-ingest"
}

output "api_key_id" {
  description = "API Gateway API Key ID"
  value       = aws_api_gateway_api_key.hivemq_key.id
}

output "api_key_value" {
  description = "API Gateway API Key value (sensitive)"
  value       = aws_api_gateway_api_key.hivemq_key.value
  sensitive   = true
}

output "lambda_function_name" {
  description = "HiveMQ Processor Lambda function name"
  value       = aws_lambda_function.hivemq_processor.function_name
}

output "lambda_function_arn" {
  description = "HiveMQ Processor Lambda function ARN"
  value       = aws_lambda_function.hivemq_processor.arn
}

output "usage_plan_id" {
  description = "API Gateway usage plan ID"
  value       = aws_api_gateway_usage_plan.mqtt_bridge.id
}
