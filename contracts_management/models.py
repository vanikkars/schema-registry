from pydantic import BaseModel, Field
from typing import List


class ColumnDefinition(BaseModel):
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type (string, integer, number, date, timestamp, etc.)")
    nullable: bool = Field(default=True, description="Whether the column can contain null values")
    description: str = Field(default="", description="Column description")


class ContractMetadata(BaseModel):
    data_owner: str = Field(default="Data Team", description="Data owner name")
    data_owner_email: str = Field(default="data-team@company.com", description="Data owner email")
    data_steward: str = Field(default="Data Engineering", description="Data steward name")
    data_steward_email: str = Field(default="data-engineering@company.com", description="Data steward email")
    sla_uptime_percentage: float = Field(default=99.95, description="SLA uptime percentage")
    sla_max_latency_ms: int = Field(default=5000, description="Maximum latency in milliseconds")


class DataContract(BaseModel):
    contract_id: str = Field(..., description="Unique contract identifier")
    name: str = Field(..., description="Human-readable contract name")
    description: str = Field(..., description="Detailed description of the contract")
    version: str = Field(default="1.0.0", description="Contract version (semantic versioning)")
    columns: List[ColumnDefinition] = Field(..., description="List of column definitions")
    metadata: ContractMetadata = Field(default_factory=ContractMetadata, description="Contract metadata")
    created_at: str = Field(..., description="Contract creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Contract last update timestamp (ISO 8601)")

    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "users-v1",
                "name": "Users",
                "description": "Schema for user records",
                "version": "1.0.0",
                "columns": [
                    {
                        "name": "user_name",
                        "data_type": "string",
                        "nullable": False,
                        "description": "Username for the user"
                    },
                    {
                        "name": "email",
                        "data_type": "string",
                        "nullable": False,
                        "description": "Email address of the user"
                    },
                    {
                        "name": "date_of_birth",
                        "data_type": "date",
                        "nullable": False,
                        "description": "Date of birth in YYYY-MM-DD format"
                    }
                ],
                "metadata": {
                    "data_owner": "User Management",
                    "data_owner_email": "user-mgmt@company.com",
                    "data_steward": "Data Engineering",
                    "data_steward_email": "data-engineering@company.com",
                    "sla_uptime_percentage": 99.95,
                    "sla_max_latency_ms": 5000
                },
                "created_at": "2026-07-26T09:44:45.962207+00:00",
                "updated_at": "2026-07-26T09:44:45.962343+00:00"
            }
        }