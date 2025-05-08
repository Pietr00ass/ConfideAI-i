
import re
def detect_emails(text):
    return re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
