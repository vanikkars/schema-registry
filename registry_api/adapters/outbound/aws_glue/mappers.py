"""AWS Glue type mappers and schema converters (adapter-level utilities)."""

import json
from registry_api.domain.models import DataContract


def contract_to_avro(contract: DataContract) -> str:
    """Convert a DataContract to AVRO schema format.

    Args:
        contract: DataContract model instance

    Returns:
        JSON string of AVRO schema
    """
    fields = []
    for col in contract.columns:
        field = {
            "name": col.name,
            "type": map_type_to_avro(col.data_type),
        }
        if col.description:
            field["doc"] = col.description
        if col.nullable:
            field["type"] = ["null", field["type"]]
            field["default"] = None
        fields.append(field)

    # Build comprehensive documentation including metadata
    doc = contract.description or ""
    if contract.metadata:
        doc += f"\n\nMetadata:\n"
        doc += f"  Data Owner: {contract.metadata.data_owner} ({contract.metadata.data_owner_email})\n"
        doc += f"  Data Steward: {contract.metadata.data_steward} ({contract.metadata.data_steward_email})\n"
        doc += f"  SLA Uptime: {contract.metadata.sla_uptime_percentage}%\n"
        doc += f"  SLA Max Latency: {contract.metadata.sla_max_latency_ms}ms"

    schema = {
        "type": "record",
        "name": contract.name.replace(" ", ""),
        "namespace": "com.example.schema",
        "doc": doc,
        "fields": fields,
    }

    return json.dumps(schema)


def map_type_to_glue(data_type: str) -> str:
    """Map contract data types to AWS Glue types.

    Args:
        data_type: Contract data type

    Returns:
        Glue/Hive type
    """
    type_map = {
        "string": "string",
        "integer": "bigint",
        "number": "double",
        "boolean": "boolean",
        "date": "date",
        "timestamp": "timestamp",
        "object": "string",
        "array": "array<string>",
    }
    return type_map.get(data_type, "string")


def map_type_to_avro(data_type: str) -> str:
    """Map contract data types to AVRO types.

    Args:
        data_type: Contract data type

    Returns:
        AVRO type
    """
    type_map = {
        "string": "string",
        "integer": "int",
        "number": "double",
        "boolean": "boolean",
        "date": "string",
        "timestamp": "string",
        "object": "string",
        "array": "array",
    }
    return type_map.get(data_type, "string")
