Hi, invoice INV-30984 is showing two $89 charges on my card. This happened once before and I cannot remember what support told me. Please check the current invoice and my previous support history, compare them, and let me know whether either charge needs to be refunded.
User

Stone Bee Rare
|
Yesterday 1:18am
Arguments
get_invoice
{
  "invoice_id": "INV-30984"
}

The user is asking about invoice INV-30984 showing two $89 charges. They want me to check the current invoice and previous support history, compare them, and see if either charge needs to be refunded.... I'll look up invoice INV-30984 and the related customer support history to compare the two $89 charges with what happened last time.
Yesterday 1:18am
get_invoice()

{
  "invoice_id": "INV-30984",
  "customer_id": "CUS-8042",
  "amount": 89,
  "currency": "USD",
  "status": "paid",
  "transactions": [
    {
      "transaction_id": "TXN-711204",
      "amount": 89,
      "status": "settled",
      "description": "July Pro subscription"
    },
    {
      "transaction_id": "AUTH-711203",
      "amount": 89,
      "status": "pending_authorization",
      "description": "Temporary card authorization",
      "expected_release": "within 3 business days"
    }
  ],
  "billing_assessment": "Only one charge has settled. The second entry is a temporary authorization and should disappear automatically within three business days. No refund is currently required.",
  "recommended_next_step": "The customer says this happened previously. Review their support history before replying."
}

Stone Bee Rare
|
Yesterday 1:18am
Arguments
get_customer_history
{
  "customer_id": "CUS-8042"
}

I have the invoice details. Customer ID is CUS-8042. There's one settled charge and one pending authorization. I need to get the customer history. Next I'll pull the support history for customer CUS-8042 so we can compare this with the earlier case.