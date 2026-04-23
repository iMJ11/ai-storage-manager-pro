import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import time
import shutil
import stat 

# --- Ultra Pro Dark Theme Constants ---
BG_MAIN = "#0d0d0f"       
BG_PANEL = "#1a1a1e"      
FG_TEXT = "#999999"       
FG_HIGHLIGHT = "#ffffff"  
BTN_BG = "#27272b"        
BTN_HOVER = "#3b3b40"     
ACCENT_BLUE = "#005fb8"   
ACCENT_RED = "#d32f2f"    
ACCENT_PURPLE = "#ce93d8" 
ACCENT_GREEN = "#2e7d32"  
SELECT_BG = "#004a94"     

class AIStorageManagerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Storage Manager Pro")
        self.root.geometry("1300x820") 
        self.root.configure(bg=BG_MAIN)

        self.setup_styles()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.tab1 = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab2 = tk.Frame(self.notebook, bg=BG_MAIN)

        self.notebook.add(self.tab1, text="  📁 AI File Cleaner  ")
        self.notebook.add(self.tab2, text="  💽 Smart Disk Analyzer  ")

        # Identification Keywords (Used to tag projects when found)
        self.known_projects_to_hunt = [
            "SAM3D", "WHAM_ENV", "CLIFF", "WAN2GP", "SKYFALL-GS", 
            "UNIRIG", "OLLAMA", "COMFYUI", "DETECTRON2", "FORZAHORIZON", 
            "ROMP", "CHROME_AI", "AUTODESK", "ODIS"
        ]
        
        self.known_categories = [
            "🟢 Safe to Delete (Pure Junk/Temp)",
            "🟣 AI Models (Delete ONLY if unused)",
            "🟡 Dev / Python (Use Conda)",
            "🟠 Installed Apps (Uninstall properly)",
            "⚪ User Data / Custom",
            "🔴 OS / System (DO NOT TOUCH)"
        ]

        self.search_timer = None 
        self.build_tab1()
        self.build_tab2()
        self.apply_tree_colors()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=BG_PANEL, foreground=FG_TEXT, fieldbackground=BG_PANEL, borderwidth=0, rowheight=30, font=("Segoe UI", 9))
        style.map("Treeview", background=[("selected", SELECT_BG)], foreground=[("selected", FG_HIGHLIGHT)])
        style.configure("Treeview.Heading", background=BTN_BG, foreground=FG_HIGHLIGHT, relief="flat", borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("Treeview.Heading", background=[("active", BTN_HOVER)])
        style.configure("Vertical.TScrollbar", background=BTN_BG, troughcolor=BG_MAIN, bordercolor=BG_MAIN, arrowcolor=FG_TEXT, relief="flat")
        style.configure("TCombobox", fieldbackground=BG_PANEL, background=BTN_BG, foreground=FG_HIGHLIGHT, borderwidth=0, arrowsize=15)
        style.map('TCombobox', fieldbackground=[('readonly', BG_PANEL)], selectbackground=[('readonly', ACCENT_BLUE)], selectforeground=[('readonly', FG_HIGHLIGHT)], foreground=[('readonly', FG_HIGHLIGHT)])
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=BTN_BG, foreground=FG_TEXT, padding=[25, 10], font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", ACCENT_BLUE)], foreground=[("selected", FG_HIGHLIGHT)])

    def apply_tree_colors(self):
        for tree in (self.tree1, self.tree2):
            tree.tag_configure("cat_safe", foreground="#81c784")  
            tree.tag_configure("cat_ai", foreground="#ce93d8")    
            tree.tag_configure("cat_sys", foreground="#e57373")   
            tree.tag_configure("cat_dev", foreground="#fff176")   
            tree.tag_configure("cat_app", foreground="#ffb74d")   

    def get_color_tag(self, category):
        if "🟢" in category: return "cat_safe"
        if "🟣" in category: return "cat_ai"
        if "🔴" in category: return "cat_sys"
        if "🟡" in category: return "cat_dev"
        if "🟠" in category: return "cat_app"
        return ""

    def create_button(self, parent, text, command, bg_col=BTN_BG, fg_col=FG_HIGHLIGHT):
        return tk.Button(parent, text=text, command=command, bg=bg_col, fg=fg_col, activebackground=BTN_HOVER, activeforeground=FG_HIGHLIGHT, relief="flat", borderwidth=0, cursor="hand2", padx=20, pady=6, font=("Segoe UI", 9, "bold"))

    def create_entry_field(self, parent, width=20, justify="left"):
        container = tk.Frame(parent, bg=BG_PANEL, padx=8, pady=6)
        entry = tk.Entry(container, width=width, bg=BG_PANEL, fg=FG_HIGHLIGHT, insertbackground=FG_HIGHLIGHT, relief="flat", highlightthickness=0, borderwidth=0, justify=justify, font=("Segoe UI", 10))
        entry.pack(fill=tk.X, expand=True)
        return container, entry

    def format_size(self, size_mb):
        if size_mb >= 1024: return f"{size_mb / 1024:.2f} GB"
        return f"{size_mb:.2f} MB"

    def detect_project(self, path):
        p = path.lower()
        if "google\\chrome" in p and "optguideondevicemodel" in p:
            return "CHROME_AI"
        for proj in self.known_projects_to_hunt:
            if proj.lower() in p:
                return proj
        return "GENERAL"

    def determine_category(self, path, folder_name=""):
        p = path.lower()
        n = folder_name.lower()
        system_temp_markers = ["appdata\\local\\temp", "windows\\temp", "appdata\\local\\crashdumps"]
        if any(marker in p for marker in system_temp_markers): return self.known_categories[0]
        app_cache_markers = ["pip\\cache", "media cache files", "adobe\\common", "autodesk\\odis"]
        if any(marker in p for marker in app_cache_markers): return self.known_categories[0]
        ai_keywords = ["huggingface", ".ollama", "optguideondevicemodel", ".cache\\torch", ".cache\\clip"]
        if any(x in p for x in ai_keywords): return self.known_categories[1]
        dev_keywords = ["miniconda", "anaconda", "\\envs\\", ".venv"]
        if any(x in p for x in dev_keywords): return self.known_categories[2]
        os_keywords = ["windows", "system volume information", "recovery", "$recycle.bin", "perflogs"]
        if n in os_keywords or "c:\\windows" in p: return self.known_categories[5]
        app_paths = ["program files", "programdata", "appdata\\local\\programs"]
        if any(x in p for x in app_paths): return self.known_categories[3]
        return self.known_categories[4]

    def copy_tree_data(self, tree, columns):
        if not tree.get_children(): return
        lines = ["\t".join(columns)]
        for item in tree.get_children():
            lines.append("\t".join(str(v) for v in tree.item(item, "values")))
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        messagebox.showinfo("Copied", "Data copied to clipboard!")

    # ==========================================
    #                 TAB 1 UI
    # ==========================================
    def build_tab1(self):
        top_frame = tk.Frame(self.tab1, bg=BG_MAIN, pady=10)
        top_frame.pack(fill=tk.X)
        row1 = tk.Frame(top_frame, bg=BG_MAIN)
        row1.pack(fill=tk.X, pady=(0, 20))
        tk.Label(row1, text="Target Path:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold"), width=12, anchor="w").pack(side=tk.LEFT)
        c1, self.path_entry1 = self.create_entry_field(row1)
        c1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.create_button(row1, "Browse", self.browse_folder1).pack(side=tk.LEFT, padx=5)
        self.scan_btn1 = self.create_button(row1, "Scan Everything", self.start_scan1, bg_col=ACCENT_BLUE)
        self.scan_btn1.pack(side=tk.LEFT, padx=5)
        row2 = tk.Frame(top_frame, bg=BG_MAIN)
        row2.pack(fill=tk.X)
        tk.Label(row2, text="Filter Name:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold"), width=12, anchor="w").pack(side=tk.LEFT)
        c2, self.search_entry1 = self.create_entry_field(row2, width=15)
        c2.pack(side=tk.LEFT, padx=5)
        self.search_entry1.bind("<KeyRelease>", self.debounce_filter1)
        tk.Label(row2, text="Min Size (MB):", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        c3, self.size_entry1 = self.create_entry_field(row2, width=8, justify="center")
        c3.pack(side=tk.LEFT, padx=5)
        self.size_entry1.insert(0, "0") 
        tk.Label(row2, text="Extension:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.type_combo1 = ttk.Combobox(row2, values=["All Files", "AI Models", "Junk", "3D Assets", "Media"], state="readonly", width=18)
        self.type_combo1.current(0); self.type_combo1.pack(side=tk.LEFT, padx=5, ipady=4)
        self.type_combo1.bind("<<ComboboxSelected>>", self.debounce_filter1)
        mid_frame = tk.Frame(self.tab1, bg=BG_MAIN, pady=10); mid_frame.pack(fill=tk.BOTH, expand=True)
        cols = ("Name", "Size", "Project", "Category", "Full Path")
        self.tree1 = ttk.Treeview(mid_frame, columns=cols, show="headings", style="Treeview")
        for col in cols: self.tree1.heading(col, text=col, command=lambda _col=col: self.sort_column1(_col, False))
        self.tree1.column("Name", width=250); self.tree1.column("Size", width=80, anchor=tk.E)
        self.tree1.column("Project", width=120); self.tree1.column("Category", width=250)
        self.tree1.column("Full Path", width=400)
        scroll = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.tree1.yview)
        self.tree1.configure(yscroll=scroll.set); scroll.pack(side=tk.RIGHT, fill=tk.Y); self.tree1.pack(fill=tk.BOTH, expand=True)
        self.ctx_menu1 = tk.Menu(self.root, tearoff=0, bg=BG_PANEL, fg=FG_HIGHLIGHT, activebackground=ACCENT_BLUE, relief="flat", borderwidth=0)
        self.ctx_menu1.add_command(label="Open File Location", command=self.open_location1)
        self.tree1.bind("<Button-3>", lambda e: self.show_menu(e, self.tree1, self.ctx_menu1))
        bot_frame = tk.Frame(self.tab1, bg=BG_MAIN, pady=15); bot_frame.pack(fill=tk.X)
        self.status1 = tk.Label(bot_frame, text="System Ready", bg=BG_MAIN, fg="#555555", font=("Segoe UI", 10))
        self.status1.pack(side=tk.LEFT)
        self.create_button(bot_frame, "Delete Selected", self.delete_selected1, bg_col=ACCENT_RED).pack(side=tk.RIGHT, padx=5)
        self.create_button(bot_frame, "📋 Export List", lambda: self.copy_tree_data(self.tree1, cols), bg_col=ACCENT_GREEN).pack(side=tk.RIGHT, padx=5)
        self.file_data1 = [] 

    def browse_folder1(self):
        folder = filedialog.askdirectory()
        if folder: self.path_entry1.delete(0, tk.END); self.path_entry1.insert(0, folder)

    def start_scan1(self):
        self.scan_btn1.config(state=tk.DISABLED); self.status1.config(text="Scanning deep system directories...", fg=ACCENT_BLUE)
        self.tree1.delete(*self.tree1.get_children()); threading.Thread(target=self.scan_bg1, daemon=True).start()

    def scan_bg1(self):
        folder = self.path_entry1.get().strip()
        if not os.path.isdir(folder): self.root.after(0, lambda: self.scan_btn1.config(state=tk.NORMAL)); return
        try: min_size = float(self.size_entry1.get())
        except: min_size = 0.0
        self.file_data1 = []
        start_time = time.time()
        def fast_scan(path):
            try:
                for entry in os.scandir(path):
                    try:
                        if entry.is_dir(follow_symlinks=False): fast_scan(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            smb = entry.stat().st_size / (1024 * 1024)
                            if smb >= min_size:
                                proj = self.detect_project(entry.path)
                                cat = self.determine_category(entry.path, entry.name)
                                self.file_data1.append((entry.name, smb, proj, cat, entry.path))
                    except: pass
            except: pass
        fast_scan(folder); elapsed = int(time.time() - start_time); self.root.after(0, lambda: self.refresh_table1(elapsed))

    def debounce_filter1(self, event=None):
        if self.search_timer: self.root.after_cancel(self.search_timer)
        self.search_timer = self.root.after(300, self.refresh_table1)

    def refresh_table1(self, elapsed_time=""):
        self.tree1.delete(*self.tree1.get_children()); search_name = self.search_entry1.get().lower().strip()
        display_count = 0; max_display = 3000
        for item in self.file_data1:
            if display_count >= max_display: break
            if search_name and search_name not in item[0].lower(): continue
            display_count += 1; col_tag = self.get_color_tag(item[3])
            self.tree1.insert("", tk.END, values=(item[0], self.format_size(item[1]), item[2], item[3], item[4]), tags=(item[4], col_tag))
        self.status1.config(text=f"Showing {display_count} files.", fg="#4caf50"); self.scan_btn1.config(state=tk.NORMAL)

    def sort_column1(self, col, reverse):
        col_idx = ("Name", "Size", "Project", "Category", "Full Path").index(col)
        if col == "Size": self.file_data1.sort(key=lambda x: x[1], reverse=reverse)
        else: self.file_data1.sort(key=lambda x: str(x[col_idx]).lower(), reverse=reverse)
        self.refresh_table1(); self.tree1.heading(col, command=lambda: self.sort_column1(col, not reverse))

    def show_menu(self, event, tree, menu):
        row_id = tree.identify_row(event.y)
        if row_id: tree.selection_set(row_id); menu.post(event.x_root, event.y_root)

    def open_location1(self):
        sel = self.tree1.selection()
        if sel: subprocess.Popen(f'explorer /select,"{os.path.normpath(self.tree1.item(sel[0], "tags")[0])}"')

    def delete_selected1(self):
        sel = self.tree1.selection()
        if not sel: return
        safe_to_delete = []
        for item in sel:
            if "🔴" not in self.tree1.item(item, "values")[3]: safe_to_delete.append(item)
        if not safe_to_delete: return
        if messagebox.askyesno("Confirm", f"Wipe {len(safe_to_delete)} files?"):
            for item in safe_to_delete:
                path = self.tree1.item(item, "tags")[0]
                try:
                    os.chmod(path, stat.S_IWRITE); os.remove(path)
                    if not os.path.exists(path): self.file_data1 = [f for f in self.file_data1 if f[4] != path]
                except: pass
            self.refresh_table1()

    # ==========================================
    #                 TAB 2 UI
    # ==========================================
    def build_tab2(self):
        top_frame = tk.Frame(self.tab2, bg=BG_MAIN, pady=10)
        top_frame.pack(fill=tk.X)
        row1 = tk.Frame(top_frame, bg=BG_MAIN)
        row1.pack(fill=tk.X, pady=(0, 20))
        tk.Label(row1, text="System Drive:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold"), width=12, anchor="w").pack(side=tk.LEFT)
        c4, self.path_entry2 = self.create_entry_field(row1)
        c4.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry2.insert(0, "C:\\")
        self.create_button(row1, "Browse", self.browse_folder2).pack(side=tk.LEFT, padx=5)
        self.scan_btn2 = self.create_button(row1, "Deep Analyze Disk", self.start_scan2, bg_col=ACCENT_BLUE)
        self.scan_btn2.pack(side=tk.LEFT, padx=5)

        # Row 2 with Dynamic Project Dropdown and Added Size Limit
        row2 = tk.Frame(top_frame, bg=BG_MAIN)
        row2.pack(fill=tk.X)

        tk.Label(row2, text="By Project:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold"), width=12, anchor="w").pack(side=tk.LEFT)
        self.proj_combo2 = ttk.Combobox(row2, values=["All Projects"], state="readonly", width=18)
        self.proj_combo2.current(0); self.proj_combo2.pack(side=tk.LEFT, padx=5, ipady=4)
        self.proj_combo2.bind("<<ComboboxSelected>>", lambda e: self.refresh_table2())

        # NEW: Min Size Filter in Analyzer
        tk.Label(row2, text="Min Size (MB):", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        c5, self.size_entry2 = self.create_entry_field(row2, width=8, justify="center")
        c5.pack(side=tk.LEFT, padx=5); self.size_entry2.insert(0, "0")
        self.size_entry2.bind("<KeyRelease>", lambda e: self.refresh_table2())

        tk.Label(row2, text="Category:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        self.cat_combo2 = ttk.Combobox(row2, values=["All Categories"] + self.known_categories, state="readonly", width=35)
        self.cat_combo2.current(0); self.cat_combo2.pack(side=tk.LEFT, padx=5, ipady=4)
        self.cat_combo2.bind("<<ComboboxSelected>>", lambda e: self.refresh_table2())
        
        self.create_button(row2, "🔄 Rescan System", self.start_scan2).pack(side=tk.LEFT, padx=20)
        
        mid_frame = tk.Frame(self.tab2, bg=BG_MAIN, pady=10); mid_frame.pack(fill=tk.BOTH, expand=True)
        cols = ("Folder Name", "Total Size", "Project", "Category", "Full Path")
        self.tree2 = ttk.Treeview(mid_frame, columns=cols, show="headings", style="Treeview")
        for col in cols: self.tree2.heading(col, text=col, command=lambda _col=col: self.sort_column2(_col, False))
        self.tree2.column("Folder Name", width=200); self.tree2.column("Total Size", width=80, anchor=tk.E)
        self.tree2.column("Project", width=120); self.tree2.column("Category", width=250)
        self.tree2.column("Full Path", width=400)
        scroll = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.tree2.yview); scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree2.configure(yscroll=scroll.set); self.tree2.pack(fill=tk.BOTH, expand=True)
        self.ctx_menu2 = tk.Menu(self.root, tearoff=0, bg=BG_PANEL, fg=FG_HIGHLIGHT, activebackground=ACCENT_BLUE, relief="flat", borderwidth=0)
        self.ctx_menu2.add_command(label="Open Folder Location", command=self.open_location2)
        self.tree2.bind("<Button-3>", lambda e: self.show_menu(e, self.tree2, self.ctx_menu2))
        bot_frame = tk.Frame(self.tab2, bg=BG_MAIN, pady=15); bot_frame.pack(fill=tk.X)
        self.status2 = tk.Label(bot_frame, text="Ready", bg=BG_MAIN, fg="#555555", font=("Segoe UI", 10))
        self.status2.pack(side=tk.LEFT)
        self.create_button(bot_frame, "Turbo Delete", self.delete_selected2, bg_col=ACCENT_RED).pack(side=tk.RIGHT, padx=5)
        self.create_button(bot_frame, "📋 Export List", lambda: self.copy_tree_data(self.tree2, cols), bg_col=ACCENT_GREEN).pack(side=tk.RIGHT, padx=5)
        self.file_data2 = [] 

    def browse_folder2(self):
        folder = filedialog.askdirectory()
        if folder: self.path_entry2.delete(0, tk.END); self.path_entry2.insert(0, folder)

    def start_scan2(self):
        self.scan_btn2.config(state=tk.DISABLED); self.status2.config(text="Deep Scanning entire drive... Please wait.", fg=ACCENT_PURPLE)
        self.tree2.delete(*self.tree2.get_children()); threading.Thread(target=self.scan_bg2, daemon=True).start()

    def scan_bg2(self):
        root_path = self.path_entry2.get().strip()
        if not os.path.isdir(root_path): self.root.after(0, lambda: self.scan_btn2.config(state=tk.NORMAL)); return
        folder_sizes = {}; restricted = ["recovery", "system volume information", "$recycle.bin", "windowsapps"]
        def fast_scan_sizes(path):
            total = 0
            try:
                for entry in os.scandir(path):
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name.lower() in restricted: continue
                            total += fast_scan_sizes(entry.path)
                        else: total += entry.stat().st_size
                    except: pass
            except: pass
            folder_sizes[path] = total
            return total
        fast_scan_sizes(root_path)
        children_of = {}
        for c_path in folder_sizes.keys():
            parent = os.path.dirname(c_path); children_of.setdefault(parent, []).append(c_path)
        final_data = {}
        for path, size in folder_sizes.items():
            is_wrap = False
            if path in children_of:
                for c_path in children_of[path]:
                    if folder_sizes[c_path] >= (size * 0.90): is_wrap = True; break
            if not is_wrap: final_data[path] = size
        self.file_data2 = []
        for path, size in final_data.items():
            mb = size / (1024 * 1024)
            self.file_data2.append((os.path.basename(path), mb, self.detect_project(path), self.determine_category(path, os.path.basename(path)), path))
        self.file_data2.sort(key=lambda x: x[1], reverse=True); self.root.after(0, lambda: self.refresh_table2(True))

    def refresh_table2(self, complete=False):
        # FIXED: Dynamic Project Menu builds from actual findings, not hardcoded defaults
        found_projs = sorted(list(set(item[2] for item in self.file_data2)))
        if "GENERAL" in found_projs: found_projs.remove("GENERAL"); found_projs.append("GENERAL")
        
        current_p = self.proj_combo2.get()
        self.proj_combo2['values'] = ["All Projects"] + found_projs
        if current_p not in self.proj_combo2['values']: self.proj_combo2.current(0)
        
        p_filter, c_filter = self.proj_combo2.get(), self.cat_combo2.get()
        try: m_size = float(self.size_entry2.get())
        except: m_size = 0.0

        self.tree2.delete(*self.tree2.get_children())
        display_count = 0; max_display = 3000
        for item in self.file_data2:
            if display_count >= max_display: break
            if item[1] < m_size: continue # Live Size Filtering
            if p_filter != "All Projects" and item[2] != p_filter: continue
            if c_filter != "All Categories" and item[3] != c_filter: continue
            self.tree2.insert("", tk.END, values=(item[0], self.format_size(item[1]), item[2], item[3], item[4]), tags=(item[4], self.get_color_tag(item[3])))
            display_count += 1
        if complete: self.status2.config(text="Deep Storage Analysis Complete.", fg="#4caf50"); self.scan_btn2.config(state=tk.NORMAL)

    def sort_column2(self, col, reverse):
        col_idx = ("Folder Name", "Total Size", "Project", "Category", "Full Path").index(col)
        if col == "Total Size": self.file_data2.sort(key=lambda x: x[1], reverse=reverse)
        else: self.file_data2.sort(key=lambda x: str(x[col_idx]).lower(), reverse=reverse)
        self.refresh_table2(); self.tree2.heading(col, command=lambda: self.sort_column2(col, not reverse))

    def open_location2(self):
        sel = self.tree2.selection()
        if sel: subprocess.Popen(f'explorer "{os.path.normpath(self.tree2.item(sel[0], "tags")[0])}"')

    def delete_selected2(self):
        sel = self.tree2.selection()
        if not sel: return
        to_del = []
        for item in sel:
            cat = self.tree2.item(item, "values")[3]
            if "🔴" not in cat: to_del.append(self.tree2.item(item, "tags")[0])
        if not to_del: return
        if messagebox.askyesno("Turbo Delete", f"Wipe {len(to_del)} folders?"):
            self.status2.config(text="Forcefully clearing storage...", fg=ACCENT_RED)
            def run_del():
                for p in to_del:
                    try:
                        subprocess.run(f'cmd /c del /f /s /q /a "{os.path.normpath(p)}\\*"', shell=True)
                        subprocess.run(f'cmd /c rmdir /s /q "{os.path.normpath(p)}"', shell=True)
                        if not os.path.exists(p): self.file_data2 = [f for f in self.file_data2 if f[4] != p]
                    except: pass
                self.root.after(0, self.refresh_table2) # Drodown updates here as part of refresh
            threading.Thread(target=run_del, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk(); app = AIStorageManagerPro(root); root.mainloop()