import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import open3d as o3d

# ==========================================
# CONFIGURATION & DIRECTORY CONSTANTS
# ==========================================
# Adjust this path to match where your main folder is located
MAIN_DIR = "./" 

# Folder subsets you are allowed to annotate
ALLOWED_BLOCKS = {
    "LS_PCQA_block_files": ["block 1", "block 6", "block 7"],
    "Basics_block_files": ["block 1", "block 5", "block 6", "block 7"],
    "Calibration": ["Calibration Set"]
}

RATING_OPTIONS = ["None", "Low", "Medium", "High", "Severe"]
TEXTURE_OPTIONS = [
    "clearly identifiable", 
    "strongly distorted but identifiable", 
    "distorted but identifiable", 
    "barely identifiable", 
    "completely damaged"
]

COLUMNS = [
    "Ply_name", "Texture Condition", "Brightness distortion", "Color Distortion", 
    "Noise", "Blurriness", "Point Density Distortion", "Scattering Artifact", 
    "Grid Artifact", "Missing Region", "Deformed Shape", "Moire Pattern", "Quality Description"
]

class PCQAAnnotatorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCQA Annotation Assistant")
        self.root.geometry("500x750")
        
        self.ppc_files = []
        self.current_index = 0
        self.excel_save_path = ""
        self.current_vis_data = None
        
        self.setup_ui()

    def setup_ui(self):
        # --- Block Selection Frame ---
        frame_select = ttk.LabelFrame(self.root, text=" 1. Select Block / Dataset ", padding=10)
        frame_select.pack(fill="x", padx=15, pady=10)
        
        ttk.Label(frame_select, text="Dataset Group:").grid(row=0, column=0, sticky="w", pady=2)
        self.combo_group = ttk.Combobox(frame_select, values=list(ALLOWED_BLOCKS.keys()), state="readonly")
        self.combo_group.grid(row=0, column=1, fill="x", pady=2)
        self.combo_group.bind("<<ComboboxSelected>>", self.update_block_options)
        
        ttk.Label(frame_select, text="Specific Block:").grid(row=1, column=0, sticky="w", pady=2)
        self.combo_block = ttk.Combobox(frame_select, state="readonly")
        self.combo_block.grid(row=1, column=1, fill="x", pady=2)
        
        btn_load = ttk.Button(frame_select, text="Load Point Clouds", command=self.load_dataset)
        btn_load.grid(row=2, column=0, columnspan=2, pady=10)

        # --- Progress & File Info Frame ---
        self.frame_info = ttk.LabelFrame(self.root, text=" 2. Current Evaluation ", padding=10)
        self.frame_info.pack(fill="x", padx=15, pady=5)
        
        self.lbl_progress = ttk.Label(self.frame_info, text="Progress: 0 / 0", font=("Arial", 10, "bold"))
        self.lbl_progress.pack(anchor="w")
        
        self.lbl_file = ttk.Label(self.frame_info, text="File: None Loaded", wraplength=450, foreground="blue")
        self.lbl_file.pack(anchor="w", pady=5)
        
        self.btn_view = ttk.Button(self.frame_info, text="▶ View / Refresh 3D Models", command=self.visualize_current, state="disabled")
        self.btn_view.pack(fill="x", pady=5)

        # --- Annotation Form Frame ---
        self.frame_form = ttk.LabelFrame(self.root, text=" 3. Distortions & Attributes ", padding=10)
        self.frame_form.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Scrollable area inside form for safety across screens
        canvas = tk.Canvas(self.frame_form, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame_form, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.dropdowns = {}
        
        # Create Form Fields dynamically
        for col in COLUMNS[1:-1]: # Exclude Ply_name and Description
            f = ttk.Frame(self.scroll_frame)
            f.pack(fill="x", pady=4)
            lbl = ttk.Label(f, text=f"{col}:", width=22, anchor="w")
            lbl.pack(side="left")
            
            opts = TEXTURE_OPTIONS if col == "Texture Condition" else RATING_OPTIONS
            cb = ttk.Combobox(f, values=opts, state="readonly", width=25)
            cb.set(opts[0]) # Default to first option (e.g. None / clearly identifiable)
            cb.pack(side="right", fill="x", expand=True)
            self.dropdowns[col] = cb
            
        # Quality Description Text box
        f_desc = ttk.Frame(self.scroll_frame)
        f_desc.pack(fill="x", pady=6)
        ttk.Label(f_desc, text="Quality Description:").pack(anchor="w")
        self.txt_desc = tk.Text(f_desc, height=3, width=45)
        self.txt_desc.pack(fill="x", pady=2)

        # --- Submission Navigation ---
        frame_nav = ttk.Frame(self.root, padding=10)
        frame_nav.pack(fill="x", padx=15, pady=5)
        
        self.btn_submit = ttk.Button(frame_nav, text="Save & Next File", command=self.save_and_next, state="disabled")
        self.btn_submit.pack(fill="x", ipady=5)

    def update_block_options(self, event=None):
        group = self.combo_group.get()
        self.combo_block.config(values=ALLOWED_BLOCKS[group])
        self.combo_block.set(ALLOWED_BLOCKS[group][0])

    def load_dataset(self):
        group = self.combo_group.get()
        block = self.combo_block.get()
        
        if not group or not block:
            messagebox.showwarning("Selection Missing", "Please select both a group and a block.")
            return
            
        # Target Excel path for saving findings
        self.excel_save_path = os.path.join(MAIN_DIR, group, f"{block}_annotations.xlsx")
        
        # Gather Distorted Point Clouds (PPC)
        ppc_dir = os.path.join(MAIN_DIR, "PointClouds", "PPC")
        self.ppc_files = sorted(glob.glob(os.path.join(ppc_dir, "*.ply")))
        
        if not self.ppc_files:
            messagebox.showerror("Error", f"No .ply files found inside folder: {ppc_dir}")
            return
            
        self.current_index = 0
        
        # Read existing annotations to pick up where we left off if needed
        if os.path.exists(self.excel_save_path):
            try:
                df_existing = pd.read_excel(self.excel_save_path)
                annotated_names = df_existing["Ply_name"].astype(str).tolist()
                # Advance pointer past already rated systems
                while self.current_index < len(self.ppc_files):
                    basename = os.path.basename(self.ppc_files[self.current_index])
                    if basename in annotated_names:
                        self.current_index += 1
                    else:
                        break
            except Exception as e:
                pass
                
        self.btn_view.config(state="normal")
        self.btn_submit.config(state="normal")
        self.update_file_display()

    def update_file_display(self):
        if self.current_index >= len(self.ppc_files):
            self.lbl_progress.config(text=f"Progress: {len(self.ppc_files)} / {len(self.ppc_files)}")
            self.lbl_file.config(text="🎉 All point clouds in this path have been annotated!")
            self.btn_view.config(state="disabled")
            self.btn_submit.config(state="disabled")
            return
            
        self.lbl_progress.config(text=f"Progress: {self.current_index + 1} / {len(self.ppc_files)}")
        current_file = os.path.basename(self.ppc_files[self.current_index])
        self.lbl_file.config(text=f"File: {current_file}")
        
        # Clear/Reset inputs to defaults
        for cb in self.dropdowns.values():
            cb.set(cb['values'][0])
        self.txt_desc.delete("1.0", tk.END)

    def find_reference_file(self, distorted_filename):
        """
        Tries to match the distorted file back to its source reference file.
        Modify this method if your filenames don't share identical substrings.
        """
        src_dir = os.path.join(MAIN_DIR, "PointClouds", "SRC")
        src_files = glob.glob(os.path.join(src_dir, "*.ply"))
        
        # Simple heuristic: Does the source filename show up within the distorted string?
        for src_path in src_files:
            src_base = os.path.splitext(os.path.basename(src_path))[0]
            if src_base in distorted_filename:
                return src_path
                
        # Fallback: Default to first file if naming matching strategy yields nothing
        return src_files[0] if src_files else None

    def visualize_current(self):
        if self.current_index >= len(self.ppc_files):
            return
            
        dist_path = self.ppc_files[self.current_index]
        ref_path = self.find_reference_file(os.path.basename(dist_path))
        
        if not ref_path or not os.path.exists(ref_path):
            messagebox.showerror("Error", "Could not locate matching reference source cloud in SRC folder.")
            return

        pcd_ref = o3d.io.read_point_cloud(ref_path)
        pcd_dist = o3d.io.read_point_cloud(dist_path)

        vis1 = o3d.visualization.Visualizer()
        vis1.create_window(window_name="Reference Source", width=700, height=550, left=50, top=50)
        vis1.add_geometry(pcd_ref)

        vis2 = o3d.visualization.Visualizer()
        vis2.create_window(window_name=f"Distorted: {os.path.basename(dist_path)}", width=700, height=550, left=780, top=50)
        vis2.add_geometry(pcd_dist)

        vis1.get_render_option().point_size = 2.0
        vis2.get_render_option().point_size = 2.0

        # Non-blocking render loops
        while True:
            vis1.update_geometry(pcd_ref)
            vis2.update_geometry(pcd_dist)
            
            if not vis1.poll_events() or not vis2.poll_events():
                break
                
            vis1.update_renderer()
            vis2.update_renderer()
            self.root.update() # Keeps master UI responsive

        vis1.destroy_window()
        vis2.destroy_window()

    def save_and_next(self):
        current_file = os.path.basename(self.ppc_files[self.current_index])
        
        # Package metrics row
        row_data = {"Ply_name": current_file}
        for col, cb in self.dropdowns.items():
            row_data[col] = cb.get()
        row_data["Quality Description"] = self.txt_desc.get("1.0", "end-1c").strip()
        
        new_row_df = pd.DataFrame([row_data], columns=COLUMNS)
        
        # Save or append record to block file sheet
        try:
            if os.path.exists(self.excel_save_path):
                df_existing = pd.read_excel(self.excel_save_path)
                # Eliminate existing duplicates if writing over a past submission line
                df_existing = df_existing[df_existing["Ply_name"] != current_file]
                df_final = pd.concat([df_existing, new_row_df], ignore_index=True)
            else:
                os.makedirs(os.path.dirname(self.excel_save_path), exist_ok=True)
                df_final = new_row_df
                
            df_final.to_excel(self.excel_save_path, index=False)
            
            # Step loop tracking forward
            self.current_index += 1
            self.update_file_display()
        except Exception as e:
            messagebox.showerror("File Error", f"Could not save metrics entry to Excel:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PCQAAnnotatorUI(root)
    root.mainloop()