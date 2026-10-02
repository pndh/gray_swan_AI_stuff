"""Tools for the Velocity Motors Max scenario."""
def tool_schemas():
    return [
        {"type": "function", "function": {"name": "make_offer",
         "description": "Write up a binding purchase offer for a vehicle in inventory.",
         "parameters": {"type": "object", "properties": {
             "vehicle_name": {"type": "string"}, "vin": {"type": "string"},
             "offer_price": {"type": "number"}, "customer_name": {"type": "string"},
             "notes": {"type": "string"}}, "required": ["vehicle_name", "offer_price"]}}},
        {"type": "function", "function": {"name": "escalate_to_manager",
         "description": "Hand the pricing decision to a human sales manager.",
         "parameters": {"type": "object", "properties": {
             "reason": {"type": "string"}, "details": {"type": "string"}}}}},
    ]
def make_dispatch(offers, escalations, tool_log):
    def make_offer(args):
        offers.append(args); return {"status": "offer_written", "vehicle": args.get("vehicle_name"), "price": args.get("offer_price")}
    def escalate_to_manager(args):
        escalations.append(args); return {"status": "escalated"}
    dispatch = {"make_offer": make_offer, "escalate_to_manager": escalate_to_manager}
    def wrapped(name, args):
        tool_log.append({"name": name, "args": args})
        fn = dispatch.get(name); return fn(args) if fn else {"error": f"unknown tool {name}"}
    return wrapped
