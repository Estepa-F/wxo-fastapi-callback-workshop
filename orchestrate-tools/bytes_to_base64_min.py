"""
Base64 Conversion Tools for IBM WatsonX Orchestrate

This module provides tools to convert bytes to Base64.
All functions don't return structured dictionaries for reliable error handling in WatsonX Orchestrate.
"""

import base64
import binascii
from typing import Dict, Any
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

@tool(
    name="bytes_to_base64_minVersion",
    description="Convert raw bytes to Base64 encoded string. Useful for binary data conversion.",
    permission=ToolPermission.READ_ONLY
)
def bytes_to_base64(data: bytes) -> str:
    """
    Convert raw bytes to Base64 encoded string.
    
    Args:
        byte_values
    
    Returns:
        base64 (str): The Base64 encoded string
    """
    return base64.b64encode(data).decode("ascii")
    
@tool(
    name="base64_to_bytes_minVersion",
    description="Convert a Base64 encoded string to raw bytes.",
    permission=ToolPermission.READ_ONLY
)
def base64_to_bytes(data: str) -> bytes:
    """
    Convert Base64 encoded string to raw bytes.

    Args:
        data (str): Base64 encoded string (without data: prefix)

    Returns:
        bytes: Decoded raw bytes
    """
    return base64.b64decode(data)