from invoice_db.assistant.router import AssistantRouter

router = AssistantRouter()

examples = [
    "How many paid invoices do I have?",
    "Show overdue invoices",
    "Show invoices over $500",
    "Show invoices for John Smith",
    "Tell me a joke",
]

for example in examples:
    result = router.route(
        example,
        customer_names=["John Smith", "Alice Johnson"],
    )

    print()
    print("Message:", example)
    print(result.model_dump())