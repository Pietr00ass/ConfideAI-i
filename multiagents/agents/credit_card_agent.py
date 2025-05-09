
import re
def detect_credit_cards(text):
    return re.findall(r'\b(?:\d[ -]*?){13,16}\b', text)
