from bs4 import BeautifulSoup


def format_serializer_errors(errors):
    formatted = []
    for field, messages in errors.items():
        for message in messages:
            formatted.append({"field": field, "message": str(message)})
    return formatted


def rich_text_to_plain_text(html: str) -> str:
    return BeautifulSoup(
        html or "",
        "html.parser",
    ).get_text(" ", strip=True)
