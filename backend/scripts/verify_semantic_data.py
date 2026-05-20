import sys
import os
import asyncio
from app.db.base import Base # Force model registration
from app.domains.fdv.models.fdv import BuildingComponent
from app.domains.fdv.schemas.fdv import BuildingComponent as BuildingComponentSchema

print("Successfully imported Models and Schemas.")

# Verify fields exist on SA Model
assert hasattr(BuildingComponent, 'parent_id'), "Missing parent_id on Model"
assert hasattr(BuildingComponent, 'brick_class'), "Missing brick_class on Model"
assert hasattr(BuildingComponent, 'system_code'), "Missing system_code on Model"

print("Model fields verified.")

# Verify fields exist on Pydantic Schema
fields = BuildingComponentSchema.model_fields
assert 'parent_id' in fields, "Missing parent_id on Schema"
assert 'brick_class' in fields, "Missing brick_class on Schema"
assert 'system_code' in fields, "Missing system_code on Schema"

print("Schema fields verified.")
print("Semantic Data Implementation Verified!")
