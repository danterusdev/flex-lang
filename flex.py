import sys

def tokenize(contents):
    tokens = []
    buffer = ""
    in_string = False
    for character in contents:
        if (character == ' ' or character == '\n') and not in_string:
            if buffer:
                tokens.append(buffer)
                buffer = ""
        else:
            buffer += character

        if character == '"':
            in_string = not in_string

    return tokens

def matches_token(tokens, index, macro_index, definition):
    macro_token = definition[macro_index]
    if tokens[index] == macro_token:
        return True, index + 1

    if macro_token == "((" and tokens[index] == "(":
        return True, index + 1
    if macro_token == "))" and tokens[index] == ")":
        return True, index + 1

    for part in tokens[index].split('+'):
        if ':' in part:
            part_first = part[0 : part.index(':')]
            if part_first == macro_token:
                return True, index + 1

    if macro_token[0] == "%":
        if ':' in macro_token:
            specifier = macro_token[macro_token.index(':') + 1 :]
            if specifier == "string":
                return tokens[index][0] == '"' and tokens[index][-1] == '"', index + 1
            elif specifier == "number":
                return tokens[index].isnumeric(), index + 1
            elif specifier == "[]":
                return tokens[index][0] == '[' and tokens[index][-1] == ']', index + 1
        elif macro_token.endswith(".."):
            matches = False
            while not matches:
                matches, _ = matches_token(tokens, index, macro_index + 1, definition)
                index += 1

            return True, index - 1
        else:
            return True, index + 1

    return False, index + 1

flag = False

def matches_macro(tokens, index, definition):
    global flag

    index_initial = index
    macro_index = 0
    while macro_index < len(definition):
        matches, index = matches_token(tokens, index, macro_index, definition)
        if not matches:
            return False, 0

        macro_index += 1

    return True, index - index_initial

def generate_binding(tokens, index, macro_index, definition):
    macro_token = definition[macro_index]
    bindings = {}

    if macro_token[0] == '%':
        if macro_token[-1] == ':':
            bindings[macro_token[0:-1]] = tokens[index] + ':'
        elif ':' in macro_token:
            bindings[macro_token[0 : macro_token.index(':')]] = tokens[index]
        elif macro_token.endswith(".."):
            new_binding = []
            while True:
                new_binding.append(tokens[index])
                matches, index = matches_token(tokens, index, macro_index + 1, definition)

                if matches:
                    break
            new_binding.pop()
            bindings[macro_token[0:-2]] = new_binding
        else:
            bindings[macro_token] = tokens[index]

    return bindings, index + 1

def generate_bindings(tokens, index, definition):
    bindings = {}

    for macro_index in range(len(definition)):
        bindings_new, index = generate_binding(tokens, index, macro_index, definition)
        bindings.update(bindings_new)

    return bindings

def is_str_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def get_expansion(expansion, bindings):
    new_expansion = []
    for token in expansion:

        main_part = token
        if ':' in main_part:
            main_part = main_part[0 : main_part.index(':')]

        if main_part in bindings:
            if token in bindings:
                if isinstance(bindings[main_part], list):
                    new_expansion.extend(bindings[main_part])
                else:
                    new_expansion.append(bindings[main_part])
            elif ':' in token and is_str_int(token[token.index(':') + 1:]):
                new_expansion.append(token.replace(main_part, bindings[main_part]))
            elif token[-1] == ':':
                new_expansion.append(token.replace(main_part, bindings[main_part]))
            else:
                print(token)
        elif token[0] == '\\':
            new_expansion.append(token[1:])
        else:
            new_expansion.append(token)

    return new_expansion

def parse(tokens):
    macro_definitions = []
    macro_expansions = []

    alias_definitions = {}

    for index, token in enumerate(tokens):
        if token == "macro":
            temp_definition = []
            i = index + 1
            while not tokens[i] == "(":
                temp_definition.append(tokens[i])
                i += 1

            temp_expansion = []
            i += 1
            inside_count = 1
            while True:
                if tokens[i] == "(":
                    inside_count += 1
                elif tokens[i] == ")":
                    inside_count -= 1
                    if inside_count == 0:
                        break

                temp_expansion.append(tokens[i])
                i += 1

            macro_definitions.append(temp_definition)
            macro_expansions.append(temp_expansion)
        elif token == "alias":
            alias_definitions[tokens[index + 1]] = tokens[index + 2]

    in_macro_count = 0
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "macro":
            index += 1
            while not tokens[index] == "(":
                index += 1

            index += 1
            in_macro_count += 1
        elif token == "alias":
            index += 3
        elif token == "(":
            if in_macro_count > 0:
                in_macro_count += 1
            index += 1
        elif token == ")":
            if in_macro_count > 0:
                in_macro_count -= 1
            index += 1
        else:
            if in_macro_count == 0:
                found = False

                expansions = []
                max_matched = 0

                for definition_index, definition in enumerate(macro_definitions):
                    matches, size = matches_macro(tokens, index, definition)
                    if matches:
                        bindings = generate_bindings(tokens, index, definition)
                        expansions.extend(get_expansion(macro_expansions[definition_index], bindings))
                        max_matched = max(max_matched, size)

                        found = True

                if found:
                    tokens = tokens[0 : index] + expansions + tokens[index + max_matched:]
                    index = 0
                    continue

            index += 1

    for index, token in enumerate(tokens):
        for original, alias in alias_definitions.items():
            tokens[index] = tokens[index].replace(original, alias)

    return tokens

