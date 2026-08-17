locals {
  subnet_map = {
    for index, cidr in var.private_subnet_cidrs :
    index => {
      cidr = cidr
      az   = var.availability_zones[index]
    }
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = merge(var.tags, { Name = "${var.project_name}-${var.environment}-vpc" })
}

resource "aws_subnet" "private" {
  for_each = local.subnet_map

  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = false

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-private-${each.value.az}"
      Tier = "private"
    }
  )
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.project_name}-${var.environment}-private-rt" })
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "platform" {
  name        = "${var.project_name}-${var.environment}-platform-sg"
  description = "Security group for private platform workloads."
  vpc_id      = aws_vpc.this.id

  egress {
    description = "Allow outbound within VPC and to AWS endpoints."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-platform-sg" })
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
  tags              = merge(var.tags, { Name = "${var.project_name}-${var.environment}-s3-endpoint" })
}

resource "aws_vpc_endpoint" "kinesis" {
  count = var.enable_kinesis_interface_endpoint ? 1 : 0

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.kinesis-streams"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = values(aws_subnet.private)[*].id
  security_group_ids  = [aws_security_group.platform.id]
  private_dns_enabled = true
  tags                = merge(var.tags, { Name = "${var.project_name}-${var.environment}-kinesis-endpoint" })
}

data "aws_region" "current" {}

