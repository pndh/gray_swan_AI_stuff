"""Tool schemas + stub dispatch for the PARALLAX helpdesk email scenario.

get_emails lists the shared helpdesk inbox.
reply_to_email is the scored surface: a reply to an email address.
"""
import json


def tool_schemas():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_emails",
                "description": "List the latest emails in the shared helpdesk inbox (newest last).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max emails to return."}
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "reply_to_email",
                "description": "Send a reply to an email address.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address."},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "body"],
                },
            },
        },
    ]


def make_dispatch(scenario, sent_replies, tool_log):
    """Return {tool_name: callable(args)->dict}; reply_to_email appends to sent_replies."""

    def get_emails(args):
        limit = args.get("limit", 10) or 10
        return {"emails": scenario["inbox"][-limit:]}

    def reply_to_email(args):
        entry = {"to": args.get("to", ""), "subject": args.get("subject", ""),
                 "body": args.get("body", "")}
        sent_replies.append(entry)
        return {"status": "sent", "message_id": f"msg-{len(sent_replies):03d}"}

    dispatch = {"get_emails": get_emails, "reply_to_email": reply_to_email}

    def wrapped(name, args):
        tool_log.append({"name": name, "args": args})
        fn = dispatch.get(name)
        if fn is None:
            return {"error": f"unknown tool {name}"}
        return fn(args)

    return wrapped
