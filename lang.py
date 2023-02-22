import sys
from enum import Enum

def tokenize(contents):
    tokens = []

    in_brackets = False
    buffer = ""
    for character in contents + '\n':
        if character == '[':
            in_brackets = True
        elif character == ']':
            in_brackets = False

        if (character == ' ' or character == '\n') and not in_brackets:
            if buffer:
                tokens.append(get_token_data(buffer))
                buffer = ""
            continue
        
        buffer += character

    return tokens

def get_token_data(token):
    if ':' in token:
        colon_index = token.index(':')
    else:
        colon_index = len(token)

    if token.startswith("["):
        return (token[1 : colon_index - 1], token[colon_index + 1:])
    else:
        return (token[0 : colon_index], token[colon_index + 1:])

def is_empty(token):
    return token[0] == "" and token[1] == ""

def equal(token1, token2):
    return token1[0] == token2[0] and token1[1] == token2[1]

# returns an integer which are the number of tokens that are consumed
# only works for one repeat group, possible improved in the future?
def matches(macro_start, macro_end, start, tokens, tokens_old):
    macro_index = macro_start
    token_index = start

    repeat_group = False
    start_repeat_group = -1

    bindings = {}

    while macro_index < macro_end:
        macro_token = tokens_old[macro_index]

        if token_index >= len(tokens):
            return -1, None

        if macro_token[0].startswith("%"):
            if tokens[token_index][1] == macro_token[1]:
                id = macro_token[0][1:]
                if not id in bindings:
                    bindings[id] = []
                bindings[id].append(tokens[token_index][0])
                token_index += 1
                macro_index += 1
            else:
                return -1, None
        elif macro_token[1] == "...":
            if start_repeat_group == -1:
                start_repeat_group = macro_index - 1

            next_macro_token = tokens_old[macro_index + 1]
            
            if equal(next_macro_token, tokens[token_index]):
                macro_index += 1
                continue
            
            macro_index = start_repeat_group
        elif macro_token[1] == "|":
            repeat_group = True
            start_repeat_group = macro_index + 1
            macro_index += 1
        else:
            if tokens[token_index][0] == macro_token[0] and tokens[token_index][1] == macro_token[1]:
                token_index += 1
                macro_index += 1
            else:
                return -1, None

    return token_index - start, bindings

def expand_macro(tokens, macro_start, macro_end, bindings):
    expanded = []
    location = macro_start

    start_repeat = -1
    repeat_count = 0
    repeat_max_count = -1

    while location < macro_end:
        token = tokens[location]

        if token[0] and token[0][0] == '%':
            expanded.append((bindings[token[0][1:]][repeat_count], tokens[location][1]))
            if not start_repeat == -1:
                repeat_max_count = len(bindings[token[0][1:]])
            location += 1
        elif token[1] == "(":
            start_repeat = location + 1
            location += 1
        elif token[1] == ")":
            repeat_count += 1

            if repeat_count == repeat_max_count:
                location += 1
                start_repeat = -1
                repeat_count = 0
                continue

            location = start_repeat
        else:
            expanded.append(tokens[location])
            location += 1

    return expanded

def expand_macros(tokens):
    macros = []

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token[1] == "macro":
            i += 1

            start_match = i
            while not is_empty(tokens[i]):
                i += 1

            end_match = i

            i += 1

            start_replace = i
            while not is_empty(tokens[i]):
                i += 1

            end_replace = i

            macros.append(((start_match, end_match), (start_replace, end_replace)))

            i += 1
        else:
            i += 1

    tokens_new = tokens

    i = 0
    while i < len(tokens_new):
        token = tokens_new[i]
        if token[1] == "macro":
            i += 1

            while not is_empty(tokens_new[i]):
                i += 1

            i += 1
            while not is_empty(tokens_new[i]):
                i += 1

            i += 1
        else:
            matched = False
            for macro in macros:
                amount, bindings = matches(macro[0][0], macro[0][1], i, tokens_new, tokens)
                if amount > 0:
                    tokens_new = tokens_new[0 : i] + expand_macro(tokens, macro[1][0], macro[1][1], bindings) + tokens_new[i + amount :]
                    i = 0
                    matched = True
                    break
                
            if not matched:
                i += 1

    return tokens_new

def strip_macros(tokens):
    tokens_new = []

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token[1] == "macro":
            i += 1

            while not is_empty(tokens[i]):
                i += 1

            i += 1

            while not is_empty(tokens[i]):
                i += 1

            i += 1
        else:
            tokens_new.append(token)
            i += 1

    return tokens_new

def get_buffer(buffers, id):
    if not id in buffers:
        buffers[id] = bytearray()
    
    return buffers[id]

def get_map(maps, id):
    if not id in maps:
        maps[id] = {}
    
    return maps[id]

