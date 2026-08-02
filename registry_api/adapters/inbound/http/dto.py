"""Data transfer objects and response builders for HTTP API."""


def build_schema_response(schema_info: dict, contract: dict) -> dict:
    """Build a schema response dict from schema details and contract info.

    Args:
        schema_info: Schema details from the registry adapter
        contract: Contract data

    Returns:
        Formatted response dict
    """
    return {
        "arn": schema_info.get("arn", ""),
        "name": contract.get("contract_id", ""),
        "version": contract.get("version", ""),
        "description": schema_info.get("description", ""),
        "latest_version": schema_info.get("latest_version", 0),
        "next_version": schema_info.get("next_version", 0),
        "checkpoint": schema_info.get("checkpoint", ""),
        "status": schema_info.get("status", "AVAILABLE"),
        "data_format": schema_info.get("data_format", "AVRO"),
        "compatibility": schema_info.get("compatibility", "BACKWARD"),
        "columns": [
            {
                "name": col["name"],
                "type": col["type"],
                "nullable": col["nullable"],
                "description": col.get("description", ""),
            }
            for col in contract.get("columns", [])
        ],
        "metadata": contract.get("metadata", {}),
    }


def format_error_response(error: Exception) -> dict:
    """Format a domain error into an error response dict.

    Args:
        error: Domain exception

    Returns:
        Error response dict
    """
    return {
        "error": error.__class__.__name__,
        "message": str(error),
    }
