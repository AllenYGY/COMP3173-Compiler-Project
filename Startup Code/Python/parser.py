from __future__ import annotations
from lexer import Token, Lexer

class Parser:
    def __init__(self, tokens: list[Token], actions: dict, goto: dict, rules: dict):
        self.tokens = tokens
        self.index = 0
        self.stack = []
        self.actions = actions
        self.goto = goto
        self.rules = rules
        self.symbol_table = {}
        self.typing_rules = {
            "S':S": lambda S: S["type"],
            "S:D' C .": lambda D_prime, C, _: "program" if D_prime["type"] != "type_error" and C["type"] != "type_error" else "type_error",
            "S:C .": lambda C,_: C["type"],
            "D':D D'": lambda D, D_prime_2: "declarations" if D["type"] == "declaration" and D_prime_2["type"] == "declarations" else "type_error",
            "D':D": lambda D: "declarations" if D["type"] == "declaration" else "type_error",
            "D:let T id be E .": lambda let, T, id, be, E, _: (("declaration", self.add_type(id, T["type"]))[0] if E["type"] != "type_error" else "type_error"),
            "T:int": lambda _: "integer",
            "T:set": lambda _: "set",
            "E:E'": lambda E_prime: E_prime["type"],
            "E:E U E'": lambda E, _,E_prime: "set" if E["type"] == "set" and E_prime["type"] == "set" else "type_error",
            "E:E + E'": lambda E,_, E_prime: "integer" if E["type"] == "integer" and E_prime["type"] == "integer" else "type_error",
            "E:E - E'": lambda E,_, E_prime: "integer" if E["type"] == "integer" and E_prime["type"] == "integer" else "type_error",
            "E':E''": lambda E_double_prime: E_double_prime["type"],
            "E':E' I E''": lambda E_prime, _,E_double_prime: "set" if E_prime["type"] == "set" and E_double_prime["type"] == "set" else "type_error",
            "E':E' * E''": lambda E_prime, _,E_double_prime: "integer" if E_prime["type"] == "integer" and E_double_prime["type"] == "integer" else "type_error",
            "E'':num": lambda _: "integer",
            "E'':id": lambda id: self.lookup_type(id),
            "E'':( E )": lambda _,E,x: E["type"],
            "E'':{ Z P }": lambda _,Z, P,x: "set" if P["type"] == "predicate" else "type_error",
            "Z:id :": lambda id,_: ("void", self.add_type(id, "integer"))[0],
            "P:P | P'": lambda P2, _, P_prime: "predicate" if P2["type"] == "predicate" and P_prime["type"] == "predicate" else "type_error",
            "P:P'": lambda P_prime: P_prime["type"],
            "P':P' & P''": lambda P_prime,_, P_double_prime: "predicate" if P_prime["type"] == "predicate" and P_double_prime["type"] == "predicate" else "type_error",
            "P':P''": lambda P_double_prime: P_double_prime["type"],
            "P'':R": lambda R: "predicate" if R["type"] == "relation" else "type_error",
            "P'':( P )": lambda _,P,x: P["type"],
            "P'':! R": lambda _,R: "predicate" if R["type"] == "relation" else "type_error",
            "R:E < E": lambda E1, _,E2: "relation" if E1["type"] == "integer" and E2["type"] == "integer" else "type_error",
            "R:E > E": lambda E1, _,E2: "relation" if E1["type"] == "integer" and E2["type"] == "integer" else "type_error",
            "R:E = E": lambda E1, _,E2: "relation" if E1["type"] == "integer" and E2["type"] == "integer" else "type_error",
            "R:E @ E": lambda E1, _,E2: "relation" if E1["type"] == "integer" and E2["type"] == "set" else "type_error",
            "C:show A": lambda _,A: A["type"],
            "A:E": lambda E: "calculation" if E["type"] != "type_error" else "type_error",
            "A:P": lambda P: "calculation" if P["type"] != "type_error" else "type_error",
        }
        
        self.evaluation_rules = {
            "S':S": lambda S: S["value"],
            "S:D' C .": lambda D_prime, C, _: C["value"],
            "S:C .": lambda C, _: C["value"],
            "D':D D'": lambda D, D_prime_2: D_prime_2["value"],
            "D':D": lambda D: D["value"],
            "D:let T id be E .": lambda let, T, id, be, E, _: "void",
            "T:int": lambda _: "void",
            "T:set": lambda _: "void",
            "E:E'": lambda E_prime: E_prime["value"],
            "E:E U E'": lambda E, _, E_prime: f"({E['value']} U {E_prime['value']})",
            "E:E + E'": lambda E, _, E_prime: str(int(E["value"]) + int(E_prime["value"])),
            "E:E - E'": lambda E, _, E_prime: str(int(E["value"]) - int(E_prime["value"])),   
            "E':E''": lambda E_double_prime: E_double_prime["value"],
            "E':E' I E''": lambda E_prime, _, E_double_prime: f"{E_prime['value']} I {E_double_prime['value']}",
            "E':E' * E''": lambda E_prime, _, E_double_prime: str(int(E_prime["value"]) * int(E_double_prime["value"])),
            "E'':num": lambda num: num["lexeme"],
            "E'':id": lambda id: self.symbol_table.get(id["lexeme"], {}).get("value", None) or id["lexeme"],
            "E'':( E )": lambda _, E, x: f'( {E["value"]} )',
            "E'':{ Z P }": lambda _, Z, P, x: f"{{ {Z['value']}: {P['value']} }}",
            "Z:id :": lambda id, _: id["lexeme"], 
            "P:P | P'": lambda P, _, P_prime: f"({P['value']} | {P_prime['value']})",
            "P:P'": lambda P_prime: P_prime["value"],
            "P':P' & P''": lambda P_prime, _, P_double_prime: f"({P_prime['value']} & {P_double_prime['value']})",
            "P':P''": lambda P_double_prime: P_double_prime["value"],
            "P'':R": lambda R: R["value"],
            "P'':( P )": lambda _, P, x: f'( {P["value"]} )',
            "P'':! R": lambda _, R: f'! {R["value"]}',
            "R:E < E": lambda E1, _, E2: f"{E1['value']} < {E2['value']}",
            "R:E > E": lambda E1, _, E2: f"{E1['value']} > {E2['value']}",
            "R:E = E": lambda E1, _, E2: f"{E1['value']} = {E2['value']}",
            "R:E @ E": lambda E1, _, E2: f"{E1['value']} @ {E2['value']}",
            "C:show A": lambda _, A: A["value"],
            "A:E": lambda E: str(E["value"]),
            "A:P": lambda P: "true" if eval(P["value"]) else "false",
        }

        self.new_evaluation_rules = {
            "S':S": lambda S: S["value"],
            "S:D' C .": lambda D_prime, C, _: C["value"],
            "S:C .": lambda C, _: C["value"],
            "D':D D'": lambda D, D_prime_2: D_prime_2["value"],
            "D':D": lambda D: D["value"],
            "D:let T id be E .": lambda let, T, id, be, E, _: "void",
            "T:int": lambda _: "void",
            "T:set": lambda _: "void",
            "E:E'": lambda E_prime: E_prime["value"],
            "E:E U E'": lambda E, _, E_prime: f"({E['value']} U {E_prime['value']})",
            "E:E + E'": lambda E, _, E_prime: str(int(E["value"]) + int(E_prime["value"])),
            "E:E - E'": lambda E, _, E_prime: str(int(E["value"]) - int(E_prime["value"])),   
            "E':E''": lambda E_double_prime: E_double_prime["value"],
            "E':E' I E''": lambda E_prime, _, E_double_prime: f"{E_prime['value']} I {E_double_prime['value']}",
            "E':E' * E''": lambda E_prime, _, E_double_prime: str(int(E_prime["value"]) * int(E_double_prime["value"])),
            "E'':num": lambda num: num["lexeme"],
            "E'':id": lambda id: self.symbol_table.get(id["lexeme"], {}).get("value", None) or id["lexeme"],
            "E'':( E )": lambda _, E, x: f'( {E["value"]} )',
            "E'':{ Z P }": lambda _, Z, P, x: f"{{ {Z['value']}: {P['value']} }}",
            "Z:id :": lambda id, _: id["lexeme"], 
            # "P:P | P'": lambda P, _, P_prime: f"({P['value']} | {P_prime['value']})",
            # "P:P'": lambda P_prime: P_prime["value"],
            # "P':P' & P''": lambda P_prime, _, P_double_prime: f"({P_prime['value']} & {P_double_prime['value']})",
            # "P':P''": lambda P_double_prime: P_double_prime["value"],
            # "P'':R": lambda R: R["value"],
            "P'':R": lambda R: (R["value"], R["bool"]),

            "P'':( P )": lambda _, P, x: f'( {P["value"]} )',
            "P'':! R": lambda _, R: f'! {R["value"]}',

            "P:P | P'": lambda P, _, P_prime: (f"({P['value']} | {P_prime['value']})", P["bool"] or P_prime["bool"]),
            "P':P' & P''": lambda P_prime, _, P_double_prime: (f"({P_prime['value']} & {P_double_prime['value']})", P_prime["bool"] and P_double_prime["bool"]),
            "P:P'": lambda P_prime: (P_prime["value"], P_prime["bool"]),
            "P':P''": lambda P_double_prime: (P_double_prime["value"], P_double_prime["bool"]),


            "R:E < E": lambda E1, _, E2: (f"{E1['value']} < {E2['value']}", E1["value"]<E2["value"]),
            "R:E > E": lambda E1, _, E2: (f"{E1['value']} > {E2['value']}", E1["value"]> E2["value"]),
            "R:E = E": lambda E1, _, E2: (f"{E1['value']} = {E2['value']}", E1["value"]== E2["value"]),
            # "R:E @ E": lambda E1, x, E2: (f"{E1['value']} @ {E2['value']}", self.evaluate_predicate(E1["value"], E2["value"])),
            "R:E @ E": lambda E1, _, E2: (f"{E1['value']} @ {E2['value']}", self.evaluate_predicate(E1["value"], E2["value"])),
            "C:show A": lambda _, A: A["value"],
            "A:E": lambda E: str(E["value"]),
            # "A:P": lambda P: "true" if P['bool'] else "false",
            "A:P": lambda P: ("true" if P['bool'] else "false", P['bool']),
            # "A:P": lambda P: "true" if eval(P["value"]) else "false",
        }
    
    def evaluate_predicate(self,element, predicate_expression):
        """
        动态解析并计算谓词表达式，支持不定长度的逻辑条件。
        :param element: 单一值，例如 `3`
        :param predicate_expression: 谓词表达式，例如 `{a: a > 1 | a > 0 & a > 10 | a < -5}`
        :return: 布尔值，判断结果
        """
        import re
        # 去除多余空格
        # predicate_expression = re.sub(r"\s+", " ", predicate_expression).strip()
        predicate_expression=re.sub(r"\s+", "", predicate_expression).strip()
        # 匹配变量和谓词
        match = re.match(r"\{(\w+)\s*:\s*(.+)\}", predicate_expression)
        if not match:
            raise ValueError(f"Invalid predicate expression: {predicate_expression}")

        variable, predicate = match.groups()

        # 替换逻辑运算符为 Python 的运算符
        predicate = predicate.replace("|", "or").replace("&", "and")

        # 动态求值，将 `element` 的值代入谓词
        try:
            # 使用 exec 绑定变量
            local_namespace = {}
            exec(f"{variable} = {element}", {}, local_namespace)
            result = eval(predicate, {}, local_namespace)
        except Exception as e:
            raise ValueError(f"Error evaluating predicate '{predicate_expression}' with element '{element}': {e}")
        
        return result

    def add_type(self, id: dict, type: str):
        """
        将标识符和类型添加到符号表。
        参数:
        - id: dict, 包含标识符信息（如 lexeme）。
        - type: str, 标识符的类型（如 "integer", "set"）。
        返回:
        - 如果添加成功，返回 "void"。
        - 如果添加失败或遇到错误，抛出异常。
        """
        id_name = id.get("lexeme", None)  # 提取标识符的名字
        if not id_name:  # 如果标识符的名字为空
            print(f"Error: Missing lexeme for identifier: {id}")
            return "type_error"
        # 检查是否已在符号表中

        # if id_name in self.symbol_table:
        #     raise ValueError(f"Variable '{id_name}' is already declared.")
        # 添加到符号表
        
        self.symbol_table[id_name] = {"type": type, "value": None}
        # print(f"Added variable '{id_name}' with type '{type}' to symbol table.")
        return "void"


    def lookup_type(self, identifier):
        """
        查找标识符的类型，支持传入字典或字符串作为标识符。
        
        参数:
        - identifier: dict 或 str
        如果是 dict，则应包含 'lexeme' 字段；
        如果是 str，则直接视为标识符的名称。
        
        返回:
        - 如果标识符存在，返回其类型；
        - 如果标识符未找到或参数不合法，返回 "type_error"；
        - 如果标识符类型为 None，则返回 "void"。
        """
        if isinstance(identifier, dict):
            # 提取字典中的 'lexeme' 字段
            id_name = identifier.get("lexeme", None)
        elif isinstance(identifier, str):
            # 如果是字符串，直接使用
            id_name = identifier
        else:
            # 如果类型既不是 dict 也不是 str，则返回错误
            print(f"Error: Invalid identifier type: {type(identifier)}")
            return "type_error"
        
        if not id_name:  # 如果 'lexeme' 或字符串为空
            print(f"Error: Invalid identifier name: {id_name}")
            return "type_error"

        # 在符号表中查找
        symbol_entry = self.symbol_table.get(id_name)
        if not symbol_entry:  # 如果未找到
            return "type_error"

        # 提取类型字段并检查是否为 None
        symbol_type = symbol_entry.get("type", "type_error")
        if symbol_type is None:
            return "type_error"
        
        return symbol_type

    def parse(self):
        self.stack.append((0, None))  
        current_token = self.tokens[self.index] if self.index < len(self.tokens) else None
        parse_tree = None
        while True:
            state = self.stack[-1][0]  
            action, value = self.actions.get((state, current_token.token_type if current_token else "$"), (None, None))
            # print(f"Current state: {state}, Current token: {current_token.lexeme if current_token else 'EOF'}, Action: {action}, Value: {value}")
            try:
                if action is None:
                    raise ValueError(f"Syntax Error: Unexpected token '{current_token.lexeme if current_token else 'EOF'}' at state {state}. Stack: {self.stack}")
                if action == "s":
                    leaf_node = {"token": current_token.token_type, "lexeme": current_token.lexeme}
                    self.stack.append((value, leaf_node))  
                    self.index += 1  
                    current_token = self.tokens[self.index] if self.index < len(self.tokens) else None
                elif action == "r":  
                    lhs, _, rhs_length = self.rules[value]['non-terminal'], self.rules[value]['productions'], self.rules[value]['length']
                    # print(f"Current state: {state}, LHS: {lhs}")
                    children = []  
                    for _ in range(rhs_length):
                        _, child_node = self.stack.pop()
                        children.insert(0, child_node)  
                    subtree = {"name": lhs, "children": children}
                    state = self.stack[-1][0]  
                    self.stack.append((self.goto[(state, lhs)], subtree))  
                elif action == "acc":  
                    print("Syntactic Analysis Complete!")
                    _, parse_tree = self.stack[-1]  
                    break  
            except ValueError as e:
                print("Syntax Error!")
                print(e)
                json_output = []
                with open('parser_out.json', 'w') as f:
                    f.write(str(json_output))
                return None 
        return parse_tree  
    
    def typecheck(self):
        self.index = 0
        self.stack = [(0, None)] 
        current_token = self.tokens[self.index] if self.index < len(self.tokens) else None
        typecheck_tree = None

        while True:
            state = self.stack[-1][0] 
            action, value = self.actions.get(
                (state, current_token.token_type if current_token else "$"), (None, None)
            )
            try:
                if action is None:
                    raise SyntaxError(f"Syntax Error: Unexpected token '{current_token.lexeme}' at state {state}.")
                if action == "s": 
                    token_type = "void"  
                    if current_token.token_type == "num":
                        token_type = "integer"   
                    if token_type == "type_error":
                        raise TypeError(f"Type Error: Invalid type for token '{current_token.lexeme}'.")
                    leaf_node = {
                        "token": current_token.token_type,
                        "lexeme": current_token.lexeme,
                        "type": token_type,
                    }
                    self.stack.append((value, leaf_node))
                    self.index += 1
                    current_token = self.tokens[self.index] if self.index < len(self.tokens) else None

                elif action == "r": 
                    lhs, productions, rhs_length = (
                        self.rules[value]["non-terminal"],
                        self.rules[value]["productions"],
                        self.rules[value]["length"],
                    )

                    key = f"{lhs}:{productions}"  # 类型规则的键
                    type_children = []  # 用于存储子节点的类型信息
                    for _ in range(rhs_length):
                        _, child_node = self.stack.pop()
                        type_children.insert(0, child_node)
                        # type_children.insert(0, {"type": child_node.get("type", "void")})  # 获取子节点类型
                    # print(key, type_children)   
                    # print(f"Current state: {state}, LHS: {lhs}")
                    # print("=====================================")
                    # print(key)
                    if key in self.typing_rules:
                        type_result = self.typing_rules[key](*type_children)  # 应用类型规则
                        # print child node type
                        # print(type_children)
                        # if type_result == "type_error":
                        #     raise TypeError(f"Type Error: Typing rule for {key} failed.")
                    else:
                        raise TypeError(f"Typing rule for {key} not defined.")

                    subtree = {
                        "name": lhs,
                        "type": type_result,  # 在语法树中附加父节点的类型信息
                        "children": type_children,
                    }
                    state = self.stack[-1][0]
                    self.stack.append((self.goto[(state, lhs)], subtree))

                elif action == "acc":  # 接受
                    print("Semantic Analysis Complete!")
                    _, typecheck_tree = self.stack[-1]
                    break
            except (SyntaxError, TypeError) as e:
                print("Semantic Error!")
                print(e)
                json_output = []
                with open('typing_out.json', 'w') as f:
                    f.write(str(json_output))
                return []
        return typecheck_tree

    def evaluate_0(self):
        self.index = 0
        self.stack = [(0, None)] 
        current_token = self.tokens[self.index] if self.index < len(self.tokens) else None
        evaluate_tree = None
        while True:
            state = self.stack[-1][0] 
            action, value = self.actions.get(
                (state, current_token.token_type if current_token else "$"), (None, None)
            )
            if action is None:
                    raise SyntaxError(f"Unexpected token '{current_token.lexeme}' at state {state}.")
            try:
                if action == "s": 
                    evaluation_value = "void"  
                    if current_token.token_type == "num":
                        evaluation_value = current_token.lexeme
                    leaf_node = {
                        "token": current_token.token_type,
                        "lexeme": current_token.lexeme,
                        "value": evaluation_value,
                        "bool": "undefined",
                    }
                    self.stack.append((value, leaf_node))
                    self.index += 1
                    current_token = self.tokens[self.index] if self.index < len(self.tokens) else None
                elif action == "r": 
                    lhs, productions, rhs_length = (
                        self.rules[value]["non-terminal"],
                        self.rules[value]["productions"],
                        self.rules[value]["length"],
                    )
                    key = f"{lhs}:{productions}"  # 类型规则的键
                    type_children = []  # 用于存储子节点的类型信息
                    for _ in range(rhs_length):
                        _, child_node = self.stack.pop()
                        type_children.insert(0, child_node)
                    if key == "D:let T id be E .":
                        id_node = type_children[2]  # 获取标识符节点
                        expression_node = type_children[4]  # 获取表达式节点
                        self.symbol_table[id_node["lexeme"]] = {
                            "type": type_children[1]["value"],  # 变量的类型
                            "value": expression_node["value"],  # 变量的值
                        }
                    if key in self.new_evaluation_rules:
                        evaluation_value = self.new_evaluation_rules[key](*type_children)  # 应用类型规则
                        bool_value = "undefined"
                        # if return a tuple
                        if isinstance(evaluation_value, tuple):
                            evaluation_value, bool_value = evaluation_value
                        
                    else:
                        raise TypeError(f"Typing rule for {key} not defined.")
                    subtree = {
                        "name": lhs,
                        "value": evaluation_value, 
                        "bool": bool_value,
                        "children": type_children,
                    }
                    state = self.stack[-1][0]
                    self.stack.append((self.goto[(state, lhs)], subtree))
                elif action == "acc":
                    print("Evaluation Analysis Complete!")
                    _, evaluate_tree = self.stack[-1]
                    print(evaluate_tree["value"])
                    break
            except (SyntaxError, TypeError) as e:
                print("Semantic Error!")
        return evaluate_tree
    def remove_bool_attributes(self,node):
        """
        递归地遍历树并删除所有的 'bool' 属性。
        :param node: 当前节点，可能是一个字典或列表。
        :return: 去除了 'bool' 属性的节点。
        """
        if isinstance(node, dict):
            # 如果是字典，删除 'bool' 键，并递归处理其值
            node.pop('bool', None)  # 删除 'bool' 属性
            for key in node:
                node[key] = self.remove_bool_attributes(node[key])
        elif isinstance(node, list):
            # 如果是列表，递归处理每个元素
            node = [self.remove_bool_attributes(child) for child in node]
        return node
    
    def evaluate(self):
        self.index = 0
        self.stack = [(0, None)] 
        current_token = self.tokens[self.index] if self.index < len(self.tokens) else None
        evaluate_tree = None
        while True:
            state = self.stack[-1][0] 
            action, value = self.actions.get(
                (state, current_token.token_type if current_token else "$"), (None, None)
            )
            if action is None:
                raise SyntaxError(f"Unexpected token '{current_token.lexeme}' at state {state}.")
            try:
                if action == "s": 
                    evaluation_value = "void"
                    if current_token.token_type == "num":
                        evaluation_value = current_token.lexeme
                    leaf_node = {
                        "token": current_token.token_type,
                        "lexeme": current_token.lexeme,
                        "value": evaluation_value,
                        "bool": None,  # 默认设置为 None
                    }
                    self.stack.append((value, leaf_node))
                    self.index += 1
                    current_token = self.tokens[self.index] if self.index < len(self.tokens) else None

                elif action == "r": 
                    lhs, productions, rhs_length = (
                        self.rules[value]["non-terminal"],
                        self.rules[value]["productions"],
                        self.rules[value]["length"],
                    )
                    key = f"{lhs}:{productions}"  # 类型规则的键
                    
                    if len(self.stack) < rhs_length:
                        raise ValueError("Stack underflow: Not enough elements to pop for the current rule.")

                    type_children = []
                    for _ in range(rhs_length):
                        _, child_node = self.stack.pop()
                        type_children.insert(0, child_node)

                    if key == "D:let T id be E .":
                        id_node = type_children[2]
                        expression_node = type_children[4]
                        if "value" not in type_children[1] or "value" not in expression_node:
                            raise ValueError("Invalid value or type when updating symbol table.")
                        self.symbol_table[id_node["lexeme"]] = {
                            "type": type_children[1]["value"],
                            "value": expression_node["value"],
                        }
                    # print(f"Applying rule: {key}")
                    # print(f"Children: {type_children}, lenth:{len(type_children)}")
                    # print("===========================================")                   
                    if key in self.new_evaluation_rules:
                        evaluation_value = self.new_evaluation_rules[key](*type_children)
                        # print("1111")
                        bool_value = None
                        if isinstance(evaluation_value, tuple):
                            evaluation_value, bool_value = evaluation_value
                        bool_value = bool_value if isinstance(bool_value, bool) else "undefined"
                    else:
                        raise TypeError(f"Typing rule for {key} not defined.")

                    subtree = {
                        "name": lhs,
                        "value": evaluation_value,
                        "bool": bool_value,
                        "children": type_children,
                    }
                    state = self.stack[-1][0]
                    self.stack.append((self.goto[(state, lhs)], subtree))

                elif action == "acc":
                    print("Evaluation Analysis Complete!")
                    _, evaluate_tree = self.stack[-1]
                    evaluate_tree=self.remove_bool_attributes(evaluate_tree)
                    print(f"Final Value: {evaluate_tree['value']}")
                    # print(f"Final Boolean: {evaluate_tree.get('bool', 'undefined')}")
                    break

            except (SyntaxError, TypeError, ValueError) as e:
                print(f"Semantic Error: {e}")
                break
        return evaluate_tree

