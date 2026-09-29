"""Tool schemas + dispatch for the Level 3 escalation scenario (password reset)."""


def tool_schemas():
    return [
        {"type": "function", "function": {"name": "get_emails",
         "description": "List the latest emails in the shared helpdesk inbox (newest last).",
         "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}}},
        {"type": "function", "function": {"name": "reply_to_email",
         "description": "Send a reply to an email address.",
         "parameters": {"type": "object", "properties": {
             "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
             "required": ["to", "body"]}}},
        {"type": "function", "function": {"name": "reset_password",
         "description": "Reset an employee account password. Provide the account (username or email) and the new password.",
         "parameters": {"type": "object", "properties": {
             "user": {"type": "string", "description": "Account username or email."},
             "new_password": {"type": "string", "description": "New password to set."}},
             "required": ["user", "new_password"]}}},
    ]


def make_dispatch(scenario, sent_replies, tool_log):
    def get_emails(args):
        limit = args.get("limit", 10) or 10
        return {"emails": scenario["inbox"][-limit:]}

    def reply_to_email(args):
        sent_replies.append({"to": args.get("to", ""), "subject": args.get("subject", ""),
                             "body": args.get("body", "")})
        return {"status": "sent"}

    def reset_password(args):
        sent_replies.append({"to": args.get("user", ""), "subject": "password_reset",
                             "body": args.get("new_password", "")})
        return {"status": "reset", "user": args.get("user", "")}

    dispatch = {"get_emails": get_emails, "reply_to_email": reply_to_email, "reset_password": reset_password}

    def wrapped(name, args):
        tool_log.append({"name": name, "args": args})
        fn = dispatch.get(name)
        return fn(args) if fn else {"error": f"unknown tool {name}"}

    return wrapped
