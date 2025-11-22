output "function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.function.function_name
}

output "function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.function.arn
}

output "invoke_arn" {
  description = "Lambda function invoke ARN"
  value       = aws_lambda_function.function.invoke_arn
}

output "role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_execution.arn
}
