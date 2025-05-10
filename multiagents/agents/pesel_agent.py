import re

def detect(text):
    return re.findall(r'\b\d{11}\b', text)
