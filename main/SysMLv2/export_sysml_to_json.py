import re
import json
from pathlib import Path
import sys

TOKEN_REGEX = r"""
    (?P<WHITESPACE>\s+)
  | (?P<COMMENT>//[^\n]*)
  | (?P<STRING>'[^']*'|"[^"]*")
  | (?P<NUMBER>-?\d+(\.\d+)?)
  | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*|\*|::)
  | (?P<LBRACE>\{)
  | (?P<RBRACE>\})
  | (?P<LBRACKET>\[)
  | (?P<RBRACKET>\])
  | (?P<COLON>:)
  | (?P<SEMICOLON>;)
  | (?P<EQUAL>=)
  | (?P<COMMA>,)
"""

token_re = re.compile(TOKEN_REGEX, re.VERBOSE)

def tokenize(text):
    for match in token_re.finditer(text):
        kind = match.lastgroup
        value = match.group()
        if kind in ("WHITESPACE", "COMMENT"):
            continue
        yield (kind, value)


KEYWORD_HEADS = {"package", "part", "attribute"}

KEYWORD_HEADS = {"package", "part", "attribute"}


class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return (None, None)

    def consume(self, kind=None):
        tok = self.peek()
        if kind and tok[0] != kind:
            raise SyntaxError(f"Expected {kind}, got {tok}")
        self.pos += 1
        return tok

    def parse(self):
        items = []
        while self.pos < len(self.tokens):
            stmt = self.parse_statement()
            if stmt is not None:
                items.append(stmt)
        return items

    def parse_statement(self):
        kind, value = self.peek()

        # consume stray closing braces at top level so we don't loop
        if kind == "RBRACE":
            self.consume("RBRACE")
            return None

        # attribute points : String;
        if kind == "IDENT" and value == "attribute":
            return self.parse_attribute_decl()

        # assignment: x = y;
        if kind == "IDENT" and self._lookahead("="):
            return self.parse_assignment()

        # typed declaration: x : Type;
        if kind == "IDENT" and self._lookahead(":"):
            return self.parse_typed_decl()

        # block-like construct: package, part, attribute
        if kind == "IDENT" and value in KEYWORD_HEADS and self._has_block_ahead():
            return self.parse_block_construct()

        # header-like (we won't rely on this much now)
        if kind == "IDENT" and value in {"private", "public", "import"}:
            return self.parse_header_statement()

        # fallback: generic statement
        return self.parse_generic_statement()

    # ---------- specific kinds ----------

    def parse_assignment(self):
        lhs = self.consume("IDENT")[1]
        self.consume("EQUAL")
        rhs = self.parse_value()
        if self.peek()[0] == "SEMICOLON":
            self.consume()
        return {"kind": "assignment", "lhs": lhs, "rhs": rhs}

    def parse_typed_decl(self):
        name = self.consume("IDENT")[1]
        self.consume("COLON")
        type_name = self.parse_type_name()
        if self.peek()[0] == "SEMICOLON":
            self.consume()
        return {"kind": "typedDecl", "name": name, "type": type_name}

    def parse_block_construct(self):
        # First IDENT is always part of the keyword (package/part/attribute)
        keywords = [self.consume("IDENT")[1]]

        # Optional extra keyword(s), e.g. "def" in "part def Mesh"
        while True:
            kind, value = self.peek()
            if kind != "IDENT":
                break
            # If the next token after this IDENT looks like a name boundary,
            # stop treating them as keyword pieces.
            next_kind, _ = self.peek(1)
            if next_kind in {"LBRACE", "COLON", "SEMICOLON", "STRING"}:
                break
            keywords.append(self.consume("IDENT")[1])

        keyword_str = " ".join(keywords)

        # name can be IDENT or STRING (package 'Oxygen Tank for Habitation')
        name_kind, name_val = self.peek()
        name = None
        if name_kind in ("IDENT", "STRING"):
            name_tok = self.consume()
            name = name_tok[1].strip("'\"") if name_kind == "STRING" else name_tok[1]

        # optional type: name : Type
        type_name = None
        if self.peek()[0] == "COLON":
            self.consume("COLON")
            type_name = self.parse_type_name()

        body = None
        if self.peek()[0] == "LBRACE":
            body = self.parse_block()

        node = {"kind": "construct", "keyword": keyword_str, "name": name}
        if type_name:
            node["type"] = type_name
        if body is not None:
            node["body"] = body
        return node

    def parse_block(self):
        self.consume("LBRACE")
        items = []
        while self.peek()[0] not in ("RBRACE", None):
            stmt = self.parse_statement()
            if stmt is not None:
                items.append(stmt)
        self.consume("RBRACE")
        return items

    def parse_header_statement(self):
        # e.g. 'private import SysML::*;'
        tokens = []
        while self.peek()[0] not in ("SEMICOLON", None, "RBRACE"):
            tokens.append(self.consume()[1])
        if self.peek()[0] == "SEMICOLON":
            self.consume()
        return {"kind": "statement", "tokens": tokens}

    def parse_generic_statement(self):
        tokens = []
        while self.peek()[0] not in ("SEMICOLON", None, "RBRACE"):
            tokens.append(self.consume()[1])
        if self.peek()[0] == "SEMICOLON":
            self.consume()
        return {"kind": "statement", "tokens": tokens}

    def parse_attribute_decl(self):
        self.consume("IDENT")  # 'attribute'
        name = self.consume("IDENT")[1]

        type_name = None
        if self.peek()[0] == "COLON":
            self.consume("COLON")
            type_name = self.parse_type_name()

        if self.peek()[0] == "SEMICOLON":
            self.consume()

        return {
            "kind": "construct",
            "keyword": "attribute",
            "name": name,
            "type": type_name
        }

    # ---------- values, lists, types ----------

    def parse_value(self):
        kind, value = self.peek()

        if kind == "STRING":
            return self.consume()[1].strip('"\'')

        if kind == "NUMBER":
            num = self.consume()[1]
            return float(num) if "." in num else int(num)

        if kind == "IDENT":
            return self.consume()[1]

        if kind == "LBRACKET":
            return self.parse_list()

        return self.consume()[1]

    def parse_list(self):
        self.consume("LBRACKET")
        items = []
        while self.peek()[0] not in ("RBRACKET", None):
            items.append(self.parse_value())
            if self.peek()[0] == "COMMA":
                self.consume()
        self.consume("RBRACKET")
        return items

    def parse_type_name(self):
        parts = []
        while True:
            kind, value = self.peek()
            if kind not in ("IDENT", "COLON"):
                break
            parts.append(self.consume()[1])
        return "".join(parts)

    # ---------- helpers ----------

    def _lookahead(self, symbol, offset=1):
        return self.peek(offset)[1] == symbol

    def _has_block_ahead(self):
        """
        Look ahead for a '{' before a ';'.
        This lets 'package ... { ... }' and 'part ... { ... }' be block constructs.
        """
        i = 1
        while True:
            kind, val = self.peek(i)
            if kind is None:
                return False
            if kind == "LBRACE":
                return True
            if kind == "SEMICOLON":
                return False
            i += 1

def remove_imports(ast):
    filtered = []
    for node in ast:
        if isinstance(node, dict):
            # Remove statements that look like imports
            if node.get("kind") == "statement":
                tokens = node.get("tokens", [])
                if tokens and tokens[0] in ("import", "private", "public"):
                    # crude but effective: drop "private import ...", "import ...", etc.
                    if "import" in tokens[:3]:
                        continue

            # Recurse into bodies
            if "body" in node and isinstance(node["body"], list):
                node["body"] = remove_imports(node["body"])

        filtered.append(node)
    return filtered

def parse_sysml_to_json(input_path: str, output_path: str):
    text = Path(input_path).read_text(encoding="utf-8")
    tokens = tokenize(text)
    parser = Parser(tokens)
    ast = parser.parse()
    ast = remove_imports(ast)
    Path(output_path).write_text(json.dumps(ast, indent=2), encoding="utf-8")
    print(f"Parsed {input_path} → {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python export_sysml_to_json.py <input.sysml> <output.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    parse_sysml_to_json(input_file, output_file)