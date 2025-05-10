import re

def detect(text):
    return re.findall(r'\b(?:\d[ -]*?){13,16}\b', text)
