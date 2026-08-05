def format_errors(errors):
    formatted = []
    for field, messages in errors.items():
        for message in messages:
            formatted.append({"field": field, "message": str(message)})
    return formatted
