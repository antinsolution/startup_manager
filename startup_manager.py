
import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import winreg

HKCU_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
HKLM_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"


class StartupManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Startup Manager")
        self.root.geometry("950x550")

        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        self.path_var = tk.StringVar()

        tk.Entry(top, textvariable=self.path_var).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )

        tk.Button(top, text="Browse", command=self.browse).pack(side="left", padx=2)
        tk.Button(top, text="Add Startup", command=self.add_startup).pack(side="left", padx=2)
        tk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=2)
        tk.Button(top, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=2)

        columns = ("scope", "name", "command")

        self.tree = ttk.Treeview(root, columns=columns, show="headings")

        self.tree.heading("scope", text="Scope")
        self.tree.heading("name", text="Name")
        self.tree.heading("command", text="Command")

        self.tree.column("scope", width=80, anchor="center")
        self.tree.column("name", width=220)
        self.tree.column("command", width=620)

        yscroll = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        yscroll.pack(side="right", fill="y", pady=(0, 10))

        self.status = tk.Label(root, anchor="w", text="Ready")
        self.status.pack(fill="x", padx=10, pady=(0, 10))

        self.refresh()

    def browse(self):
        filename = filedialog.askopenfilename(
            title="Select program",
            filetypes=[
                ("Executable", "*.exe"),
                ("Batch", "*.bat *.cmd"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.path_var.set(filename)

    def get_entries(self):
        entries = []

        if not IS_WINDOWS:
            return entries

        locations = [
            ("HKCU", winreg.HKEY_CURRENT_USER, HKCU_RUN),
            ("HKLM", winreg.HKEY_LOCAL_MACHINE, HKLM_RUN),
        ]

        for scope, hive, path in locations:
            try:
                key = winreg.OpenKey(hive, path)
                count = winreg.QueryInfoKey(key)[1]

                for i in range(count):
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entries.append((scope, name, value))
                    except OSError:
                        pass

                winreg.CloseKey(key)

            except OSError:
                pass

        return entries

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for scope, name, command in self.get_entries():
            self.tree.insert("", "end", values=(scope, name, command))

        self.status.config(text=f"Loaded {len(self.tree.get_children())} startup entries")

    def add_startup(self):
        if not IS_WINDOWS:
            messagebox.showerror("Unsupported", "This feature only works on Windows.")
            return

        path = self.path_var.get().strip()

        if not path:
            messagebox.showwarning("Warning", "Select a file first.")
            return

        if not os.path.exists(path):
            messagebox.showerror("Error", "File does not exist.")
            return

        name = os.path.splitext(os.path.basename(path))[0]

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                HKCU_RUN,
                0,
                winreg.KEY_SET_VALUE,
            )

            winreg.SetValueEx(
                key,
                name,
                0,
                winreg.REG_SZ,
                f'"{path}"'
            )

            winreg.CloseKey(key)

            self.refresh()
            messagebox.showinfo("Success", f"Added '{name}' to startup.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_selected(self):
        if not IS_WINDOWS:
            return

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Select an entry first.")
            return

        values = self.tree.item(selected[0])["values"]

        scope = values[0]
        name = values[1]

        hive = (
            winreg.HKEY_CURRENT_USER
            if scope == "HKCU"
            else winreg.HKEY_LOCAL_MACHINE
        )

        try:
            key = winreg.OpenKey(
                hive,
                HKCU_RUN,
                0,
                winreg.KEY_SET_VALUE,
            )

            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)

            self.refresh()

            messagebox.showinfo(
                "Success",
                f"Removed startup entry:\n{name}"
            )

        except PermissionError:
            messagebox.showerror(
                "Permission Denied",
                "Administrator rights may be required."
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    StartupManager(root)
    root.mainloop()
