import customtkinter as ctk
import mpmath as mp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

# Set extremely high precision (10^31 bits)
mp.mp.prec = 10**31

# Allowed names for mpmath evaluation
allowed_names = { 
    "sin": mp.sin,
    "cos": mp.cos,
    "tan": mp.tan,
    "log": lambda x: mp.log(x, 10),
    "ln": mp.log,
    "sqrt": mp.sqrt,
    "exp": mp.exp,
    "pi": mp.pi,
    "e": mp.e
}

# Use transformations to support implicit multiplication (e.g., "2x" -> "2*x")
transformations = standard_transformations + (implicit_multiplication_application,)

class AdvancedScientificCalculator(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Extremely Advanced Scientific Calculator")
        self.geometry("1200x900")
        self.configure(bg_color="#1e1e1e")
        self.attributes("-topmost", True)
        
        # Internal state
        self.expression = ""
        self.history = []
        self.shift_mode = False
        self.memory = 0
        
        # Shift mapping for digit buttons (for alternative variable insertion)
        self.shift_mapping = {
            "7": "x", "8": "y", "9": "z",
            "4": "a", "5": "b", "6": "c",
            "1": "d", "2": "e", "3": "f",
            "0": "g"
        }
        self.func_map = {
            "sin": "sin(", "cos": "cos(", "tan": "tan(",
            "log": "log(", "ln": "ln(", "√": "sqrt(",
            "exp": "exp(", "x^y": "^"
        }
        
        # Top menu frame with advanced function buttons
        menu_frame = ctk.CTkFrame(self, fg_color="#2e2e2e", corner_radius=10)
        menu_frame.grid(row=0, column=0, columnspan=10, padx=10, pady=10, sticky="nsew")
        self.diff_button = ctk.CTkButton(menu_frame, text="Differentiate", command=self.differentiate_expression, width=120)
        self.diff_button.grid(row=0, column=0, padx=5, pady=5)
        self.int_button = ctk.CTkButton(menu_frame, text="Integrate", command=self.integrate_expression, width=120)
        self.int_button.grid(row=0, column=1, padx=5, pady=5)
        self.solve_button = ctk.CTkButton(menu_frame, text="Solve Eqn", command=self.solve_equation, width=120)
        self.solve_button.grid(row=0, column=2, padx=5, pady=5)
        self.ode_button = ctk.CTkButton(menu_frame, text="Solve ODE", command=self.solve_ode, width=120)
        self.ode_button.grid(row=0, column=3, padx=5, pady=5)
        self.fourier_button = ctk.CTkButton(menu_frame, text="Fourier", command=self.fourier_transform, width=120)
        self.fourier_button.grid(row=0, column=4, padx=5, pady=5)
        self.latex_button = ctk.CTkButton(menu_frame, text="LaTeX Render", command=self.latex_render, width=120)
        self.latex_button.grid(row=0, column=5, padx=5, pady=5)
        self.matrix_button = ctk.CTkButton(menu_frame, text="Matrix Ops", command=self.matrix_operations, width=120)
        self.matrix_button.grid(row=0, column=6, padx=5, pady=5)
        self.mem_clear = ctk.CTkButton(menu_frame, text="MC", command=self.memory_clear, width=60)
        self.mem_clear.grid(row=0, column=7, padx=5, pady=5)
        self.mem_recall = ctk.CTkButton(menu_frame, text="MR", command=self.memory_recall, width=60)
        self.mem_recall.grid(row=0, column=8, padx=5, pady=5)
        self.mem_add = ctk.CTkButton(menu_frame, text="M+", command=self.memory_add, width=60)
        self.mem_add.grid(row=0, column=9, padx=5, pady=5)
        self.mem_sub = ctk.CTkButton(menu_frame, text="M-", command=self.memory_subtract, width=60)
        self.mem_sub.grid(row=0, column=10, padx=5, pady=5)

        # Editable expression entry
        self.expr_var = ctk.StringVar(value="")
        self.entry = ctk.CTkEntry(self, textvariable=self.expr_var, font=("Arial", 24),
                                   justify="right", height=50)
        self.entry.grid(row=1, column=0, columnspan=10, padx=20, pady=10, sticky="nsew")
        self.entry.bind("<KeyRelease>", self.update_expression_from_entry)
        
        # Basic shift toggle button
        self.shift_button = ctk.CTkButton(self, text="Shift Off", font=("Arial", 18),
                                          command=self.toggle_shift, height=50)
        self.shift_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Basic calculator buttons layout
        buttons = [
            ["sin", "cos", "tan", "log"],
            ["ln", "√", "x^y", "exp"],
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "+"],
            ["-", "0", ".", "("],
            [")", "pi", "e", "C"],
            ["=", "Del", "toDeg", "toRad"],
            ["Graph"]
        ]
        row_index = 3
        for row in buttons:
            for col_index, btn_text in enumerate(row):
                widget = self.create_button_widget(btn_text)
                widget.grid(row=row_index, column=col_index, padx=5, pady=5, sticky="nsew")
            row_index += 1

        # History panel on the right
        self.history_box = ctk.CTkTextbox(self, font=("Arial", 12))
        self.history_box.grid(row=1, column=10, rowspan=row_index, padx=10, pady=10, sticky="nsew")
        self.history_box.insert("0.0", "History:\n")
        self.history_box.configure(state="disabled")

        # Configure grid weights
        for i in range(row_index+1):
            self.grid_rowconfigure(i, weight=1)
        for j in range(11):
            self.grid_columnconfigure(j, weight=1)

        # Bind keyboard events and Ctrl+G for graph
        self.bind_all("<Key>", self.handle_key)
        self.bind_all("<Control-g>", lambda event: self.graph_expression())

    def update_expression_from_entry(self, event):
        self.expression = self.expr_var.get()

    def create_button_widget(self, btn_text):
        command = lambda x=btn_text: self.click(x)
        if btn_text in self.shift_mapping:
            display_text = f"{btn_text} ({self.shift_mapping[btn_text]})"
        else:
            display_text = btn_text
        return ctk.CTkButton(self, text=display_text, font=("Arial", 18),
                             command=command, height=50)

    def toggle_shift(self):
        self.shift_mode = not self.shift_mode
        self.shift_button.configure(text="Shift On" if self.shift_mode else "Shift Off")

    def click(self, key):
        if key == "=":
            try:
                expr = self.expression.replace('^', '**')
                # Parse using implicit multiplication transformation for human-friendly input
                expr_sym = parse_expr(expr, transformations=transformations)
                result = eval(str(expr_sym), {"__builtins__": None}, allowed_names)
                self.add_history(f"{expr} = {result}")
                self.expression = str(result)
            except Exception:
                self.expression = "Error"
            self._update_display()
        elif key == "C":
            self.expression = ""
            self._update_display()
        elif key == "Del":
            self.expression = self.expression[:-1]
            self._update_display()
        elif key == "toDeg":
            try:
                value = mp.mpf(self.expression)
                converted = value * 180 / mp.pi
                self.add_history(f"toDeg({self.expression}) = {converted}")
                self.expression = str(converted)
            except Exception:
                self.expression = "Error"
            self._update_display()
        elif key == "toRad":
            try:
                value = mp.mpf(self.expression)
                converted = value * mp.pi / 180
                self.add_history(f"toRad({self.expression}) = {converted}")
                self.expression = str(converted)
            except Exception:
                self.expression = "Error"
            self._update_display()
        elif key == "Graph":
            self.graph_expression()
        else:
            if key.isdigit() and self.shift_mode:
                key = self.shift_mapping.get(key, key)
            self.expression += key
            self._update_display()

    def _update_display(self):
        self.expr_var.set(self.expression)

    def add_history(self, text):
        self.history.append(text)
        self.history_box.configure(state="normal")
        self.history_box.insert("end", text + "\n")
        self.history_box.configure(state="disabled")
        self.history_box.see("end")

    def differentiate_expression(self):
        var = "x"
        try:
            symbol = sp.symbols(var)
            expr_sym = parse_expr(self.expression, transformations=transformations)
            diff_expr = sp.diff(expr_sym, symbol)
            result = sp.N(diff_expr)
            self.add_history(f"d/d{var}({self.expression}) = {result}")
            self.expression = str(result)
        except Exception:
            self.expression = "Error"
        self._update_display()

    def integrate_expression(self):
        var = "x"
        try:
            symbol = sp.symbols(var)
            expr_sym = parse_expr(self.expression, transformations=transformations)
            int_expr = sp.integrate(expr_sym, symbol)
            result = sp.N(int_expr)
            self.add_history(f"∫({self.expression}) d{var} = {result}")
            self.expression = str(result)
        except Exception:
            self.expression = "Error"
        self._update_display()

    def solve_equation(self):
        var = "x"
        try:
            if "=" in self.expression:
                lhs, rhs = self.expression.split("=")
                eq_expr = sp.Eq(parse_expr(lhs, transformations=transformations),
                                  parse_expr(rhs, transformations=transformations))
            else:
                eq_expr = sp.Eq(parse_expr(self.expression, transformations=transformations), 0)
            symbol = sp.symbols(var)
            solutions = sp.solve(eq_expr, symbol)
            self.add_history(f"Solve({self.expression}) = {solutions}")
            self.expression = str(solutions)
        except Exception:
            self.expression = "Error"
        self._update_display()

    import re

    def solve_ode(self):
        try:
            # Define symbols and function for ODE solving.
            x = sp.symbols("x")
            y = sp.Function("y")
            # Clean and prepare the input.
            ode_input = self.expression.strip()
            # Replace any form of "dy/dx" (ignoring spaces) with the proper derivative notation.
            ode_input = re.sub(r"d\s*y\s*/\s*d\s*x", "Derivative(y(x), x)", ode_input, flags=re.IGNORECASE)
            # Split the equation at the first "=" sign.
            match = re.match(r"(.+?)=(.+)", ode_input)
            if match:
                lhs = match.group(1).strip()
                rhs = match.group(2).strip()
                # Replace bare 'y' with 'y(x)' in the right-hand side.
                rhs = re.sub(r"\by\b(?!\()", "y(x)", rhs)
                local_dict = {"x": x, "y": y, "Derivative": sp.Derivative}
                lhs_expr = parse_expr(lhs, local_dict=local_dict, transformations=transformations)
                rhs_expr = parse_expr(rhs, local_dict=local_dict, transformations=transformations)
                ode_sym = sp.Eq(lhs_expr, rhs_expr)
            else:
                # If no '=' is found, assume the expression equals zero.
                local_dict = {"x": x, "y": y, "Derivative": sp.Derivative}
                ode_expr = parse_expr(ode_input, local_dict=local_dict, transformations=transformations)
                ode_sym = sp.Eq(ode_expr, 0)
            sol = sp.dsolve(ode_sym)
            self.add_history(f"Solve ODE({self.expression}) = {sol}")
            self.expression = str(sol.rhs) if hasattr(sol, "rhs") else str(sol)
        except Exception as e:
            self.expression = "Error: " + str(e)
        self._update_display()




    def fourier_transform(self):
        # Compute the Fourier transform of the given expression with respect to x
        var = sp.symbols("x")
        w = sp.symbols("w")
        try:
            expr_sym = parse_expr(self.expression, transformations=transformations)
            ft = sp.fourier_transform(expr_sym, var, w)
            self.add_history(f"Fourier({self.expression}) = {ft}")
            self.expression = str(ft)
        except Exception:
            self.expression = "Error"
        self._update_display()

    def latex_render(self):
        # Render the current expression as LaTeX in a pop-up window.
        try:
            expr_sym = parse_expr(self.expression, transformations=transformations)
            latex_str = sp.latex(expr_sym)
        except Exception:
            latex_str = "Error"
        latex_window = ctk.CTkToplevel(self)
        latex_window.title("LaTeX Render")
        latex_window.geometry("600x200")
        label = ctk.CTkLabel(latex_window, text=latex_str, font=("Arial", 16), wraplength=580)
        label.pack(padx=10, pady=10)
        self.add_history(f"LaTeX Render: {latex_str}")

    def matrix_operations(self):
        # Basic matrix operations: determinant and inverse.
        try:
            expr_sym = parse_expr(self.expression, transformations=transformations)
            det = expr_sym.det() if hasattr(expr_sym, "det") else "N/A"
            inv = expr_sym.inv() if hasattr(expr_sym, "inv") else "N/A"
            self.add_history(f"Matrix Det: {det}\nMatrix Inv: {inv}")
            self.expression = f"Det: {det}"
        except Exception:
            self.expression = "Error"
        self._update_display()

    def memory_clear(self):
        self.memory = 0
        self.add_history("Memory Cleared")

    def memory_recall(self):
        self.expression += str(self.memory)
        self._update_display()
        self.add_history(f"Memory Recalled: {self.memory}")

    def memory_add(self):
        try:
            value = float(eval(self.expression.replace('^', '**'), {"__builtins__": None}, allowed_names))
            self.memory += value
            self.add_history(f"Memory Added: {value} -> {self.memory}")
        except Exception:
            self.add_history("Memory Add Error")

    def memory_subtract(self):
        try:
            value = float(eval(self.expression.replace('^', '**'), {"__builtins__": None}, allowed_names))
            self.memory -= value
            self.add_history(f"Memory Subtracted: {value} -> {self.memory}")
        except Exception:
            self.add_history("Memory Subtract Error")

    def handle_key(self, event):
        if event.keysym == "Return":
            self.click("=")
            return "break"
        elif event.keysym == "BackSpace":
            self.click("Del")
            return "break"
        elif event.keysym == "Escape":
            self.click("C")
            return "break"
        else:
            return

    def graph_expression(self):
        self.graph_window = ctk.CTkToplevel(self)
        self.graph_window.title("Graph Options")
        self.graph_window.attributes("-topmost", True)
        self.graph_window.geometry("700x600")
        domain_frame = ctk.CTkFrame(self.graph_window)
        domain_frame.pack(padx=10, pady=10, fill="x")
        x_min_label = ctk.CTkLabel(domain_frame, text="X min:")
        x_min_label.grid(row=0, column=0, padx=5, pady=5)
        self.x_min_entry = ctk.CTkEntry(domain_frame, width=80)
        self.x_min_entry.grid(row=0, column=1, padx=5, pady=5)
        self.x_min_entry.insert(0, "-10")
        x_max_label = ctk.CTkLabel(domain_frame, text="X max:")
        x_max_label.grid(row=0, column=2, padx=5, pady=5)
        self.x_max_entry = ctk.CTkEntry(domain_frame, width=80)
        self.x_max_entry.grid(row=0, column=3, padx=5, pady=5)
        self.x_max_entry.insert(0, "10")
        var_label = ctk.CTkLabel(domain_frame, text="Variable:")
        var_label.grid(row=1, column=0, padx=5, pady=5)
        self.var_entry = ctk.CTkEntry(domain_frame, width=80)
        self.var_entry.grid(row=1, column=1, padx=5, pady=5)
        self.var_entry.insert(0, "x")
        add_func_button = ctk.CTkButton(domain_frame, text="Add Function", command=self.add_function_to_plot)
        add_func_button.grid(row=1, column=2, padx=5, pady=5)
        plot_button = ctk.CTkButton(domain_frame, text="Plot Graph", command=self.plot_graph)
        plot_button.grid(row=1, column=3, padx=5, pady=5)
        
        self.func_list = ctk.CTkTextbox(self.graph_window, font=("Arial", 12))
        self.func_list.pack(padx=10, pady=10, fill="x")
        self.func_list.insert("0.0", "Functions to Plot:\n")
        self.func_list.configure(state="disabled")
        
        self.graph_frame = ctk.CTkFrame(self.graph_window)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def add_function_to_plot(self):
        if self.expression.strip():
            self.func_list.configure(state="normal")
            self.func_list.insert("end", self.expression + "\n")
            self.func_list.configure(state="disabled")
            self.add_history(f"Added function for plotting: {self.expression}")
    
    def plot_graph(self):
        try:
            x_min = float(self.x_min_entry.get())
            x_max = float(self.x_max_entry.get())
        except Exception:
            x_min, x_max = -10, 10
        var = self.var_entry.get().strip() or "x"
        funcs_text = self.func_list.get("1.0", "end").strip().splitlines()[1:]
        all_funcs = []
        if self.expression.strip():
            all_funcs.append(self.expression)
        for f_text in funcs_text:
            if f_text.strip():
                all_funcs.append(f_text.strip())
        if not all_funcs:
            return
        x_vals = np.linspace(x_min, x_max, 400)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        colors = ["blue", "red", "green", "orange", "purple", "brown"]
        for idx, func_expr in enumerate(all_funcs):
            expr_str = func_expr.replace('^', '**')
            sympy_locals = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                            "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt,
                            "exp": sp.exp, "pi": sp.pi, "e": sp.E}
            try:
                symbol = sp.symbols(var)
                expr_sym = parse_expr(expr_str, local_dict=sympy_locals, transformations=transformations)
                f = sp.lambdify(symbol, expr_sym, "numpy")
                y_vals = f(x_vals)
                if np.isscalar(y_vals):
                    y_vals = np.full_like(x_vals, float(y_vals))
                else:
                    y_vals = np.array(y_vals, dtype=np.float64)
                    if y_vals.shape != x_vals.shape:
                        y_const = float(y_vals)
                        y_vals = np.full(x_vals.shape, y_const)
                ax.plot(x_vals, y_vals, color=colors[idx % len(colors)], label=func_expr)
            except Exception as e:
                self.add_history(f"Error plotting {func_expr}: {e}")
        ax.set_xlabel(var)
        ax.set_ylabel("f(" + var + ")")
        ax.grid(True)
        ax.legend()
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.graph_window.update_idletasks()

    def handle_key(self, event):
        if event.keysym == "Return":
            self.click("=")
            return "break"
        elif event.keysym == "BackSpace":
            self.click("Del")
            return "break"
        elif event.keysym == "Escape":
            self.click("C")
            return "break"
        else:
            return

    def memory_clear(self):
        self.memory = 0
        self.add_history("Memory Cleared")

    def memory_recall(self):
        self.expression += str(self.memory)
        self._update_display()
        self.add_history(f"Memory Recalled: {self.memory}")

    def memory_add(self):
        try:
            value = float(eval(self.expression.replace('^', '**'), {"__builtins__": None}, allowed_names))
            self.memory += value
            self.add_history(f"Memory Added: {value} -> {self.memory}")
        except Exception:
            self.add_history("Memory Add Error")

    def memory_subtract(self):
        try:
            value = float(eval(self.expression.replace('^', '**'), {"__builtins__": None}, allowed_names))
            self.memory -= value
            self.add_history(f"Memory Subtracted: {value} -> {self.memory}")
        except Exception:
            self.add_history("Memory Subtract Error")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = AdvancedScientificCalculator()
    app.mainloop()
