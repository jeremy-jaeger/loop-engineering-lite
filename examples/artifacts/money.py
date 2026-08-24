def dollars_to_cents(text):
    if text.startswith('$'):
        text = text[1:]
    if not text.replace('.', '', 1).isdigit():
        raise ValueError('Malformed input')
    return int(float(text) * 100)