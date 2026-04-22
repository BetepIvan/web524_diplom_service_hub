import string
import random


def generate_slug():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))