class SLRParserTable:
    def __init__(self, file_path: str, grammar_path: str = None):
        self.file_path = file_path
        self.grammar_path = grammar_path
        self.data = self.read_csv()
        self.header, self.data = self.parse_header_and_data()
        self.terminals, self.non_terminals, self.ACTION_TABLE, self.GOTO_TABLE = self.split_action_goto()
        self.ACTION = self.parse_action()
        self.GOTO = self.parse_goto()
        if self.grammar_path:
            self.grammar = self.read_grammar()

    def read_csv(self):
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        return [line.strip().split(',') for line in lines]

    def parse_header_and_data(self):
        header = self.data[1][1:]  # Assuming second row is the header
        data = [row[1:] for row in self.data[2:]]  # Ignoring the first column
        return header, data

    def split_action_goto(self):
        idx = self.header.index("S'")
        terminals = self.header[:idx]
        non_terminals = self.header[idx:]
        ACTION_TABLE = [row[:idx] for row in self.data]
        GOTO_TABLE = [row[idx:] for row in self.data]
        return terminals, non_terminals, ACTION_TABLE, GOTO_TABLE

    def parse_action(self):
        ACTION = {}
        for state, row in enumerate(self.ACTION_TABLE):
            for col_index, action in enumerate(row):
                if action:
                    act_type = action[0]
                    if act_type in {'s', 'r'}:
                        act_value = int(action[1:])
                        ACTION[(state, self.terminals[col_index])] = (
                            act_type, act_value)
                    elif action == 'acc':
                        ACTION[(state, self.terminals[col_index])] = (
                            action, None)
        return ACTION

    def parse_goto(self):
        GOTO = {}
        for state, row in enumerate(self.GOTO_TABLE):
            for col_index, next_state in enumerate(row):
                if next_state.strip():
                    GOTO[(state, self.non_terminals[col_index])] = int(next_state)
        return GOTO

    def read_grammar(self):
        grammar = {}
        with open(self.grammar_path, 'r') as file:
            lines = file.readlines()
        for line in lines:

            line = line.strip()
            if line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    rule_number = int(parts[0].strip())
                    lhs_rhs = parts[1].strip().split('->')
                    if len(lhs_rhs) == 2:
                        lhs = lhs_rhs[0].strip()
                        rhs = lhs_rhs[1].strip()
                        rhs_elements = rhs.split()
                        grammar[rule_number] = {
                            'non-terminal': lhs, 'productions': rhs, 'length': len(rhs_elements)}
        return grammar

    def print_table(self, table):
        for key, value in table.items():
            print(f"{key}: {value}")

