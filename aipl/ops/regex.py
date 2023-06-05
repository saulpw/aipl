import re

from aipl import defop


def preprompt_capture(prompt:str='') -> re.Pattern:
    import re
    return re.compile(prompt)

@defop('regex-capture', 0, 0.5, preprompt=preprompt_capture)
def regex_capture(aipl, v:str, prompt:re.Pattern=None) -> dict:
    'Capture from prompt regex into named matching groups.'
    m = prompt.match(v)
    if not m:
        return {}
    return m.groupdict()


def preprompt_translate(prompt:str=''):
    import re
    d = []
    for line in prompt.splitlines():
       regex, output = line.split(maxsplit=1)
       d.append((re.compile(regex), output))

    return d

@defop('regex-translate', 0, 0, preprompt=preprompt_translate)
def regex_translate(aipl, v:str, prompt:list):
    '''Translate input according to regex translation rules in prompt, one per line, with regex and output separated by whitespace:
        \bDr\.?\b Doctor
        \bJr\.?\b Junior
    '''
    for regex, output in prompt:
        m = regex.match(v)
        if m:
            return output
    return v
