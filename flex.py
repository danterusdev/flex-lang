import sys

def tokenize(contents):
    tokens = []
    buffer = ""
    for character in contents:
        if character == ' ' or character == '\n':
            if buffer:
                tokens.append(buffer)
                buffer = ""
        else:
            buffer += character

    return tokens

def matches_token(tokens, index, macro_token):
    if tokens[index] == macro_token:
        return True

    for part in tokens[index].split('+'):
        if ':' in part:
            part_first = part[0 : part.index(':')]
            if part_first == macro_token:
                return True

    if macro_token[0] == "%":
        if ':' in macro_token:
            specifier = macro_token[macro_token.index(':') + 1 :]
            if specifier == "string":
                return tokens[index][0] == '"' and tokens[index][-1] == '"'
            elif specifier == "number":
                return tokens[index].isnumeric()
        else:
            return True

    return False

def matches_macro(tokens, index, definition):
    for macro_index, macro_token in enumerate(definition):
        if not matches_token(tokens, index + macro_index, macro_token):
            return False
    return True

def generate_binding(tokens, index, macro_token):
    bindings = {}

    if macro_token[0] == '%':
        if macro_token[-1] == ':':
            bindings[macro_token[0:-1]] = tokens[index] + ':'
        elif ':' in macro_token:
            bindings[macro_token[0 : macro_token.index(':')]] = tokens[index]
        else:
            bindings[macro_token] = tokens[index]

    return bindings

def generate_bindings(tokens, index, definition):
    bindings = {}

    for macro_index, macro_token in enumerate(definition):
        bindings.update(generate_binding(tokens, index + macro_index, macro_token))

    return bindings

def get_expansion(expansion, bindings):
    new_expansion = []
    for token in expansion:

        main_part = token
        if ':' in main_part:
            main_part = main_part[0 : main_part.index(':')]

        if main_part in bindings:
            new_expansion.append(token.replace(main_part, bindings[main_part]))
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
        elif token == "write_final":
            index += 1
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
                for definition_index, definition in enumerate(macro_definitions):
                    if matches_macro(tokens, index, definition):
                        bindings = generate_bindings(tokens, index, definition)
                        tokens = tokens[0 : index] + get_expansion(macro_expansions[definition_index], bindings) + tokens[index + len(definition):]

                        found = True
                        break

                if found:
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

    to_write = []

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
            elif token == "write_final":
                location = tokens[index]
                index += 2
                buffers_to_write = []
                while not tokens[index] == ")":
                    name = tokens[index].split(':')[0][1:]
                    buffers_to_write.append(name)
                    #buffers_to_write.append(int(tokens[index][1:]))
                    index += 1

                to_write.append((location, buffers_to_write))
                index += 1

    for to_adjust_small in to_adjust:
        for id, id2, extra, size, location in to_adjust_small:
            if extra == "final_location":
                buffer = buffers[id]
                buffer_bytes = int.from_bytes(buffer[location : location + size], "little")
                buffers[id] = buffer[0 : location] + (len(buffers[id2]) + buffer_bytes).to_bytes(size, "little") + buffer[location + size:]
    
    for to_write in to_write:
        file = open(to_write[0], "wb")
        for buffer in to_write[1]:
            file.write(buffers[buffer])
        file.close()
    
tokens = []
for file in sys.argv[1:]:
    contents = open(file, "r").read()
    tokens.extend(tokenize(contents))

tokens = parse(tokens)
finalize(tokens)
