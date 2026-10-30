"""Operator command parsing and delivery through the public Auth service only."""

import argparse
import sys
from uuid import UUID

from ui_http.auth import AuthFailureKind, AuthServiceError, create_service


def _uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError:
        raise argparse.ArgumentTypeError("user-id must be a UUID") from None


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("auth", help="Review and manage Auth users.")
    operations = parser.add_subparsers(dest="auth_command", required=True)
    operations.add_parser("pending", help="List pending registration requests.")
    for operation in ("approve", "reject", "disable"):
        command = operations.add_parser(operation, help=f"{operation.title()} a user.")
        command.add_argument("user_id", type=_uuid, metavar="user-id")


def run(args: argparse.Namespace) -> int:
    try:
        service = create_service()
        if args.auth_command == "pending":
            users = service.list_pending()
            if not users:
                print("No pending registration requests.")
            for user in users:
                print(f"{user.id}\t{user.username}\t{user.status}\t{user.created_at.isoformat()}")
        else:
            operation = {
                "approve": service.approve, "reject": service.reject, "disable": service.disable,
            }[args.auth_command]
            identity = operation(args.user_id)
            print(f"{identity.id}\t{identity.username}\t{identity.status}")
    except AuthServiceError as error:
        # Map only the classified failure, never raw exception or persistence text.
        if error.kind == AuthFailureKind.OPERATIONAL_FAILURE:
            print("Authentication service unavailable.", file=sys.stderr)
            return 1
        print({
            AuthFailureKind.INVALID_INPUT: "Invalid authentication input.",
            AuthFailureKind.NOT_FOUND: "User not found.",
            AuthFailureKind.INVALID_TRANSITION: "Invalid user status transition.",
        }[error.kind], file=sys.stderr)
        return 2
    return 0
