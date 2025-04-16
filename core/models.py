import uuid
from django.db import models

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class Role(BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True)
    
class Permission(BaseModel):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True)
