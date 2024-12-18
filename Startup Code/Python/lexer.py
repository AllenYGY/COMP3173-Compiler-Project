from __future__ import annotations
class Token:
    # Your implementation
    def __init__(self, token_type: str, lexeme: str, value=None):
        """
        Initialize a token.
        """
        self.token_type = token_type
        self.lexeme = lexeme
        self.value = value

    def to_dict(self):
        """
        Convert the token to a dictionary format for JSON output.
        """
        return {"token": self.token_type, "lexeme": self.lexeme}

class Lexer:
    # Your implementation
    # This is only an example, you can modify it as you like
    KEYWORDS = {"let", "be", "show", "int", "set","simplify"}
    PUNCTUATIONS = {".", "(", ")", "{", "}", ":"}
    OPERATORS = {"+", "-", "*", "@", "<", ">","=", "&", "|", "!", "U", "I"}
    WHITESPACE = {" ","\n","\t"}  # Space is treated as a special character

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.position = 0  # Current position in the source code
        self.symbol_table = {}  # Symbol table for variable names

    def next_token(self) -> Token:
        """
        Reads the next token from the input and returns it based on its type.
        - If the token is 'num', returns the token and its value.
        - If the token is 'id', stores the variable in the symbol table and returns its location.
        - For other tokens, only returns the token itself.
        """
        while self.position < len(self.source_code):
            char = self.source_code[self.position]

            if char in self.WHITESPACE: # Skip whitespace or newline
                self.position += 1
                continue

            # Check if the character is a valid token
            if char in self.OPERATORS or char in self.PUNCTUATIONS or char.isalpha() or char.isdigit():
                # * Process single-character tokens
                if char in self.PUNCTUATIONS or char in self.OPERATORS: # punctuation or operator 
                    token = Token(token_type=char, lexeme=char)
                    self.position += 1
                    return token, None
                if char.isupper(): # Uppercase character
                    raise ValueError(f"Lexical Error: Invalid character '{char}' at position {self.position}")
                # * Process multi-character tokens
                if char.isalpha(): 
                    token = self._process_identifier_or_keyword()  # identifier or keyword
                    if token.token_type == "id":
                        # Store variable in the symbol table
                        if token.lexeme not in self.symbol_table:
                            self.symbol_table[token.lexeme] = {
                                "type": None, "value": None}
                        return token, self.symbol_table[token.lexeme]
                    return token, None
                elif char.isdigit():  # number
                    token = self._process_number()
                    return token, token.value
                else:
                    raise ValueError(f"Lexical Error: Unrecognized character '{char}' at position {self.position}")
            else:
                raise ValueError(f"Lexical Error: Invalid character '{char}' at position {self.position}")

        return None, None  # End of input

    def _process_identifier_or_keyword(self) -> Token:
        """
        Process an identifier or a keyword.
        :return: Token representing an identifier or a keyword.
        """
        start_pos = self.position # Start position of the lexeme 
        # Continue reading characters while the lexeme is alphanumeric and lowercase
        while self.position < len(self.source_code) and self.source_code[self.position].isalpha() and self.source_code[self.position].islower():
            self.position += 1

        # Extract the lexeme
        lexeme = self.source_code[start_pos:self.position]

        # Check if the lexeme is a keyword
        if lexeme in self.KEYWORDS:
            return Token(token_type=lexeme, lexeme=lexeme)

        elif lexeme.isalpha():  # Only contains alphabetic characters
            return Token(token_type="id", lexeme=lexeme)
        # Invalid identifier
        else:
            raise ValueError(f"Lexical Error: Invalid identifier '{lexeme}'")

    def _process_number(self) -> Token:
        """
        Process a number.
        :return: Token representing a number.
        """
        start_pos = self.position
        # Check for leading zero
        if self.source_code[self.position] == '0':
            self.position += 1
            # If there's another digit after the leading zero, split it
            if self.position < len(self.source_code) and self.source_code[self.position].isdigit():
                return Token(token_type="num", lexeme="0", value=0)
        # Process digits until a non-digit is encountered
        while self.position < len(self.source_code) and self.source_code[self.position].isdigit():
            self.position += 1
        # Extract the lexeme
        lexeme = self.source_code[start_pos:self.position]
        # Convert to integer and validate range
        try:
            value = int(lexeme)
            if not (0 <= value <= 4294967295):
                raise ValueError(f"Lexical Error: Number {value} out of range at position {start_pos}")
        except ValueError:
            raise ValueError(f"Lexical Error: Invalid number {lexeme} at position {start_pos}")

        return Token(token_type="num", lexeme=lexeme, value=value)


    def tokenize(self) -> list[Token]:
        """
        Tokenize the entire source code. If an error occurs, stop parsing and return an empty list.
        :return: List of tokens or an empty list if an error occurs.
        """
        try:
            tokens = []
            while True:
                token, _ = self.next_token()
                if token is None:
                    break
                tokens.append(token)
            print("Lexical Analysis Complete!") # Lexical Analysis Complete!
        except ValueError as e:
            # print(e)
            print("Lexical Error!")
            tokens = []
        return tokens, self.symbol_table


if __name__ == '__main__':


    test_cases = {
        1: "let int x be 5.\n let set s be { x : x > 3 }. show x @ s.",
        2: "is a test string.",
        3: "let y be 10. show y + 20.",
        4: "let invalidvar be 5.",  
        5: "show123+x+456.",
        6: "let set s be {a:a=3|a=4}.",
        7: "let int id be xx .",
        8: "show z I y."
    }

    example_cases = {
        1: "show 3 .",
        2: '''
            let int x be 3 .
            show x + 1 .
            ''',
        3: '''
            let int x be 3 .
            let int y be 4 .
            let set s be {a:a=3|a=4}.
            show x @ s .
            ''',
        4: '''
            let set x be {a:a>3} .
            let set y be {a:a<5} .
            show x I y.
            ''',
        5: '''
            let set x be {a:a>3} .
            let set y be {a:a<5 & a @ x} .
            let set z be {a:a>0}.
            show z I y.
            ''',
        6: '''
            This is a lexical error.
           ''',
        7:  '''
            this is a syntax error.
            ''',
        8:  '''
            let set x be 4.
            let set y be 4.
            show x @ y.            
            ''',
        9:  " show 3 < 5 & 2 > 4 ."
    }

    # source_code = example_cases[3]
    source_code = test_cases[5]
    source_code = "10000000000"
    source_code ="let be show int set"
    source_code ="0999999999"
    source_code ="show s1 U s2 ."
    source_code ="4199999999"
    source_code ="letintxbe((({x:x>0}}U{y:y<5}}I{z:z=3}))showx+@5."
    source_code ="4294967295"
    source_code ="00912"
    lexer = Lexer(source_code)
    tokens= lexer.tokenize()
    lexeme_list = [token.lexeme for token in tokens]
    token_list = [token.token_type for token in tokens]
    print(token_list)
    # for token in tokens:
    #     print(token.to_dict())

