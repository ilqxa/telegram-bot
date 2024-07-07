import re


def screen_special_characters(text: str) -> str:
    special_chars = r"_\*\[\]\(\)~`>#\+\-=|{}\.!"
    regex_pattern = f"[{re.escape(special_chars)}]"
    escaped_text = re.sub(regex_pattern, lambda match: f"\\{match.group(0)}", text)
    return escaped_text
