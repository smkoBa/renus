from renus.core.exception import abort_if

def keys_exists(element, keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return 'renus validation:key not exist'
    return _element

class Validate:
    def __init__(self, form: dict, break_on_error: bool = False) -> None:
        self._form = form
        self._break_on_error = break_on_error
        self._error = False
        self._msg = {}

    def rules(self, rules_data: dict,msg:str='invalid_data'):
        res = {}
        for field in rules_data:
            val=keys_exists(self._form, field.split('.'))

            if val!='renus validation:key not exist':
                if val is None and 'default' in rules_data[field]:
                    val=rules_data[field]['default']

                check = self.__check(val, rules_data[field])
                if check == True:
                    res[field] = val
                else:
                    self._error = True
                    self._msg[field] = check
                    if self._break_on_error:
                        break
            elif 'default' in rules_data[field]:
                res[field] = rules_data[field]['default']
            elif 'required' in rules_data[field]:
                self._error = True
                self._msg[field] = [['required_error']]
                if self._break_on_error:
                    break

        abort_if(self._error,{'msg': msg, 'errors': self._msg},422)

        return res

    def __check(self, input, rules):
        error=False
        msg=[]
        for rule in rules:
            if rule not in ['default']:
                name, args = type_rule(rule)
                test = getattr(__import__('renus.core.validation.rules', fromlist=['']), 'valid_' + name)({'input': input, 'args': args})
                if test != True:
                    error=True
                    msg.append(test)

        return True if error==False else msg


def type_rule(rule: str):
    arr = rule.split(':')
    name = arr[0]
    arr.pop(0)
    args = arr
    return [name, args]
