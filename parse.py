import json

class ParseException(Exception):
    def __init__(self, message, parsed, unparsed):
        self.message = message
        self.parsed = parsed
        self.unparsed = unparsed

class StringParseException(ParseException):
    def __init__(self, message, parsed, unparsed, string, err):
        super().__init__(message, parsed, unparsed)
        self.string = string
        self.err = err

# use .parse() or .capture_parse() (just a wrapper around parse() that returns the exception instead in the event that it fails)
class Parser:
    def __init__(self, string):
        self.string = string
        self.len = len(self.string)

    def throw(self, msg, pos):
        raise ParseException(msg, self.string[:pos], self.string[pos:])

    def parse(self):
        val, _ = self.parse_value(0)
        return val

    def capture_parse(self):
        try:
            return self.parse()
        except Exception as e:
            return e

    def parse_string(self, pos):
        escaped = False
        start = pos
        while True:
            pos += 1
            if pos >= self.len:
                self.throw("EOF reached before string ended", start)
            c = self.string[pos]
            if not escaped and c == '"':
                break
            if c == '\\':
                escaped = not escaped
            else:
                escaped = False
        string = self.string[start:pos + 1]
        try:
            string = json.loads(string)
        except Exception as err:
            raise StringParseException("failed to parse string", self.string[:start], self.string[start:], string, err)
        return string, pos

    # starts with "-0123456789". "cannot" start with 0 if following character isn't a "." or "e"
    def parse_number(self, pos):
        start = pos
        parse_func = int
        if self.string[pos] == '-' and (pos == self.len - 1 or self.string[pos + 1] not in '0123456789'):
            self.throw("invalid numeric value", start)
        while True:
            pos += 1
            if pos >= self.len:
                break
            c = self.string[pos]
            if c not in "0123456789":
                break
        if c == '.':
            parse_func = float
            deci_start = pos
            while True:
                pos += 1
                if pos >= self.len:
                    break
                c = self.string[pos]
                if c not in "0123456789":
                    break
            if pos == deci_start + 1:
                self.throw("invalid numeric value", start)
        if c in "eE":
            parse_func = float
            if pos == self.len - 1:
                self.throw("invalid numeric value", start)
            if self.string[pos + 1] in "-+":
                pos += 1
            expo_start = pos
            while True:
                pos += 1
                if pos >= self.len:
                    break
                c = self.string[pos]
                if c not in "0123456789":
                    break
            if pos == expo_start + 1:
                self.throw("invalid numeric value", start)
        if c not in "0123456789,]}" and not c.isspace():
            self.throw("Number parse error", start)
        if self.string[start] == "0" and self.string[start + 1] not in ".eE" and pos - start > 1:
            self.throw("Leading zero found in number parse", start)
        return parse_func(self.string[start:pos]), pos - 1

    def parse_literal(self, pos):
        start = pos
        while True:
            c = self.string[pos]
            if c in ",]}" or c.isspace():
                break
            if not c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                self.throw("Literal parse error", start)
            pos += 1
        token = self.string[start:pos]
        if not token in ["false", "true", "null"]:
            self.throw('Invalid literal: "{}"'.format(token), start)
        pos -= 1
        if token == "false":
            return False, pos
        if token == "true":
            return True, pos
        return None, pos

    def parse_value(self, pos):
        start = pos
        while True:
            if pos >= self.len:
                self.throw("EOF reached while trying to find value", start)
            c = self.string[pos]
            if not c.isspace():
                break
            pos += 1
        if c in "-0123456789":
            return self.parse_number(pos)
        if c == '"':
            return self.parse_string(pos)
        if c == '[':
            return self.parse_array(pos)
        if c == '{':
            return self.parse_object(pos)
        return self.parse_literal(pos)

    def parse_object(self, pos):
        start = pos
        obj = {}
        while True:
            pos += 1
            if pos >= self.len:
                self.throw("EOF reached while parsing object", start)
            c = self.string[pos]
            if c.isspace():
                continue
            if c == '}':
                break
            if c == '"':
                member_start = pos
                key, pos = self.parse_string(pos)
                while True:
                    pos += 1
                    if pos >= self.len:
                        self.throw("EOF reached while parsing object member", member_start)
                    c = self.string[pos]
                    if c.isspace():
                        continue
                    break
                if c != ':':
                    self.throw("member-separator (i.e, colon) not found when parsing object member", pos)
                value, pos = self.parse_value(pos + 1)
                obj[key] = value
                member_end = pos
                while True:
                    pos += 1
                    if pos >= self.len:
                        self.throw("EOF reached while searching for next object member", member_end)
                    c = self.string[pos]
                    if c.isspace():
                        continue
                    break
                if c not in ',}':
                    self.throw("Invalid character found while searching for next object member", pos)
                if c == '}':
                    break
            else:
                self.throw("Invalid character found while searching for object member key", pos)
        return obj, pos

    def parse_array(self, pos):
        start = pos
        array = []
        while True:
            pos += 1
            if pos >= self.len:
                self.throw("EOF reached while parsing array", start)
            c = self.string[pos]
            if c.isspace():
                continue
            if c == ']':
                break
            value, pos = self.parse_value(pos)
            array.append(value)
            value_end = pos
            while True:
                pos += 1
                if pos >= self.len:
                    self.throw("EOF reached while searching for next array value", value_end)
                c = self.string[pos]
                if c.isspace():
                    continue
                break
            if c not in ',]':
                self.throw("Invalid character found while searching for next array value", pos)
            if c == ']':
                break
        return array, pos