def finalize(tokens):
    to_adjust = []

    buffers = {}
    stacks = {}
    maps = {}

    final_tokens = []

    in_macro_count = 0
    index = 0
    while index < len(tokens):
        token = tokens[index]
        old_in_macro_count = in_macro_count
        if token == "macro":
            index += 1
            while not tokens[index] == "(":
                index += 1

            index += 1
            in_macro_count += 1
        elif token == "alias":
            index += 3
        elif token == "(":
            if in_macro_count > 0:
                in_macro_count += 1
            index += 1
        elif token == ")":
            if in_macro_count > 0:
                in_macro_count -= 1
            index += 1
        else:
            index += 1
        
        if in_macro_count == 0 and old_in_macro_count == 0:
            if token[0] == '$' and token.endswith(":buffer:push"):
                id = token.split(':')[0][1:]
                if not id in buffers:
                    buffers[id] = b''

                index += 1

                while not tokens[index] == ')':
                    try:
                        size = int(tokens[index][tokens[index].rindex(':') + 1])
                    except ValueError:
                        size = 0
                    except IndexError:
                        size = 0

                    value = 0
                    to_adjust_temp = []

                    thing = tokens[index]
                    if thing[-2] == ':':
                        thing = thing[0:-2]

                    for statement in thing.split('+'):
                        if not statement[0] == '$' and not statement[0] == '"':
                            value += int(statement)
                        elif tokens[index][0] == '"':
                            buffers[id] += bytes(tokens[index][1: -2], "utf-8")
                        elif statement[0] == '$' and ':' in statement:
                            id2 = statement.split(':')[0][1:]
                            extra = statement[statement.rindex(':') + 1 : ]

                            if not id2 in buffers:
                                buffers[id2] = b''

                            if extra == "location":
                                value += len(buffers[id2])
                            else:
                                to_adjust_temp.append((id, id2, extra, size, len(buffers[id])))

                    to_adjust.append(to_adjust_temp)

                    if size > 0:
                        buffers[id] += value.to_bytes(size, "little")

                    index += 1

                index += 1
            elif token[0] == '$' and token.endswith(":map:insert"):
                id = token.split(':')[0][1:]
                if not id in maps:
                    maps[id] = {}

                index += 1
                maps[id][tokens[index]] = tokens[index + 1]

                index += 3
            elif token[0] == '$' and token.endswith(":stack:push"):
                id = token.split(':')[0][1:]
                if not id in stacks:
                    stacks[id] = []

                index += 1
                while not tokens[index] == ")":
                    stacks[id].append(tokens[index])
                    index += 1

                index += 1
            elif token[0] == '$' and token.endswith(":stack:pop_check"):
                id = token.split(':')[0][1:]
                if not id in stacks:
                    stacks[id] = []

                failed = False

                index += 1
                while not tokens[index] == ")":
                    if tokens[index][0] == '"':
                        if failed:
                            print(tokens[index][1:-2])
                    else:
                        popped = stacks[id].pop()
                        if popped != tokens[index]:
                            failed = True
                    index += 1

                index += 1
            elif token == "final":
                location = tokens[index]
                index += 1
                inside = 1
                while inside > 0:
                    final_tokens.append(tokens[index])
                    index += 1

                    if tokens[index] == '(':
                        inside += 1
                    elif tokens[index] == ')':
                        inside -= 1

                index += 1

    for to_adjust_small in to_adjust:
        for id, id2, extra, size, location in to_adjust_small:
            if extra == "final_location":
                buffer = buffers[id]
                buffer_bytes = int.from_bytes(buffer[location : location + size], "little")
                buffers[id] = buffer[0 : location] + (len(buffers[id2]) + buffer_bytes).to_bytes(size, "little") + buffer[location + size:]

    index = 0
    while index < len(final_tokens):
        if final_tokens[index] == "write":
            output_file = final_tokens[index + 1]
            index += 3
            file = open(output_file, "wb")
            while not final_tokens[index] == ")":
                file.write(buffers[final_tokens[index].split(':')[0][1:]])
                index += 1

            file.close()
            index += 1
        else:
            index += 1

    print(maps)
    
tokens = []
for file in sys.argv[1:]:
    contents = open(file, "r").read()
    tokens.extend(tokenize(contents))

tokens = parse(tokens)
print(tokens)
finalize(tokens)
