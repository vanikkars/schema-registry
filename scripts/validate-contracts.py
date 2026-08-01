#!/usr/bin/env python3
"""
Validate data contracts against the registry API.
Can be used locally or in CI/CD pipelines.

Usage:
    python scripts/validate-contracts.py                    # Validate all contracts
    python scripts/validate-contracts.py contracts/user/    # Validate specific directory
    python scripts/validate-contracts.py contracts/user/02/user_v1.json  # Validate single file

Requirements:
    pip install requests
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found")
    print("Install with: pip install requests")
    sys.exit(1)


@dataclass
class ValidationResult:
    file: str
    status: str  # PASSED, FAILED, SKIPPED
    contract_name: str = None
    reason: str = None
    response_code: int = None


class ContractValidator:
    def __init__(self, registry_url: str = "http://localhost:8000"):
        self.registry_url = registry_url.rstrip('/')
        self.results: List[ValidationResult] = []

    def validate_contract(self, file_path: Path) -> ValidationResult:
        """Validate a single contract file."""
        if not file_path.exists():
            return ValidationResult(
                file=str(file_path),
                status="SKIPPED",
                reason="File not found"
            )

        # Check if it's a JSON file
        if file_path.suffix != '.json':
            return ValidationResult(
                file=str(file_path),
                status="SKIPPED",
                reason="Not a JSON file"
            )

        try:
            with open(file_path, 'r') as f:
                contract = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                file=str(file_path),
                status="FAILED",
                reason=f"Invalid JSON: {str(e)}"
            )

        # Validate that contract has a 'name' field (minimal requirement)
        if 'name' not in contract:
            return ValidationResult(
                file=str(file_path),
                status="FAILED",
                contract_name='unknown',
                reason="Missing required field: 'name'"
            )

        # Send to registry API
        try:
            response = requests.post(
                f"{self.registry_url}/api/v1/schemas",
                json=contract,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 201]:
                return ValidationResult(
                    file=str(file_path),
                    status="PASSED",
                    contract_name=contract.get('name'),
                    response_code=response.status_code
                )
            else:
                return ValidationResult(
                    file=str(file_path),
                    status="FAILED",
                    contract_name=contract.get('name'),
                    reason=f"API returned {response.status_code}: {response.text[:100]}",
                    response_code=response.status_code
                )

        except requests.exceptions.ConnectionError:
            return ValidationResult(
                file=str(file_path),
                status="FAILED",
                contract_name=contract.get('name'),
                reason=f"Cannot connect to registry API at {self.registry_url}"
            )
        except requests.exceptions.Timeout:
            return ValidationResult(
                file=str(file_path),
                status="FAILED",
                contract_name=contract.get('name'),
                reason="Registry API request timed out"
            )

    def validate_contracts(self, target_path: Path = None) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate contracts in a directory or single file.
        Returns (all_passed, results)
        """
        if target_path is None:
            target_path = Path('contracts')

        target_path = Path(target_path)

        # Collect files to validate
        files_to_validate = []

        if target_path.is_file():
            files_to_validate = [target_path]
        elif target_path.is_dir():
            files_to_validate = sorted(target_path.rglob('*.json'))
        else:
            print(f"⚠️  Warning: {target_path} not found", file=sys.stderr)
            return True, []

        if not files_to_validate:
            print(f"⚠️  Warning: No JSON files found in {target_path}")
            print(f"⏭️  Skipping validation - no contracts defined")
            return True, []

        # Validate each file
        for file_path in files_to_validate:
            result = self.validate_contract(file_path)
            self.results.append(result)
            self._print_result(result)

        # Summary - only fail if there are actual validation failures (not missing files)
        failed_validations = [r for r in self.results if r.status == "FAILED" and r.reason != "File not found"]
        all_passed = len(failed_validations) == 0
        return all_passed, self.results

    def _print_result(self, result: ValidationResult):
        """Print a single validation result."""
        status_emoji = {
            'PASSED': '✅',
            'FAILED': '❌',
            'SKIPPED': '⏭️ '
        }

        emoji = status_emoji.get(result.status, '❓')
        print(f"{emoji} {result.file}")

        if result.status == "FAILED":
            print(f"   Reason: {result.reason}")
        elif result.status == "PASSED":
            print(f"   Contract: {result.contract_name} (HTTP {result.response_code})")

    def print_summary(self):
        """Print validation summary."""
        if not self.results:
            return

        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        skipped = sum(1 for r in self.results if r.status == "SKIPPED")

        print(f"\n{'='*60}")
        print(f"Validation Summary")
        print(f"{'='*60}")
        print(f"✅ Passed:  {passed}")
        print(f"❌ Failed:  {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"{'='*60}")

        if failed > 0:
            print("\nFailed contracts:")
            for result in self.results:
                if result.status == "FAILED":
                    print(f"  - {result.file}: {result.reason}")

    def export_results(self, output_file: str):
        """Export results to JSON file."""
        data = {
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r.status == "PASSED"),
                'failed': sum(1 for r in self.results if r.status == "FAILED"),
                'skipped': sum(1 for r in self.results if r.status == "SKIPPED"),
            },
            'results': [asdict(r) for r in self.results]
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n📄 Results exported to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate data contracts against the registry API"
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='contracts',
        help='Path to contract file or directory (default: contracts/)'
    )
    parser.add_argument(
        '--registry-url',
        default='http://localhost:8000',
        help='Registry API URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--export',
        help='Export results to JSON file'
    )

    args = parser.parse_args()

    print(f"\n🔍 Validating contracts...")
    print(f"📍 Registry API: {args.registry_url}")
    print(f"📂 Target path: {args.path}\n")

    validator = ContractValidator(registry_url=args.registry_url)
    all_passed, results = validator.validate_contracts(Path(args.path))

    validator.print_summary()

    if args.export:
        validator.export_results(args.export)

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()