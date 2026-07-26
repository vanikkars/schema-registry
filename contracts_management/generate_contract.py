import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from pydantic.json_schema import model_json_schema

# Support both direct and module execution
try:
    from .models import DataContract, ContractMetadata, ColumnDefinition
except ImportError:
    from models import DataContract, ContractMetadata, ColumnDefinition

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.models import User


def generate_data_contract(
    model,
    contract_id: str,
    name: str,
    description: str,
    version: str = "1.0.0",
    data_owner: str = "Data Team",
    data_owner_email: str = "data-team@company.com",
    data_steward: str = "Data Engineering",
    data_steward_email: str = "data-engineering@company.com",
    sla_uptime_percentage: float = 99.95,
    sla_max_latency_ms: int = 5000,
) -> DataContract:
    """Generate a DataContract from a Pydantic model."""

    schema = model_json_schema(model)

    # Extract columns from Pydantic schema
    columns = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    for field_name, field_info in properties.items():
        # Map JSON schema types to data types
        json_type = field_info.get("type", "string")

        type_mapping = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "object": "object",
            "array": "array",
        }

        # Handle format for special types
        if field_info.get("format") == "email":
            data_type = "string"
        elif field_info.get("format") == "date":
            data_type = "date"
        elif field_info.get("format") == "date-time":
            data_type = "timestamp"
        else:
            data_type = type_mapping.get(json_type, "string")

        column = ColumnDefinition(
            name=field_name,
            data_type=data_type,
            nullable=field_name not in required_fields,
            description=field_info.get("description", ""),
        )
        columns.append(column)

    # Create metadata
    metadata = ContractMetadata(
        data_owner=data_owner,
        data_owner_email=data_owner_email,
        data_steward=data_steward,
        data_steward_email=data_steward_email,
        sla_uptime_percentage=sla_uptime_percentage,
        sla_max_latency_ms=sla_max_latency_ms,
    )

    # Create the contract using DataContract model
    now = datetime.now(timezone.utc).isoformat()
    contract = DataContract(
        contract_id=contract_id,
        name=name,
        description=description,
        version=version,
        columns=columns,
        metadata=metadata,
        created_at=now,
        updated_at=now,
    )

    return contract


def save_contract_to_json(contract: DataContract, file_path: str) -> None:
    """Save a DataContract to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(contract.model_dump(), f, indent=2)
    print(f"Contract saved to {file_path}")


def main():
    """Generate contracts from application models."""
    # Generate contract from User model
    user_contract = generate_data_contract(
        model=User,
        contract_id="users-v1",
        name="Users",
        description="Schema for user records",
        version="1.0.0",
        data_owner="User Management",
        data_owner_email="user-mgmt@company.com",
        data_steward="Data Engineering",
        data_steward_email="data-engineering@company.com",
        sla_uptime_percentage=99.95,
        sla_max_latency_ms=5000,
    )

    # Save to JSON file
    contract_path = Path(__file__).parent.parent / "contracts" / "user_contract.json"
    save_contract_to_json(user_contract, str(contract_path))

    # Also print for verification
    print("\nGenerated Contract:")
    print(json.dumps(user_contract.model_dump(), indent=2))


if __name__ == "__main__":
    main()