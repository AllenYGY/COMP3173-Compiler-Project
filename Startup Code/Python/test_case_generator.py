import random

class EnhancedTestCaseGenerator:
    KEYWORDS = ["let", "be", "show", "int", "set","simplify"]
    PUNCTUATIONS = [".", "(", ")", "{", "}", ":"]
    RELATIONAL_OPERATORS = ["<", ">", "="]
    LOGICAL_OPERATORS = ["&", "|", "!"]
    ARITHMETIC_OPERATORS = ["+", "-", "*"]
    SET_OPERATORS = ["U", "I"]
    IDENTIFIERS = ["".join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, 5))) for _ in range(100)]
    # NUMBERS = [str(i) for i in range(0, 4294967295)] + ["00", "01", "0001"]  # 增加前导零数字
    NUMBERS = [str(i) for i in range(0,10000000)] + ["00", "01", "0001"]  # 增加前导零数字

    def __init__(self, num_cases=10, allow_no_space=True, include_invalid_cases=False):
        self.num_cases = num_cases
        self.allow_no_space = allow_no_space
        self.include_invalid_cases = include_invalid_cases

    def _maybe_remove_spaces(self, code: str) -> str:
        """
        随机移除空格，生成无空格的情况。
        """
        if self.allow_no_space and random.choice([True, False]):
            return ''.join(code.split())  # 移除所有空格
        return code

    def generate_test_case(self):
        """
        生成单个测试用例。
        """
        case_type = random.choice(["declaration", "calculation", "complex", "random_tokens", "invalid"])
        if case_type == "declaration":
            case = self.generate_declaration()
        elif case_type == "calculation":
            case = self.generate_calculation()
        elif case_type == "complex":
            case = self.generate_complex_case()
        elif case_type == "random_tokens":
            case = self.generate_random_tokens()
        elif case_type == "invalid" and self.include_invalid_cases:
            case = self.generate_invalid_case()
        else:
            case = self.generate_random_tokens()  # 默认 fallback
        return self._maybe_remove_spaces(case)

    def generate_declaration(self):
        """
        生成变量声明测试用例。
        """
        keyword = "let"
        data_type = random.choice(["int", "set"])
        identifier = random.choice(self.IDENTIFIERS)
        value = self.generate_value(data_type)
        return f"{keyword} {data_type} {identifier} be {value} ."

    def generate_value(self, data_type):
        """
        根据类型生成值。
        """
        if data_type == "int":
            return random.choice(self.NUMBERS)
        elif data_type == "set":
            return self.generate_set_expression()

    def generate_calculation(self):
        """
        生成计算表达式测试用例。
        """
        keyword = "show"
        operation = random.choice(["arithmetic", "boolean", "set"])
        if operation == "arithmetic":
            expr = self.generate_arithmetic_expression()
        elif operation == "boolean":
            expr = self.generate_predicate()
        elif operation == "set":
            expr = self.generate_set_expression()
        return f"{keyword} {expr} ."

    def generate_arithmetic_expression(self):
        """
        生成算术表达式。
        """
        expr = f"{random.choice(self.NUMBERS)} {random.choice(self.ARITHMETIC_OPERATORS)} {random.choice(self.NUMBERS)}"
        if random.choice([True, False]):
            expr = f"({expr}) {random.choice(self.ARITHMETIC_OPERATORS)} {random.choice(self.NUMBERS)}"
        return expr

    def generate_set_expression(self):
        """
        生成集合表达式。
        """
        representative = random.choice(self.IDENTIFIERS)
        predicate = self.generate_predicate()
        set_definition = f"{{ {representative} : {predicate} }}"
        if random.choice([True, False]):  # 添加集合运算
            other_set = f"{{ {random.choice(self.IDENTIFIERS)} : {self.generate_predicate()} }}"
            operator = random.choice(self.SET_OPERATORS)
            return f"{set_definition} {operator} {other_set}"
        return set_definition

    def generate_predicate(self):
        """
        生成谓词。
        """
        base_predicate = f"{random.choice(self.IDENTIFIERS)} {random.choice(self.RELATIONAL_OPERATORS)} {random.choice(self.NUMBERS)}"
        if random.choice([True, False]):  # 增加逻辑运算符连接
            logical_op = random.choice(self.LOGICAL_OPERATORS)
            additional_predicate = f"{random.choice(self.IDENTIFIERS)} {random.choice(self.RELATIONAL_OPERATORS)} {random.choice(self.NUMBERS)}"
            return f"{base_predicate} {logical_op} {additional_predicate}"
        return base_predicate

    def generate_complex_case(self):
        """
        生成复杂的测试用例。
        """
        declarations = "\n".join([self.generate_declaration() for _ in range(random.randint(1, 3))])
        calculations = "\n".join([self.generate_calculation() for _ in range(random.randint(1, 2))])
        return f"{declarations}\n{calculations}"

    def generate_random_tokens(self):
        """
        随机生成一组 token。
        """
        token_types = [
            random.choice(self.KEYWORDS),
            random.choice(self.PUNCTUATIONS),
            random.choice(self.RELATIONAL_OPERATORS),
            random.choice(self.LOGICAL_OPERATORS),
            random.choice(self.ARITHMETIC_OPERATORS),
            random.choice(self.SET_OPERATORS),
            random.choice(self.IDENTIFIERS),
            random.choice(self.NUMBERS)
        ]
        random.shuffle(token_types)
        return " ".join(token_types)

    def generate_invalid_case(self):
        """
        随机生成无效的测试用例，例如未闭合的括号、不完整的语法。
        """
        invalid_cases = [
            "let int x be (5 + .",  # 未闭合的括号
            "show x + ",  # 不完整表达式
            "let set { x : x = 5 }",  # 缺少标识符
            "show 12345678901234567890 ."  # 超出数值范围
        ]
        return random.choice(invalid_cases)

    def generate_test_cases(self):
        """
        生成多个测试用例。
        """
        return [self.generate_test_case() for _ in range(self.num_cases)]

    def save_to_file(self, filename="test_cases"):
        """
        将生成的测试用例保存到文件。
        """
        test_cases = self.generate_test_cases()
        with open(filename, "w") as f:
            for case in test_cases:
                f.write(f"{case}\n")
        print(f"Test cases saved to {filename}")


# 示例
if __name__ == "__main__":
    generator = EnhancedTestCaseGenerator(num_cases=10, allow_no_space=True, include_invalid_cases=True)
    generator.save_to_file()
