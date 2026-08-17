output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs."
  value       = values(aws_subnet.private)[*].id
}

output "security_group_id" {
  description = "Platform security group ID."
  value       = aws_security_group.platform.id
}

