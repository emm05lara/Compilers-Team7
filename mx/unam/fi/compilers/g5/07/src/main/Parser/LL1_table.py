"""
LL(1) Predictive Parsing Table Generator
----------------------------------------
Authors:
    Team 7:
    - Alvarez Salgado Eduardo Antonio
    - González Vázquez Alejandro
    - Jiménez Olivo Evelin
    - Lara Hernández Emmanuel
    - Parra Fernández Héctor Emilio

Date: April 28, 2026

Description:
This module automates the construction of the LL(1) Parsing Table M[A, a]. 
It maps Non-Terminal symbols and Lookahead Terminals to their corresponding 
Full Production Rules (Head -> Body).

Functionality:
- Computes the FIRST set for every production's right-hand side.
- Applies LL(1) rules to fill the decision matrix.
- Handles epsilon transitions using FOLLOW sets to resolve empty derivations.
- Provides a GUI visualization using a Spreadsheet-like grid (Treeview).
"""

import tkinter as tk
from tkinter import ttk
from grammar import Grammar
from first_follow import compute_first, compute_follow


class LL1Table:

    def __init__(self, grammar, first_sets, follow_sets):
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = {}
        self.conflicts = []   # 🔥 NUEVO: lista de conflictos
        self._build_table()

    # -----------------------------------
    # FIRST de una secuencia
    # -----------------------------------
    def _get_first_of_sequence(self, sequence):
        res = set()

        for symbol in sequence:
            if symbol == 'epsilon':
                res.add('epsilon')
                break

            if symbol not in self.grammar.non_terminals:
                res.add(symbol)
                break

            res.update(self.first[symbol] - {'epsilon'})

            if 'epsilon' not in self.first[symbol]:
                break
        else:
            res.add('epsilon')

        return res

    # -----------------------------------
    # INSERT con detección de conflictos
    # -----------------------------------
    def _insert(self, nt, terminal, production):
        if terminal in self.table[nt]:
            conflict_msg = (
                f"Conflict detected at M[{nt}, {terminal}]\n"
                f"  Existing: {self.table[nt][terminal]}\n"
                f"  New:      {production}"
            )

            print(conflict_msg)
            self.conflicts.append(conflict_msg)  # 🔥 guardarlo

        else:
            self.table[nt][terminal] = production

    # -----------------------------------
    # Construcción de la tabla LL(1)
    # -----------------------------------
    def _build_table(self):

        for nt in self.grammar.non_terminals:
            self.table[nt] = {}

            for prod in self.grammar.get_productions_for(nt):

                first_alpha = self._get_first_of_sequence(prod)
                full_prod_str = f"{nt} -> {' '.join(prod)}"

                # -------------------------
                # Regla 1: FIRST
                # -------------------------
                for terminal in first_alpha:
                    if terminal != 'epsilon':
                        self._insert(nt, terminal, full_prod_str)

                # -------------------------
                # Regla 2: FOLLOW
                # -------------------------
                if 'epsilon' in first_alpha:
                    for terminal in self.follow[nt]:
                        self._insert(nt, terminal, full_prod_str)

    # -----------------------------------
    # Mostrar en GUI
    # -----------------------------------
    def display_gui(self):

        window = tk.Toplevel()
        window.title("LL(1) Parsing Table")
        window.geometry("1100x600")

        terminals = sorted(list(self.grammar.terminals))

        if '$' not in terminals:
            terminals.append('$')

        if 'epsilon' in terminals:
            terminals.remove('epsilon')

        columns = ["NT"] + terminals

        container = tk.Frame(window)
        container.pack(expand=True, fill='both')

        tree = ttk.Treeview(container, columns=columns, show='headings')

        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # encabezados
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')

        # llenar tabla
        for nt in sorted(self.table.keys()):
            row = [nt]
            for t in terminals:
                row.append(self.table[nt].get(t, ""))
            tree.insert("", tk.END, values=row)

        # 🔥 mostrar conflictos en consola
        if self.conflicts:
            print("\n⚠️ GRAMMAR IS NOT LL(1)\n")
        else:
            print("\n✅ Grammar is LL(1)\n")


# -----------------------------------
# MAIN TEST
# -----------------------------------
if __name__ == "__main__":
    g = Grammar()

    first_res = compute_first(g.productions, g.non_terminals)
    follow_res = compute_follow(g.productions, g.non_terminals, first_res, g.start_symbol)

    table = LL1Table(g, first_res, follow_res)

    root = tk.Tk()
    root.withdraw()

    table.display_gui()

    root.mainloop()