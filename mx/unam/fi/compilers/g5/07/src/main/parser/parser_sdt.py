# ------------------------------------------------------------
# parser_sdt.py
# Recursive Descent Parser + Basic SDT Validation
# C-Pure Compiler - Team 7
# ------------------------------------------------------------

class ASTNode:
    def __init__(self, type, children=None, value=None, inferred_type=None):
        self.type = type
        self.children = children if children else []
        self.value = value
        self.inferred_type = inferred_type

    def __repr__(self, level=0):
        type_info = f" <{self.inferred_type}>" if self.inferred_type else ""
        value_info = f" : {self.value}" if self.value is not None else ""
        result = "  " * level + f"|-- [{self.type}]{value_info}{type_info}\n"

        for child in self.children:
            if child:
                result += child.__repr__(level + 1)

        return result

class Parser:
    TYPE_KEYWORDS = {"int", "float", "double", "char", "void"}
    def __init__(self, tokens_list):
        unknown_tokens = [t for t in tokens_list if t["type"] == "Unknown"]

        if unknown_tokens:
            first = unknown_tokens[0]
            raise Exception(
                f"[Line {first['line']}] Lexical Error: Unknown token '{first['value']}'"
            )

        self.tokens = tokens_list
        self.current = 0
        self.derivation = []

        # SDT data structures
        self.scopes = [{}]
        self.functions = {}
        self.current_function_type = None
        self.sdt_errors = []

    # ------------------------------------------------------------
    # Token control methods
    # ------------------------------------------------------------

    def peek(self):
        if self.current < len(self.tokens):
            return self.tokens[self.current]

        return {"type": "EOF", "value": "$", "line": -1, "column": -1}

    def previous(self):
        return self.tokens[self.current - 1]

    def is_at_end(self):
        return self.peek()["type"] == "EOF"

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, value):
        if self.is_at_end():
            return False
        return self.peek()["value"] == value

    def check_type(self, type_name):
        if self.is_at_end():
            return False
        return self.peek()["type"] == type_name

    def match(self, *values):
        for value in values:
            if self.check(value):
                self.advance()
                return True
        return False

    def match_type(self, type_name):
        if self.check_type(type_name):
            self.advance()
            return True
        return False

    def consume(self, expected_value, message):
        if self.check(expected_value):
            return self.advance()

        token = self.peek()
        raise Exception(
            f"[Line {token['line']}] Syntax Error: {message} "
            f"(found '{token['value']}')"
        )

    def consume_type(self, expected_type, message):
        if self.check_type(expected_type):
            return self.advance()

        token = self.peek()
        raise Exception(
            f"[Line {token['line']}] Syntax Error: {message} "
            f"(found '{token['value']}')"
        )

    def consume_data_type(self, message):
        token = self.peek()

        if token["type"] == "Keywords" and token["value"] in self.TYPE_KEYWORDS:
            return self.advance()

        raise Exception(
            f"[Line {token['line']}] Syntax Error: {message} "
            f"(found '{token['value']}')"
        )

    def log(self, rule):
        self.derivation.append(rule)

    def log_token(self, name, value):
        self.derivation.append(f"{name} → {value}")

    # ------------------------------------------------------------
    # SDT helper methods
    # ------------------------------------------------------------

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare_variable(self, name, var_type, line):
        current_scope = self.scopes[-1]

        if name in current_scope:
            self.sdt_errors.append(
                f"[Line {line}] SDT Error: Variable '{name}' is already declared "
                f"in the current scope."
            )
            return

        if var_type == "void":
            self.sdt_errors.append(
                f"[Line {line}] SDT Error: Variable '{name}' cannot be declared as void."
            )

        current_scope[name] = {
            "type": var_type,
            "initialized": False
        }

    def lookup_variable(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def mark_initialized(self, name):
        symbol = self.lookup_variable(name)
        if symbol:
            symbol["initialized"] = True

    def is_numeric(self, type_name):
        return type_name in {"int", "float", "double", "char"}

    def are_types_compatible(self, target_type, source_type):
        if target_type == source_type:
            return True

        if target_type in {"float", "double"} and source_type in {"int", "char"}:
            return True

        if target_type == "int" and source_type == "char":
            return True

        return False

    def numeric_result_type(self, left_type, right_type):
        if "double" in {left_type, right_type}:
            return "double"
        if "float" in {left_type, right_type}:
            return "float"
        return "int"

    def infer_constant_type(self, value):
        if value.startswith("'") and value.endswith("'"):
            return "char"

        lower_value = value.lower()

        if "." in lower_value or "e" in lower_value:
            return "float"

        return "int"

    # ------------------------------------------------------------
    # Grammar rules
    # ------------------------------------------------------------

    def parse_program(self):
        """
        <PROGRAM> ::= <GLOBAL_LIST>
        """
        self.log("<PROGRAM> ::= <GLOBAL_LIST>")

        declarations = []

        while not self.is_at_end():
            declarations.append(self.parse_global_decl())

        return ASTNode("PROGRAM", declarations)

    def parse_global_decl(self):
        """
        <GLOBAL> ::= <TYPE> id <GLOBAL_REST>
        """
        self.log("<GLOBAL> ::= <TYPE> id <GLOBAL_REST>")

        data_type = self.consume_data_type("Expected a data type")
        self.log_token("TYPE", data_type["value"])

        identifier = self.consume_type("Identifiers", "Expected an identifier")
        self.log_token("Identifier", identifier["value"])

        if self.check("("):
            return self.parse_func_rest(
                data_type["value"],
                identifier["value"],
                identifier["line"]
            )

        return self.parse_global_var_rest(
            data_type["value"],
            identifier["value"],
            identifier["line"]
        )

    def parse_func_rest(self, function_type, function_name, line):
        """
        <GLOBAL_REST> ::= ( ) { <STMT_LIST> }
        """
        self.log("<GLOBAL_REST> ::= ( ) { <STMT_LIST> }")

        if function_name in self.functions:
            self.sdt_errors.append(
                f"[Line {line}] SDT Error: Function '{function_name}' is already declared."
            )

        self.functions[function_name] = {"type": function_type}

        self.consume("(", "Expected '(' after function name")
        self.consume(")", "Expected ')' after '('")
        self.consume("{", "Expected '{' to start function body")

        previous_function_type = self.current_function_type
        self.current_function_type = function_type

        self.enter_scope()

        body = []

        while not self.check("}") and not self.is_at_end():
            body.append(self.parse_statement())

        self.consume("}", "Expected '}' to close function body")

        self.exit_scope()
        self.current_function_type = previous_function_type

        return ASTNode(
            "FUNCTION",
            body,
            value=f"{function_type} {function_name}",
            inferred_type=function_type
        )

    def parse_global_var_rest(self, var_type, name, line):
        """
        <GLOBAL_REST> ::= <OPT_ASSIGN> ;
        """
        self.log("<GLOBAL_REST> ::= <OPT_ASSIGN> ;")

        self.declare_variable(name, var_type, line)

        init = None

        if self.match("="):
            init = self.parse_expression()

            if not self.are_types_compatible(var_type, init.inferred_type):
                self.sdt_errors.append(
                    f"[Line {line}] SDT Error: Cannot assign value of type "
                    f"'{init.inferred_type}' to global variable '{name}' of type '{var_type}'."
                )

            self.mark_initialized(name)

        self.consume(";", "Expected ';' after global declaration")

        return ASTNode(
            "GLOBAL_VAR",
            [init] if init else [],
            value=f"{var_type} {name}",
            inferred_type=var_type
        )

    def parse_statement(self):
        """
        <STMT> ::= <IF_STMT>
                 | return <OPT_E> ;
                 | <TYPE> id <OPT_ASSIGN_LOCAL> ;
                 | id = <E> ;
                 | id ( <ARG_LIST_OPT> ) ;
        """
        token = self.peek()

        if token["value"] == "if":
            return self.parse_if_stmt()

        if token["value"] == "return":
            return self.parse_return_stmt()

        if token["type"] == "Keywords" and token["value"] in self.TYPE_KEYWORDS:
            return self.parse_local_decl()

        if token["type"] == "Identifiers":
            next_token = (
                self.tokens[self.current + 1]
                if self.current + 1 < len(self.tokens)
                else None
            )

            if next_token and next_token["value"] == "=":
                return self.parse_assignment_stmt()

            if next_token and next_token["value"] == "(":
                call = self.parse_function_call()
                self.consume(";", "Expected ';' after function call")
                return call

        raise Exception(
            f"[Line {token['line']}] Syntax Error: Expected a valid statement "
            f"and found '{token['value']}'"
        )

    def parse_return_stmt(self):
        """
        return <OPT_E> ;
        """
        self.log("<STMT> ::= return <OPT_E> ;")

        return_token = self.advance()

        expr = None

        if not self.check(";"):
            expr = self.parse_expression()

        self.consume(";", "Expected ';' after return statement")

        if self.current_function_type is not None:
            if self.current_function_type == "void" and expr is not None:
                self.sdt_errors.append(
                    f"[Line {return_token['line']}] SDT Error: Void function should not return a value."
                )

            elif self.current_function_type != "void" and expr is None:
                self.sdt_errors.append(
                    f"[Line {return_token['line']}] SDT Error: Non-void function must return a value."
                )

            elif expr is not None and not self.are_types_compatible(
                self.current_function_type,
                expr.inferred_type
            ):
                self.sdt_errors.append(
                    f"[Line {return_token['line']}] SDT Error: Return type "
                    f"'{expr.inferred_type}' is not compatible with function type "
                    f"'{self.current_function_type}'."
                )

        return ASTNode("RETURN", [expr] if expr else [])

    def parse_local_decl(self):
        """
        <STMT> ::= <TYPE> id <OPT_ASSIGN_LOCAL> ;
        """
        self.log("<STMT> ::= <TYPE> id <OPT_ASSIGN_LOCAL> ;")

        data_type = self.consume_data_type("Expected a data type")
        identifier = self.consume_type("Identifiers", "Expected an identifier")

        self.declare_variable(
            identifier["value"],
            data_type["value"],
            identifier["line"]
        )

        init = None

        if self.match("="):
            init = self.parse_expression()

            if not self.are_types_compatible(data_type["value"], init.inferred_type):
                self.sdt_errors.append(
                    f"[Line {identifier['line']}] SDT Error: Cannot assign value "
                    f"of type '{init.inferred_type}' to variable '{identifier['value']}' "
                    f"of type '{data_type['value']}'."
                )

            self.mark_initialized(identifier["value"])

        self.consume(";", "Expected ';' after local declaration")

        return ASTNode(
            "LOCAL_VAR",
            [init] if init else [],
            value=f"{data_type['value']} {identifier['value']}",
            inferred_type=data_type["value"]
        )

    def parse_assignment_stmt(self):
        """
        <STMT> ::= id = <E> ;
        """
        self.log("<STMT> ::= id = <E> ;")

        identifier = self.consume_type("Identifiers", "Expected an identifier")
        self.consume("=", "Expected '=' in assignment")

        expr = self.parse_expression()
        self.consume(";", "Expected ';' after assignment")

        symbol = self.lookup_variable(identifier["value"])

        if not symbol:
            self.sdt_errors.append(
                f"[Line {identifier['line']}] SDT Error: Variable "
                f"'{identifier['value']}' was not declared before assignment."
            )
        else:
            if not self.are_types_compatible(symbol["type"], expr.inferred_type):
                self.sdt_errors.append(
                    f"[Line {identifier['line']}] SDT Error: Cannot assign value "
                    f"of type '{expr.inferred_type}' to variable '{identifier['value']}' "
                    f"of type '{symbol['type']}'."
                )

            self.mark_initialized(identifier["value"])

        return ASTNode(
            "ASSIGN",
            [expr],
            value=identifier["value"],
            inferred_type=expr.inferred_type
        )

    def parse_if_stmt(self):
        """
        <IF_STMT> ::= if ( <E> ) { <STMT_LIST> } <ELSE_PART>
        """
        self.log("<IF_STMT> ::= if ( <E> ) { <STMT_LIST> } <ELSE_PART>")

        if_token = self.advance()

        self.consume("(", "Expected '(' after if")
        condition = self.parse_expression()
        self.consume(")", "Expected ')' after if condition")

        if condition.inferred_type == "string":
            self.sdt_errors.append(
                f"[Line {if_token['line']}] SDT Error: If condition cannot be a string literal."
            )

        self.consume("{", "Expected '{' to start if block")

        self.enter_scope()

        then_block = []

        while not self.check("}") and not self.is_at_end():
            then_block.append(self.parse_statement())

        self.consume("}", "Expected '}' to close if block")

        self.exit_scope()

        else_block = []

        if self.match("else"):
            self.consume("{", "Expected '{' to start else block")

            self.enter_scope()

            while not self.check("}") and not self.is_at_end():
                else_block.append(self.parse_statement())

            self.consume("}", "Expected '}' to close else block")

            self.exit_scope()

        return ASTNode(
            "IF",
            [
                condition,
                ASTNode("THEN", then_block),
                ASTNode("ELSE", else_block)
            ]
        )

    # ------------------------------------------------------------
    # Expression grammar
    # ------------------------------------------------------------

    def parse_expression(self):
        self.log("<E> ::= <LOGIC_OR>")
        return self.parse_logic_or()

    def parse_logic_or(self):
        node = self.parse_logic_and()

        while self.match("||"):
            operator = self.previous()
            right = self.parse_logic_and()

            if node.inferred_type == "string" or right.inferred_type == "string":
                self.sdt_errors.append(
                    f"[Line {operator['line']}] SDT Error: Logical operator '||' "
                    f"cannot be applied to strings."
                )

            node = ASTNode("BIN_OP", [node, right], value="||", inferred_type="int")

        return node

    def parse_logic_and(self):
        node = self.parse_equality()

        while self.match("&&"):
            operator = self.previous()
            right = self.parse_equality()

            if node.inferred_type == "string" or right.inferred_type == "string":
                self.sdt_errors.append(
                    f"[Line {operator['line']}] SDT Error: Logical operator '&&' "
                    f"cannot be applied to strings."
                )

            node = ASTNode("BIN_OP", [node, right], value="&&", inferred_type="int")

        return node

    def parse_equality(self):
        node = self.parse_comparison()

        while self.match("==", "!="):
            operator = self.previous()
            right = self.parse_comparison()

            node = ASTNode(
                "BIN_OP",
                [node, right],
                value=operator["value"],
                inferred_type="int"
            )

        return node

    def parse_comparison(self):
        node = self.parse_term()

        while self.match(">", ">=", "<", "<="):
            operator = self.previous()
            right = self.parse_term()

            if not self.is_numeric(node.inferred_type) or not self.is_numeric(right.inferred_type):
                self.sdt_errors.append(
                    f"[Line {operator['line']}] SDT Error: Comparison operator "
                    f"'{operator['value']}' requires numeric operands."
                )

            node = ASTNode(
                "BIN_OP",
                [node, right],
                value=operator["value"],
                inferred_type="int"
            )

        return node

    def parse_term(self):
        node = self.parse_factor()

        while self.match("+", "-"):
            operator = self.previous()
            right = self.parse_factor()

            if not self.is_numeric(node.inferred_type) or not self.is_numeric(right.inferred_type):
                self.sdt_errors.append(
                    f"[Line {operator['line']}] SDT Error: Arithmetic operator "
                    f"'{operator['value']}' requires numeric operands."
                )
                result_type = "unknown"
            else:
                result_type = self.numeric_result_type(
                    node.inferred_type,
                    right.inferred_type
                )

            node = ASTNode(
                "BIN_OP",
                [node, right],
                value=operator["value"],
                inferred_type=result_type
            )

        return node

    def parse_factor(self):
        node = self.parse_unary()

        while self.match("*", "/", "%"):
            operator = self.previous()
            right = self.parse_unary()

            if not self.is_numeric(node.inferred_type) or not self.is_numeric(right.inferred_type):
                self.sdt_errors.append(
                    f"[Line {operator['line']}] SDT Error: Arithmetic operator "
                    f"'{operator['value']}' requires numeric operands."
                )
                result_type = "unknown"
            else:
                result_type = self.numeric_result_type(
                    node.inferred_type,
                    right.inferred_type
                )

            node = ASTNode(
                "BIN_OP",
                [node, right],
                value=operator["value"],
                inferred_type=result_type
            )

        return node

    def parse_unary(self):
        if self.match("!", "-"):
            operator = self.previous()
            expr = self.parse_unary()

            if operator["value"] == "-" and not self.is_numeric(expr.inferred_type):
                self.sdt_errors.append(
                    f"[Line {operator['line']}] SDT Error: Unary '-' requires a numeric operand."
                )

            result_type = "int" if operator["value"] == "!" else expr.inferred_type

            return ASTNode(
                "UNARY",
                [expr],
                value=operator["value"],
                inferred_type=result_type
            )

        return self.parse_primary()

    def parse_primary(self):
        token = self.peek()

        if self.match_type("Identifiers"):
            identifier = self.previous()

            if self.check("("):
                self.current -= 1
                return self.parse_function_call()

            symbol = self.lookup_variable(identifier["value"])

            if not symbol:
                self.sdt_errors.append(
                    f"[Line {identifier['line']}] SDT Error: Variable "
                    f"'{identifier['value']}' was not declared before use."
                )
                inferred_type = "unknown"
            else:
                inferred_type = symbol["type"]

            self.log_token("Identifier", identifier["value"])
            return ASTNode(
                "ID",
                value=identifier["value"],
                inferred_type=inferred_type
            )

        if self.match_type("Constants"):
            constant = self.previous()
            inferred_type = self.infer_constant_type(constant["value"])

            self.log_token("Constant", constant["value"])
            return ASTNode(
                "CONST",
                value=constant["value"],
                inferred_type=inferred_type
            )

        if self.match_type("Literals"):
            literal = self.previous()

            self.log_token("Literal", literal["value"])
            return ASTNode(
                "LITERAL",
                value=literal["value"],
                inferred_type="string"
            )

        if self.match("("):
            expr = self.parse_expression()
            self.consume(")", "Expected ')' after expression")
            return expr

        raise Exception(
            f"[Line {token['line']}] Syntax Error: Expected expression "
            f"and found '{token['value']}'"
        )

    def parse_function_call(self):
        """
        id ( <ARG_LIST_OPT> )
        """
        self.log("<PRIMARY> ::= id ( <ARG_LIST_OPT> )")

        identifier = self.consume_type("Identifiers", "Expected function name")

        self.consume("(", "Expected '(' after function name")

        args = []

        if not self.check(")"):
            args.append(self.parse_expression())

            while self.match(","):
                args.append(self.parse_expression())

        self.consume(")", "Expected ')' after function arguments")

        built_in_functions = {
            "printf": "int",
            "scanf": "int"
        }

        if identifier["value"] in built_in_functions:
            return_type = built_in_functions[identifier["value"]]
        elif identifier["value"] in self.functions:
            return_type = self.functions[identifier["value"]]["type"]
        else:
            self.sdt_errors.append(
                f"[Line {identifier['line']}] SDT Error: Function "
                f"'{identifier['value']}' was not declared."
            )
            return_type = "unknown"

        return ASTNode(
            "CALL",
            args,
            value=identifier["value"],
            inferred_type=return_type
        )

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------

    def get_derivation(self, ast=None):
        output = []

        output.append("Parsing Success!")
        output.append("")

        output.append("Derivation:")
        output.extend(self.derivation)

        output.append("")

        if ast:
            output.append("Abstract Syntax Tree:")
            output.append(str(ast))
            output.append("")

        if self.sdt_errors:
            output.append("SDT Errors:")
            output.extend(self.sdt_errors)
        else:
            output.append("SDT Verified!")

        return "\n".join(output)