
import re
def detect_pesel(text):
    return re.findall(r'\b\d{11}\b', text)
