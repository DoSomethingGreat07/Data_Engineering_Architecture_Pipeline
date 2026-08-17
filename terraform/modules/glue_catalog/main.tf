resource "aws_glue_catalog_database" "this" {
  name         = var.database_name
  description  = var.description
  location_uri = null
  parameters = {
    classification = "delta"
  }

  tags = var.tags
}