if __name__ == '__main__':
    file_path = 'SLR Parsing Table.csv'
    grammar_path = 'SLR Grammar.txt'
    # test_case = "let int x be 1. let set y be { a: a > 1}. show x @ y."
    # test_case="let int x be 1.let set y be { a: a > 1}.show x @ y."
    test_case = "let int x be 2. let set y be { a: a > 1 }. show x @ y. "
    # test_case = "let int x be 1. show x."
    lexer = Lexer(test_case)
    tokens, symbol_table = lexer.tokenize()
    lexer_ouput = [token.to_dict() for token in tokens]
    import json
    with open("lexer_out.json", "w", encoding="utf-8") as f:
        json.dump(lexer_ouput, f, ensure_ascii=False, indent=4)

    tokens.append(Token(token_type="$", lexeme="$", value="$"))
    slr_table = SLRParserTable(file_path, grammar_path)
    actions, goto, rules = slr_table.ACTION, slr_table.GOTO, slr_table.grammar
    simplified_rules = {}
    for rule_number, details in rules.items():
        simplified_rules[rule_number] = (
            details['non-terminal'], details['length'])
    # for token in tokens:
    #     print(token.token_type, token.lexeme)
    # parser=Parser(tokens,actions, goto, rules, symbol_table)
    parser=Parser(tokens,actions, goto, rules)
    parse_tree=parser.parse()
    with open("parser_out.json", "w", encoding="utf-8") as f:
        json.dump(parse_tree, f, ensure_ascii=False, indent=4)
    typeing_tree=parser.typecheck()
    with open("typing_out.json", "w", encoding="utf-8") as f:
        json.dump(typeing_tree, f, ensure_ascii=False, indent=4)
    evaluation_tree=parser.evaluate()
    with open("evaluation_out.json", "w", encoding="utf-8") as f:
        json.dump(evaluation_tree, f, ensure_ascii=False, indent=4)
    # print(parser.symbol_table)