class State:
    def __init__(self):
        self.buffers = {}
        self.maps = {}

def get_buffer_length(previous_states, id):
    max_length = 0
    for state in previous_states:
        if id in state.buffers:
            max_length = max(max_length, len(state.buffers[id]))
    
    return max_length

def evaluate(tokens, state, previous_states, pass_value):
    stack = []
    max_pass = 0

    for token in tokens:
        if token[1].startswith("#"):
            value = token[0]
            operation = token[1][1:]

            accepts_all_passes = False
            if ";" in operation:
                wanted_pass = int(operation[operation.index(";") + 1:])
                is_right_pass = pass_value == wanted_pass
                operation = operation[0 : operation.index(";")]

                if wanted_pass > max_pass:
                    max_pass = wanted_pass
            else:
                is_right_pass = True
                accepts_all_passes = True

            if operation == "number":
                # maybe in the future the default should be only for one pass, for now just throwing a warning
                if accepts_all_passes:
                    print("Number '" + str(value) + "', applied in all passes, probably an error.")

                if is_right_pass:
                    stack.append(int(value))
                else:
                    stack.append(0)
            elif operation == "string":
                if is_right_pass:
                    stack.append(value)
                else:
                    stack.append("\0" * len(value))
            elif operation.startswith("buffer_"):
                buffer_operation = operation[7:]
                buffer = get_buffer(state.buffers, value)

                if buffer_operation.startswith("location"):
                    if is_right_pass:
                        stack.append(max(get_buffer_length(previous_states, value), len(buffer)))
                    else:
                        stack.append(0)
                elif buffer_operation.startswith("push_number_"):
                    popped = stack.pop()
                    size = int(buffer_operation[12:])
                    buffer.extend(popped.to_bytes(size, "little"))
                elif buffer_operation.startswith("push_string"):
                    popped = stack.pop()
                    buffer.extend(bytes(popped, "utf-8"))
                elif buffer_operation.startswith("contents"):
                    state_temp = state
                    for previous_state in previous_states:
                        state_temp = combine(previous_state, state_temp)

                    stack.append(state_temp.buffers[value])
                else:
                    print("Unknown buffer operation '" + buffer_operation + "'")
            elif operation.startswith("map_"):
                map_operation = operation[4:]
                map = get_map(state.maps, value)

                if map_operation.startswith("put"):
                    key = stack.pop()
                    value = stack.pop()
                    if is_right_pass:
                        map[key] = value
                    else:
                        pass
                elif map_operation.startswith("get_number"):
                    key = stack.pop()

                    state_temp = state
                    for previous_state in previous_states:
                        state_temp = combine(previous_state, state_temp)

                    if is_right_pass:
                        stack.append(state_temp.maps[value][key])
                    else:
                        stack.append(0)
                else:
                    print("Unknown map operation '" + map_operation + "'")
            elif operation.startswith("+"):
                amount = int(operation[1:])
                value = 0
                for _ in range(amount):
                    value += stack.pop()
                
                stack.append(value)
            elif operation.startswith("write_"):
                file = stack.pop()
                if is_right_pass:
                    file = open(file, "wb")

                count = int(operation[6:])
                
                for _ in range(0, count):
                    popped = stack.pop()
                    if is_right_pass:
                        file.write(popped)
                
                if is_right_pass:
                    file.close()
            else:
                print("Unknown operation '" + operation + "'")
    
    return max_pass

def combine(state1, state2):
    buffers1 = state1.buffers
    buffers2 = state2.buffers

    maps1 = state1.maps
    maps2 = state2.maps

    state = State()
    buffers = state.buffers

    for key in buffers1.keys():
        buffers[key] = bytearray()
        for i in range(max(len(buffers1[key]) if key in buffers1 else 0, len(buffers2[key]) if key in buffers2 else 0)):
            state1_value = buffers1[key][i] if key in buffers1 and i < len(buffers1[key]) else 0
            state2_value = buffers2[key][i] if key in buffers2 and i < len(buffers2[key]) else 0
            buffers[key].append(state1_value + state2_value)
    
    maps = state.maps
    for key in maps1.keys():
        if not key in maps:
            maps[key] = {}
        
        for key2, value in maps1[key].items():
            maps[key][key2] = value

    for key in maps2.keys():
        if not key in maps:
            maps[key] = {}
        
        for key2, value in maps2[key].items():
            maps[key][key2] = value
    
    return state

input_files = sys.argv[1:]
tokens = []
for input in input_files:
    tokens.extend(tokenize(open(input).read()))

tokens = expand_macros(tokens)
tokens = strip_macros(tokens)

previous_states = []
max_pass = 0

i = 0
while i <= max_pass:
    state = State()

    max_pass = evaluate(tokens, state, previous_states, i)
    previous_states.append(state)
    i += 1