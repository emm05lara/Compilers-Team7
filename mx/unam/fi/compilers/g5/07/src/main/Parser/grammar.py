"""
C Grammar Specification
-----------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date: April 28, 2026

Description:
This module defines the context-free grammar (CFG) for the C language.
The grammar is structured in Backus-Naur Form (BNF) and has been factorized
to eliminate left recursion, making it compatible with LL(1) parsing.

Usage:
Run this script directly to visualize the grammar in a GUI window.
"""

import tkinter as tk
from tkinter import scrolledtext



class Grammar:

    def __init__(self):

        # -------------------------
        # TERMINALS
        # -------------------------
        self.terminals = {
            'id', 'constant', 'literal',
            'int', 'float', 'double', 'char', 'void',
            'if', 'else', 'return',
            '=', ';', '(', ')', '{', '}',
            '+', '-', '*', '/', '%',
            '==', '!=', '>', '>=', '<', '<=',
            '&&', '||', '!'
        }

        # -------------------------
        # NON-TERMINALS
        # -------------------------
        self.non_terminals = {
            'PROGRAM', 'GLOBAL', 'TYPE', 'GLOBAL_REST',
            'OPT_ASSIGN', 'OPT_E',
            'STMT_LIST', 'STMT', 'STMT_ID_REST',
            'IF_STMT', 'ELSE_PART',
            'E', 'LOGIC_OR', 'LOGIC_OR_PRIME',
            'LOGIC_AND', 'LOGIC_AND_PRIME',
            'EQUALITY', 'EQUALITY_PRIME',
            'COMPARISON', 'COMPARISON_PRIME',
            'TERM', 'TERM_PRIME',
            'FACTOR', 'FACTOR_PRIME',
            'UNARY', 'PRIMARY'
        }

        self.start_symbol = 'PROGRAM'

        # -------------------------
        # PRODUCTIONS
        # -------------------------
        self.productions = {

            # PROGRAM → GLOBAL PROGRAM | ε
            'PROGRAM': [['GLOBAL', 'PROGRAM'], ['epsilon']],

            # GLOBAL → TYPE id GLOBAL_REST
            'GLOBAL': [['TYPE', 'id', 'GLOBAL_REST']],

            # TYPE → int | float | double | char | void
            'TYPE': [['int'], ['float'], ['double'], ['char'], ['void']],

            # GLOBAL_REST → function | variable
            'GLOBAL_REST': [
                ['(', ')', '{', 'STMT_LIST', '}'],
                ['OPT_ASSIGN', ';']
            ],

            # OPT_ASSIGN → = E | ε
            'OPT_ASSIGN': [['=', 'E'], ['epsilon']],

            # STATEMENTS
            'STMT_LIST': [['STMT', 'STMT_LIST'], ['epsilon']],

            'STMT': [
                ['IF_STMT'],
                ['return', 'OPT_E', ';'],
                ['TYPE', 'id', 'OPT_ASSIGN', ';'],
                ['id', 'STMT_ID_REST']
            ],

            # return optional expression
            'OPT_E': [['E'], ['epsilon']],

            # assignment or function call
            'STMT_ID_REST': [
                ['=', 'E', ';'],
                ['(', ')', ';']
            ],

            # IF
            'IF_STMT': [['if', '(', 'E', ')', '{', 'STMT_LIST', '}', 'ELSE_PART']],

            'ELSE_PART': [['else', '{', 'STMT_LIST', '}'], ['epsilon']],

            # -------------------------
            # EXPRESSIONS
            # -------------------------
            'E': [['LOGIC_OR']],

            'LOGIC_OR': [['LOGIC_AND', 'LOGIC_OR_PRIME']],
            'LOGIC_OR_PRIME': [['||', 'LOGIC_AND', 'LOGIC_OR_PRIME'], ['epsilon']],

            'LOGIC_AND': [['EQUALITY', 'LOGIC_AND_PRIME']],
            'LOGIC_AND_PRIME': [['&&', 'EQUALITY', 'LOGIC_AND_PRIME'], ['epsilon']],

            'EQUALITY': [['COMPARISON', 'EQUALITY_PRIME']],
            'EQUALITY_PRIME': [
                ['==', 'COMPARISON', 'EQUALITY_PRIME'],
                ['!=', 'COMPARISON', 'EQUALITY_PRIME'],
                ['epsilon']
            ],

            'COMPARISON': [['TERM', 'COMPARISON_PRIME']],
            'COMPARISON_PRIME': [
                ['>', 'TERM', 'COMPARISON_PRIME'],
                ['<', 'TERM', 'COMPARISON_PRIME'],
                ['>=', 'TERM', 'COMPARISON_PRIME'],
                ['<=', 'TERM', 'COMPARISON_PRIME'],
                ['epsilon']
            ],

            'TERM': [['FACTOR', 'TERM_PRIME']],
            'TERM_PRIME': [
                ['+', 'FACTOR', 'TERM_PRIME'],
                ['-', 'FACTOR', 'TERM_PRIME'],
                ['epsilon']
            ],

            'FACTOR': [['UNARY', 'FACTOR_PRIME']],
            'FACTOR_PRIME': [
                ['*', 'UNARY', 'FACTOR_PRIME'],
                ['/', 'UNARY', 'FACTOR_PRIME'],
                ['%', 'UNARY', 'FACTOR_PRIME'],
                ['epsilon']
            ],

            'UNARY': [['!', 'UNARY'], ['-', 'UNARY'], ['PRIMARY']],

            'PRIMARY': [
                ['id'],
                ['constant'],
                ['literal'],
                ['(', 'E', ')']
            ]
        }

    # -------------------------
    # UTILS
    # -------------------------

    def get_productions_for(self, non_terminal):
        return self.productions.get(non_terminal, [])

    def display_in_window(self):
        root = tk.Tk()
        root.title("C-Pure Grammar (Final)")
        root.geometry("650x750")

        label = tk.Label(root, text="Formal Grammar (BNF)",
                         font=("Arial", 14, "bold"))
        label.pack(pady=10)

        text_area = scrolledtext.ScrolledText(
            root,
            width=80,
            height=40,
            font=("Courier New", 10)
        )
        text_area.pack(padx=10, pady=10)

        grammar_text = f"Start Symbol: {self.start_symbol}\n"
        grammar_text += "=" * 50 + "\n\n"

        for nt, prods in self.productions.items():
            formatted = " | ".join([" ".join(p) for p in prods])
            grammar_text += f"<{nt}> ::= {formatted}\n\n"

        text_area.insert(tk.INSERT, grammar_text)
        text_area.configure(state='disabled')

        root.mainloop()


if __name__ == "__main__":
    g = Grammar()
    g.display_in_window()