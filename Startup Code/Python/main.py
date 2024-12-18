from __future__ import annotations
from lexer import Lexer, Token
from parser import Parser, SLRParserTable
import sys
import json

# sys.setrecursionlimit(1999999999)
# WARNING:
# - You are not allowed to use any external libraries other than the standard library
# - Please do not modify the file name of the entry file 'main.py'
# - Our autograder will test your code by runing 'python main.py <test_file>'
#   The current directory will be the same directory as the entry file
#   So please make sure your import statement is correct

def write_json_output(data, file_name):
    with open(file_name, 'w') as f:
                f.write(data)

def update_token_type(parse_tree: dict | list):
    # raise ValueError("Invalid parse tree format")
    """
    Traverse the parse tree and update the token_type of nodes where
    lexeme is 'simplify' but token_type is 'show'.
    """
    try:
        if isinstance(parse_tree, dict):
            if "token" in parse_tree and "lexeme" in parse_tree:
                if parse_tree["lexeme"] == "simplify" and parse_tree["token"] == "show":
                    parse_tree["token"] = "simplify"
            if "children" in parse_tree:
                for child in parse_tree["children"]:
                    update_token_type(child)
        elif isinstance(parse_tree, list):
            for item in parse_tree:
                update_token_type(item)
    except KeyError:
        raise ValueError("Invalid parse tree format")

def non_recursive_json_dump(data, file_path):
    try:
        stack = [(data, {})]
        while stack:
            obj, result = stack.pop()
            for key, value in obj.items():
                if isinstance(value, dict):
                    new_dict = {}
                    result[key] = new_dict
                    stack.append((value, new_dict))
                else:
                    result[key] = value
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        # print(f"Error: {e}")
        ...


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python main.py <test_file>")
        sys.exit(1)
    file_name = sys.argv[1]
    with open(file_name, 'r') as f:
        # read file to string
        source_code = f.read()
        file_path = 'SLR Parsing Table.csv'
        grammar_path = 'SLR Grammar.txt'
        lexer = Lexer(source_code)
        tokens,symbol_table = lexer.tokenize()
        lexer_ouput = [token.to_dict() for token in tokens]
        with open("lexer_out.json", "w", encoding="utf-8") as f:
            json.dump(lexer_ouput, f, ensure_ascii=False, indent=0)
        tokens.append(Token(token_type="$",lexeme="$",value="$"))
        slr_table = SLRParserTable(file_path, grammar_path)
        actions,goto,rules=slr_table.ACTION,slr_table.GOTO,slr_table.grammar
        simplified_rules = {}
        for rule_number, details in rules.items():
            simplified_rules[rule_number] = (details['non-terminal'], details['length'])
        # parser=Parser(tokens,actions, goto, rules, symbol_table)
        parser=Parser(tokens,actions, goto, rules)
        parse_tree=parser.parse()
        with open("parser_out.json", "w", encoding="utf-8") as f:
            json.dump(parse_tree, f, ensure_ascii=False, indent=0)
        typeing_tree =parser.typecheck()
        with open("typing_out.json", "w", encoding="utf-8") as f:
            json.dump(typeing_tree, f, ensure_ascii=False, indent=0)

