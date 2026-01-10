# utils/id_generator.py
import random
import string

def generate_id(prefix):
    return prefix + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))