import customtkinter as ctk
import mpmath as mp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy as sp

mp.mp.prec = 10**31

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

class ScientificCalculator(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Scientific Calculator")
        self.geometry("500x800")
        self.configure(bg_color="#1e1e1e")
        
        # Use a StringVar to back the entry widget.
        self.expr_var = ctk.StringVar()
        self.expr_var.set("")
        self.expression = ""  # Internal representation
        
        self.shift_mode = False
        # Mapping: when shift is on, these digit buttons represent letters.
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
        
        # Editable entry widget.
        self.entry = ctk.CTkEntry(self, textvariable=self.expr_var, font=("Arial", 24),
                                   justify="right", height=50)
        self.entry.grid(row=0, column=0, columnspan=4, padx=20, pady=20, sticky="nsew")
        # Bind Return, Escape, and Backspace on the entry.
        self.entry.bind("<Return>", lambda event: (self.click("="), "break"))
        self.entry.bind("<Escape>", lambda event: (self.click("C"), "break"))
        self.entry.bind("<BackSpace>", lambda event: (self.click("Del"), "break"))
        # Bind Ctrl+G for graph.
        self.bind_all("<Control-g>", lambda event: self.graph_expression())
        
        # On-screen shift toggle button.
        self.shift_button = ctk.CTkButton(self, text="Shift Off", font=("Arial", 18),
                                          corner_radius=10, command=self.toggle_shift, height=50)
        self.shift_button.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        
        # Define button layout.
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
        row_index = 2
        for row in buttons:
            if len(row) == 4:
                for col_index, btn_text in enumerate(row):
                    widget = self.create_button_widget(btn_text)
                    widget.grid(row=row_index, column=col_index, padx=10, pady=10, sticky="nsew")
                row_index += 1
            elif len(row) == 2:
                for i, btn_text in enumerate(row):
                    widget = self.create_button_widget(btn_text)
                    col_index = i * 2
                    widget.grid(row=row_index, column=col_index, columnspan=2, padx=10, pady=10, sticky="nsew")
                row_index += 1
            elif len(row) == 1:
                widget = self.create_button_widget(row[0])
                widget.grid(row=row_index, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
                row_index += 1

        for i in range(row_index):
            self.grid_rowconfigure(i, weight=1)
        for j in range(4):
            self.grid_columnconfigure(j, weight=1)
        
        # Trace changes to the entry so that internal expression is kept in sync.
        self.expr_var.trace("w", self.on_expr_var_change)

    def on_expr_var_change(self, *args):
        # Update internal expression when the user edits the entry.
        self.expression = self.expr_var.get()

    def create_button_widget(self, btn_text):
        """Return a CTkButton with appropriate display text.
           For digit buttons with a shift mapping, display as '7 (x)'."""
        command = lambda x=btn_text: self.click(x)
        if btn_text in self.shift_mapping:
            display_text = f"{btn_text} ({self.shift_mapping[btn_text]})"
        else:
            display_text = btn_text
        return ctk.CTkButton(self, text=display_text, font=("Arial", 18),
                             corner_radius=10, command=command, height=50)

    def toggle_shift(self):
        self.shift_mode = not self.shift_mode
        self.shift_button.configure(text="Shift On" if self.shift_mode else "Shift Off")

    def click(self, key):
        # If a button is pressed, update the internal expression and the display.
        if key == "=":
            try:
                expr = self.expression.replace('^', '**')
                result = eval(expr, {"__builtins__": None}, allowed_names)
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
                self.expression = str(converted)
            except Exception:
                self.expression = "Error"
            self._update_display()
        elif key == "toRad":
            try:
                value = mp.mpf(self.expression)
                converted = value * mp.pi / 180
                self.expression = str(converted)
            except Exception:
                self.expression = "Error"
            self._update_display()
        elif key == "Graph":
            self.graph_expression()
        else:
            # When shift mode is active and a digit is pressed, use its mapped letter.
            if key.isdigit() and self.shift_mode:
                key = self.shift_mapping.get(key, key)
            self.expression += key
            self._update_display()

    def _update_display(self):
        # Update the entry widget via the StringVar.
        self.expr_var.set(self.expression)

    def graph_expression(self):
        # Create a new graph window.
        self.graph_window = ctk.CTkToplevel(self)
        self.graph_window.title("Graph Options")
        self.graph_window.geometry("600x550")
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
        plot_button = ctk.CTkButton(domain_frame, text="Plot Graph", command=self.plot_graph)
        plot_button.grid(row=1, column=2, columnspan=2, padx=5, pady=5)
        self.graph_frame = ctk.CTkFrame(self.graph_window)
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def plot_graph(self):
        try:
            x_min = float(self.x_min_entry.get())
            x_max = float(self.x_max_entry.get())
        except Exception:
            x_min, x_max = -10, 10
        var = self.var_entry.get().strip() or "x"
        if not self.expression.strip():
            return
        expr_str = self.expression.replace('^', '**')
        sympy_locals = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                        "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt,
                        "exp": sp.exp, "pi": sp.pi, "e": sp.E}
        try:
            symbol = sp.symbols(var)
        except Exception:
            return
        try:
            expr_sym = sp.sympify(expr_str, locals=sympy_locals)
        except Exception:
            return
        try:
            f = sp.lambdify(symbol, expr_sym, "numpy")
        except Exception:
            return
        x_vals = np.linspace(x_min, x_max, 400)
        try:
            y_vals = f(x_vals)
            if np.isscalar(y_vals):
                y_vals = np.full_like(x_vals, float(y_vals))
            else:
                y_vals = np.array(y_vals, dtype=np.float64)
                if y_vals.shape != x_vals.shape:
                    y_const = float(y_vals)
                    y_vals = np.full(x_vals.shape, y_const)
        except Exception:
            y_vals = np.full(x_vals.shape, np.nan)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.plot(x_vals, y_vals, color="blue")
        ax.set_xlabel(var)
        ax.set_ylabel("f(" + var + ")")
        ax.grid(True)
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.graph_window.update_idletasks()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = ScientificCalculator()
    app.mainloop()
