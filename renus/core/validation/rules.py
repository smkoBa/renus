import re

def valid_required(data:dict)->any:
    if data['input'] is not None:
        return True
    return ['required_error']

def valid_string(data: dict) -> any:
    if data['input'] is None:
        return True
    t = type(data['input'])
    if t is str:
        return True
    return ['type_error', ['string', str(t)]]


def valid_bool(data: dict) -> any:
    if data['input'] is None:
        return True
    t = type(data['input'])
    if t is bool:
        return True
    return ['type_error', ['bool', str(t)]]


def valid_list(data: dict) -> any:
    if data['input'] is None:
        return True
    t = type(data['input'])
    if t is list:
        return True
    return ['type_error', ['list', str(t)]]


def valid_dict(data: dict) -> any:
    if data['input'] is None:
        return True
    t = type(data['input'])
    if t is dict:
        return True
    return ['type_error', ['dict', str(t)]]


def valid_int(data: dict) -> any:
    if data['input'] is None:
        return True
    t = type(data['input'])
    if t is int:
        return True
    return ['type_error', ['int', str(t)]]


def valid_float(data: dict) -> any:
    if data['input'] is None:
        return True
    t = type(data['input'])
    if t is float:
        return True
    return ['type_error', ['float', str(t)]]


def valid_len(data: dict) -> any:
    if data['input'] is None:
        return True
    length = len(data['input'])
    if len(data['args']) < 1:
        return ['len_error', None, length]

    if length == int(data['args'][0]):
        return True
    return ['len_error', [int(data['args'][0]), length]]


def valid_min_len(data: dict) -> any:
    if data['input'] is None:
        return True
    length = len(data['input'])
    if len(data['args']) < 1:
        return ['min_len_error', [None, length]]
    if length >= int(data['args'][0]):
        return True
    return ['min_len_error', [int(data['args'][0]), length]]


def valid_max_len(data: dict) -> any:
    if data['input'] is None:
        return True
    length = len(data['input'])
    if len(data['args']) < 1:
        return ['max_len_error', [None, length]]
    if length <= int(data['args'][0]):
        return True
    return ['max_len_error', [int(data['args'][0]), length]]


def valid_eq(data: dict) -> any:
    if data['input'] is None:
        return True
    if len(data['args']) < 1:
        return ['eq_error', [None, data['input']]]
    if data['input'] == float(data['args'][0]):
        return True
    return ['eq_error', [float(data['args'][0]), data['input']]]


def valid_min_count(data):
    if data['input'] is None:
        return True
    if len(data['args']) < 1:
        return ['min_count_error', [None, data['input']]]
    if len(data['input']) >= float(data['args'][0]):
        return True
    return ['min_count_error', [float(data['args'][0]), len(data['input'])]]


def valid_max_count(data):
    if data['input'] is None:
        return True
    if len(data['args']) < 1:
        return ['max_count_error', [None, data['input']]]
    if len(data['input']) <= float(data['args'][0]):
        return True
    return ['max_count_error', [float(data['args'][0]), len(data['input'])]]


def valid_count(data):
    if data['input'] is None:
        return True
    if len(data['args']) < 1:
        return ['count_error', [None, data['input']]]
    if len(data['input']) == float(data['args'][0]):
        return True

    return ['count_error', [float(data['args'][0]), len(data['input'])]]


def valid_min(data: dict) -> any:
    if data['input'] is None:
        return True
    if len(data['args']) < 1:
        return ['min_error', [None, data['input']]]
    if data['input'] >= float(data['args'][0]):
        return True
    return ['min_error', [float(data['args'][0]), data['input']]]


def valid_numeric(data: dict) -> any:
    if data['input'] is None:
        return True
    if re.compile('[\d]+').fullmatch(data['input']) != None:
        return True
    return ['numeric_error', [data['input']]]


def valid_max(data: dict) -> any:
    if data['input'] is None:
        return True
    if len(data['args']) < 1:
        return ['max_error', [None, data['input']]]
    if data['input'] <= float(data['args'][0]):
        return True
    return ['max_error', [float(data['args'][0]), data['input']]]


