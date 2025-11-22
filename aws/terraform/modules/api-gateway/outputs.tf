output "api_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.api.id
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.api.invoke_url}/plant"
}

output "api_execution_arn" {
  description = "API Gateway execution ARN"
  value       = aws_api_gateway_rest_api.api.execution_arn
}

output "stage_name" {
  description = "API Gateway stage name"
  value       = aws_api_gateway_stage.api.stage_name
}
