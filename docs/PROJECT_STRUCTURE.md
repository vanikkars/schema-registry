# Project Structure

## Folders

### `app/`
Application-specific models and logic.
- `__init__.py` - Package initialization
- `models.py` - Application models (e.g., User)

### `contracts_management/`
Data contracts management and generation logic.
- `__init__.py` - Package initialization with model exports
- `models.py` - Contract-related Pydantic models (DataContract, ContractMetadata, ColumnDefinition)
- `generate_contract.py` - Contract generation logic from Pydantic models

### `contracts/`
Generated and stored data contracts in JSON format.
- `user_contract.json` - Generated user contract
- `test_contract.json` - Test contract
- `transaction_contract.json` - Transaction contract

### `infra/`
Infrastructure as Code for cloud resources.
- `aws/` - AWS-specific Terraform configurations
  - `main.tf` - Glue Schema Registry and schema definitions
  - `variables.tf` - Terraform variable definitions
  - `terraform.tfvars` - Variable values for development
  - `backend.tf` - Remote state configuration (optional)
  - `README.md` - AWS Glue Schema Registry documentation

## Usage

### Running contract generation:

```bash
python contracts_management/generate_contract.py
```

### Using in code:

```python
from contracts_management import DataContract, generate_data_contract, save_contract_to_json
from app.models import User

# Generate contract
contract = generate_data_contract(
    model=User,
    contract_id="users-v1",
    name="Users",
    description="Schema for user records",
)

# Save to JSON
save_contract_to_json(contract, "contracts/user_contract.json")
```

## Separation of Concerns

- **app/** - Domain models (User, etc.)
- **contracts_management/** - Contract infrastructure and utilities
- **contracts/** - Generated contract artifacts
- **infra/** - Cloud infrastructure (AWS Glue Schema Registry)

## Workflow

1. Define application models in `app/models.py`
2. Generate contracts using `python contracts_management/generate_contract.py`
3. Contracts are saved to `contracts/` folder
4. Deploy infrastructure with Terraform: `cd infra/aws && terraform apply`
5. Upload contracts to AWS Glue Schema Registry
