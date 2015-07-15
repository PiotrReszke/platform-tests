import base64

from test_utils.mail_utils.gmail.gmail_api import get_recent_message_to


def extract_code_from_message(message):
    b = base64.urlsafe_b64decode(message)
    c = b.decode()#.replace('=3D', '=').replace('=\r\n', '')
    d = c.find('code=')
    if d != -1:
        d += len('code=')
        e = c[d:].find('&')
        code = (c[d:d + e])
        return code
    else:
        raise Exception("Can't finde code in given message")


def get_code_from_gmail(email):
    message = get_recent_message_to(email)
    code = extract_code_from_message(message)
    return code
