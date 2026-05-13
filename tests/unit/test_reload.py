#!/usr/bin/env python3
"""
Quick test script for configuration hot reload functionality.

Usage:
    python test_reload.py
"""

import os
import sys
import requests
from pathlib import Path


def read_proxy_api_key():
    """Read PROXY_API_KEY from .env file."""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ Error: .env file not found")
        return None

    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line.startswith("PROXY_API_KEY="):
            value = line.split("=", 1)[1]
            # Remove quotes
            value = value.strip('"').strip("'")
            return value

    print("❌ Error: PROXY_API_KEY not found in .env")
    return None


def test_reload(base_url: str, token: str):
    """Test /admin/reload endpoint."""
    print("\n" + "="*60)
    print("Testing: POST /admin/reload")
    print("="*60)

    try:
        response = requests.post(
            f"{base_url}/admin/reload",
            headers={
                "X-Admin-Token": token,
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Accounts before: {data.get('accounts_before')}")
            print(f"   Accounts after: {data.get('accounts_after')}")
            print(f"   Reinitialized: {len(data.get('reinitialized', []))}")
            if data.get('reinitialized'):
                for acc in data['reinitialized']:
                    print(f"      - {acc}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the server running?")
        print("   Run: make run")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_status(base_url: str, token: str):
    """Test /admin/status endpoint."""
    print("\n" + "="*60)
    print("Testing: GET /admin/status")
    print("="*60)

    try:
        response = requests.get(
            f"{base_url}/admin/status",
            headers={"X-Admin-Token": token},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Total accounts: {data.get('total_accounts')}")
            print(f"   Initialized accounts: {data.get('initialized_accounts')}")
            print(f"   Current account index: {data.get('current_account_index')}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_accounts(base_url: str, token: str):
    """Test /admin/accounts endpoint."""
    print("\n" + "="*60)
    print("Testing: GET /admin/accounts")
    print("="*60)

    try:
        response = requests.get(
            f"{base_url}/admin/accounts",
            headers={"X-Admin-Token": token},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            accounts = data.get('accounts', [])
            print("✅ Success!")
            print(f"   Found {len(accounts)} account(s):")

            for i, acc in enumerate(accounts, 1):
                print(f"\n   Account #{i}:")
                print(f"      ID: {acc.get('id')}")
                print(f"      Initialized: {acc.get('initialized')}")
                print(f"      Failures: {acc.get('failures')}")

                if acc.get('auth_type'):
                    print(f"      Auth Type: {acc.get('auth_type')}")
                    print(f"      Region: {acc.get('region')}")

                if acc.get('models_count'):
                    print(f"      Models: {acc.get('models_count')}")

                stats = acc.get('stats', {})
                print(f"      Requests: {stats.get('total_requests', 0)} total, "
                      f"{stats.get('successful_requests', 0)} success, "
                      f"{stats.get('failed_requests', 0)} failed")

            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_unauthorized(base_url: str):
    """Test authentication with wrong token."""
    print("\n" + "="*60)
    print("Testing: Authentication (wrong token)")
    print("="*60)

    try:
        response = requests.get(
            f"{base_url}/admin/status",
            headers={"X-Admin-Token": "wrong-token"},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 401:
            print("✅ Success! Correctly rejected unauthorized request")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Kiro Gateway - Configuration Hot Reload Test")
    print("="*60)

    # Read token from .env
    token = read_proxy_api_key()
    if not token:
        sys.exit(1)

    print(f"✓ PROXY_API_KEY loaded: {token[:10]}...")

    # Base URL
    base_url = "http://localhost:8000"

    # Run tests
    results = []

    results.append(("Status", test_status(base_url, token)))
    results.append(("Accounts", test_accounts(base_url, token)))
    results.append(("Reload", test_reload(base_url, token)))
    results.append(("Auth", test_unauthorized(base_url)))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