def valid_accepted(data: dict) -> any:
    if data['input'] is None:
        return True
    if valid_string(data) == True:
        data['input'] = data['input'].lower()
    acceptable = ['yes', 'on', '1', 1, True, 'true']
    if data['input'] in acceptable:
        return True
    return ['accepted_error',[data['input']]]


def valid_email(data):
    if data['input'] is None:
        return True
    allow_domain = []
    is_string = valid_string(data)
    if is_string == True:
        data['input'] = data['input'].lower()
    else:
        return is_string
    if len(data['args']) > 1:
        allow_domain = data['args']

    parse = data['input'].split('@')
    if len(parse) < 2:
        return ['email_at_error', [data['input']]]
    name, domain = parse
    parse_domain = domain.split('.')
    if len(parse_domain) < 2:
        return ['email_domain_name_error', [domain]]
    if len(parse_domain[1]) < 2:
        return ['email_domain_name_error', [domain]]
    if len(allow_domain) > 1:
        if domain not in allow_domain:
            return ['email_domain_allow_error', [domain, allow_domain]]
    if len(name) < 3:
        return ['email_name_error', [3, data['input']]]

    return True


def valid_in(data):
    if data['input'] is None:
        return True
    arr = []
    for item in data['args']:
        parse = item.split('=')
        if len(parse) > 1:
            if parse[1] == 'int':
                arr.append(int(parse[0]))
            elif parse[1] == 'bool':
                arr.append(bool(parse[0]))
        else:
            arr.append(parse[0])
    if data['input'] in arr:
        return True
    return ['in_error', [data['input'], str(arr)]]


def valid_not_in(data):
    if data['input'] is None:
        return True
    arr = []
    for item in data['args']:
        parse = item.split('=')
        if len(parse) > 1:
            if parse[1] == 'int':
                arr.append(int(parse[0]))
            elif parse[1] == 'bool':
                arr.append(bool(parse[0]))
        else:
            arr.append(parse[0])
    if data['input'] not in arr:
        return True
    return ['in_error', [data['input'], str(arr)]]


def valid_regex(data):
    if data['input'] is None:
        return True
    msg = None
    if len(data['args']) < 1:
        return ['regex_error', None, None]
    if len(data['args']) == 2:
        msg = data['args'][1]

    if re.compile(data['args'][0]).fullmatch(data['input']) is not None:
        return True
    return ['regex_error', [data['input'], msg]]


def valid_url(data):
    if data['input'] is None:
        return True
    string = valid_string(data)
    if string is not True:
        return string
    pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    if re.compile(pattern).fullmatch(data['input']) is not None:
        return True
    return ['url_error', [data['input']]]


def valid_ip(data):
    if data['input'] is None:
        return True
    string = valid_string(data)
    if string is not True:
        return string
    ipv = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", data['input'])
    if bool(ipv) and all(map(lambda n: 0 <= int(n) <= 255, ipv.groups())):
        return True

    return ['ip_error', [data['input']]]


def valid_image(data):
    allowed = ['jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
    # todo
    return False


def valid_size(data):
    #todo
    return False


def valid_file(data):
    # todo
    return False


def valid_file_type(data):
    # todo
    return False


def valid_unique(data):
    '''

    :param data store: 'unique:collection:field'
    :param data update: 'unique:collection:field:_id'
    :return:
    '''
    if data['input'] is None:
        return True
    ln=len(data['args'])
    if ln not in [2,3]:
        return ['unique_arg_error', [data['input']]]
    from renus.core.model import ModelBase
    model = ModelBase(data['args'][0], request='test').where({
        data['args'][1]: data['input']
    }).select('_id').first()
    if model is None:
        return True
    if ln==3 and data['args'][2]==model['_id']:
        return True
    return ['unique_error', [data['input']]]


def valid_exists(data):
    if data['input'] is None:
        return True
    if len(data['args']) != 2:
        return ['exists_arg_error', [data['input']]]
    from renus.core.model import ModelBase
    model=ModelBase(data['args'][0],request='test').where({
        data['args'][1]:data['input']
    }).select('_id').first()
    if model is not None:
        return True
    return ['exists_error', [data['input']]]


def valid_exists_count(data):
    # todo
    return False
