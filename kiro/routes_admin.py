# -*- coding: utf-8 -*-

# Kiro Gateway
# https://github.com/jwadow/kiro-gateway
# Copyright (C) 2025 Jwadow
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Admin API routes for configuration management.

Provides endpoints for:
- Reloading credentials.json
- Viewing account status
- Health checks
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from loguru import logger

from kiro.config import PROXY_API_KEY

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_token(x_admin_token: Optional[str] = Header(None)) -> None:
    """
    Verify admin authentication token.

    Uses the same PROXY_API_KEY for simplicity.
    In production, consider using a separate ADMIN_API_KEY.

    Args:
        x_admin_token: Admin token from X-Admin-Token header

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not x_admin_token or x_admin_token != PROXY_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing X-Admin-Token header"
        )


@router.post("/reload")
async def reload_configuration(
    request: Request,
    x_admin_token: Optional[str] = Header(None)
) -> dict:
    """
    Reload credentials.json and reinitialize accounts.

    This endpoint allows hot-reloading of configuration without restarting the server.

    Headers:
        X-Admin-Token: Admin authentication token (same as PROXY_API_KEY)

    Returns:
        {
            "status": "success",
            "message": "Configuration reloaded",
            "accounts_before": 2,
            "accounts_after": 3,
            "reinitialized": ["account1", "account2"]
        }

    Raises:
        HTTPException: If authentication fails or reload fails
    """
    verify_admin_token(x_admin_token)

    account_manager = request.app.state.account_manager

    # Count accounts before reload
    accounts_before = len(account_manager._accounts)

    logger.info("Admin: Reloading configuration...")

    try:
        # Step 1: Reload credentials.json
        await account_manager.load_credentials()

        # Step 2: Reload state.json (restore runtime state for existing accounts)
        await account_manager.load_state()

        # Step 3: Initialize new accounts (lazy initialization)
        # Only initialize accounts that don't have auth_manager yet
        reinitialized = []
        for account_id, account in account_manager._accounts.items():
            if account.auth_manager is None:
                success = await account_manager._initialize_account(account_id)
                if success:
                    reinitialized.append(account_id)
                    logger.info(f"Initialized new account: {account_id}")

        # Step 4: Save updated state
        await account_manager._save_state()

        accounts_after = len(account_manager._accounts)

        logger.info(
            f"Configuration reloaded: {accounts_before} → {accounts_after} accounts, "
            f"{len(reinitialized)} newly initialized"
        )

        return {
            "status": "success",
            "message": "Configuration reloaded successfully",
            "accounts_before": accounts_before,
            "accounts_after": accounts_after,
            "reinitialized": reinitialized
        }

    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload configuration: {str(e)}"
        )


@router.get("/status")
async def get_status(
    request: Request,
    x_admin_token: Optional[str] = Header(None)
) -> dict:
    """
    Get current account manager status.

    Headers:
        X-Admin-Token: Admin authentication token

    Returns:
        {
            "total_accounts": 3,
            "initialized_accounts": 2,
            "current_account_index": 0,
            "accounts": [...]
        }

    Raises:
        HTTPException: If authentication fails
    """
    verify_admin_token(x_admin_token)

    account_manager = request.app.state.account_manager

    accounts_info = []
    for account_id, account in account_manager._accounts.items():
        accounts_info.append({
            "id": account_id,
            "initialized": account.auth_manager is not None,
            "failures": account.failures,
            "stats": {
                "total_requests": account.stats.total_requests,
                "successful_requests": account.stats.successful_requests,
                "failed_requests": account.stats.failed_requests
            }
        })

    return {
        "total_accounts": len(account_manager._accounts),
        "initialized_accounts": sum(1 for a in account_manager._accounts.values() if a.auth_manager is not None),
        "current_account_index": account_manager._current_account_index,
        "accounts": accounts_info
    }


@router.get("/accounts")
async def list_accounts(
    request: Request,
    x_admin_token: Optional[str] = Header(None)
) -> dict:
    """
    List all configured accounts with details.

    Headers:
        X-Admin-Token: Admin authentication token

    Returns:
        {
            "accounts": [
                {
                    "id": "/path/to/creds.json",
                    "initialized": true,
                    "auth_type": "kiro_desktop",
                    "region": "us-east-1",
                    "models_count": 5,
                    "failures": 0,
                    "stats": {...}
                }
            ]
        }

    Raises:
        HTTPException: If authentication fails
    """
    verify_admin_token(x_admin_token)

    account_manager = request.app.state.account_manager

    accounts_list = []
    for account_id, account in account_manager._accounts.items():
        account_info = {
            "id": account_id,
            "initialized": account.auth_manager is not None,
            "failures": account.failures,
            "last_failure_time": account.last_failure_time,
            "models_cached_at": account.models_cached_at,
            "stats": {
                "total_requests": account.stats.total_requests,
                "successful_requests": account.stats.successful_requests,
                "failed_requests": account.stats.failed_requests
            }
        }

        if account.auth_manager:
            account_info["auth_type"] = account.auth_manager.auth_type.value
            account_info["region"] = account.auth_manager.region
            account_info["api_host"] = account.auth_manager.api_host

        if account.model_resolver:
            account_info["models_count"] = len(account.model_resolver.get_available_models())

        accounts_list.append(account_info)

    return {"accounts": accounts_list}
