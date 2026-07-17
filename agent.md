# Agent Specification & Project Replication Guide: PCQA Automation System

This document serves as the complete technical blueprint and system specification for the **Point Cloud Quality Assessment (PCQA) Annotation Assistant**. It contains all project directory structures, architectural designs, workflow logic, metadata requirements, and source code necessary for an LLM or developer to replicate the setup perfectly.

---

## 1. System Overview & Problem Statement
The manual PCQA annotation workflow requires a human assessor to evaluate 3D point cloud distortions against a reference model across hundreds of files. Doing this manually involves:
1. Hardcoding new file paths inside a visualization script repeatedly.
2. Cross-referencing complex folder structures managed by multiple research blocks.
3. Keeping a separate Excel workbook open to manually write individual categorical ratings for 12 distinct metric fields per file.

This system wraps the open3d visualization context inside a desktop graphical interface built with Python (`tkinter` + `pandas` + `openpyxl`), creating a non-blocking execution loop that automates file loading, path resolving, structural data logging, and persistent progress tracking.

---

## 2. Project Directory Structure
The application relies on strict relative path boundaries inside a uniform root folder. The structure below must be replicated identically for the initialization rules to work:

```text
├── main_folder/
│   ├── PointClouds/
│   │   ├── SRC/                                 # Source Reference Point Clouds
│   │   │   ├── model_01.ply
│   │   │   └── model_02.ply
│   │   └── PPC/                                 # Processed/Distorted Point Clouds
│   │       ├── model_01_noise_low.ply
│   │       ├── model_01_blur_high.ply
│   │       └── model_02_scattering_severe.ply
│   ├── LS_PCQA_block_files/                     # Target folder for LS blocks
│   │   ├── block 1_annotations.xlsx             # Auto-generated via UI
│   │   ├── block 6_annotations.xlsx             # Auto-generated via UI
│   │   └── block 7_annotations.xlsx             # Auto-generated via UI
│   ├── Basics_block_files/                      # Target folder for Basics blocks
│   │   ├── block 1_annotations.xlsx             # Auto-generated via UI
│   │   ├── block 5_annotations.xlsx             # Auto-generated via UI
│   │   ├── block 6_annotations.xlsx             # Auto-generated via UI
│   │   └── block 7_annotations.xlsx             # Auto-generated via UI
│   ├── Calibration/                             # Target folder for Calibration Set
│   │   └── Calibration Set_annotations.xlsx     # Auto-generated via UI
│   └── pcqa_annotator.py                        # Main UI Application Script
```

---

## 3. Scope of Annotation & Workflow Constraints
The assistant restricts file operations exclusively to the authorized evaluation phases allocated below:

| Dataset Group Group / Folder Name | Allowed Blocks / Files Subsets |
| :--- | :--- |
| `LS_PCQA_block_files` | `block 1`, `block 6`, `block 7` |
| `Basics_block_files` | `block 1`, `block 5`, `block 6`, `block 7` |
| `Calibration` | `Calibration Set` |

### Data Mapping Mechanism
- **Reference Resolution:** Distorted files located inside `PointClouds/PPC/` are matched against original geometries in `PointClouds/SRC/` by identifying whether the source filename is an exact substring within the distorted file string.
- **Incremental Resumption (Crash-Safety):** Upon loading a designated block dataset, the system queries the corresponding target `.xlsx` file. It reads `Ply_name` columns already populated, cross-checks them against the list of target `.ply` files inside the `PPC/` folder, and sets the entry pointer directly to the first unrated file.

---

## 4. Database & Excel Schema Specification
Every entry written by the tool must adhere to this structured layout with no modified naming keys. 

### Data Columns & Allowed Ranges
1. **Ply_name** *(String)*: The baseline filename of the evaluated distorted point cloud (e.g., `model_01_noise_low.ply`).
2. **Texture Condition** *(Dropdown Categorical)*: 
   - `clearly identifiable`
   - `strongly distorted but identifiable`
   - `distorted but identifiable`
   - `barely identifiable`
   - `completely damaged`
3. **Distortion Metrics** *(Dropdown Categorical for items 3 through 12)*:
   - *Allowed Choices:* `None`, `Low`, `Medium`, `High`, `Severe`
   - *Target Fields:*
     - `Brightness distortion`
     - `Color Distortion`
     - `Noise`
     - `Blurriness`
     - `Point Density Distortion`
     - `Scattering Artifact`
     - `Grid Artifact`
     - `Missing Region`
     - `Deformed Shape`
     - `Moire Pattern`
4. **Quality Description** *(String / Free Text)*: Structural text field capturing subjective physical artifact observations.

---

## 5. Complete Production Source Code

```python
import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import open3d as o3d

# ==========================================
# CONFIGURATION & DIRECTORY CONSTANTS
# ==========================================
MAIN_DIR = "./" 

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
        self.root.geometry("520x780")
        
        self.ppc_files = []
        self.current_index = 0
        self.excel_save_path = ""
        
        self.setup_ui()

    def setup_ui(self):
        # --- Block Selection Frame ---
        frame_select = ttk.LabelFrame(self.root, text=" 1. Dataset Scope Configuration ", padding=10)
        frame_select.pack(fill="x", padx=15, pady=10)
        
        ttk.Label(frame_select, text="Dataset Group:").grid(row=0, column=0, sticky="w", pady=4)
        self.combo_group = ttk.Combobox(frame_select, values=list(ALLOWED_BLOCKS.keys()), state="readonly")
        self.combo_group.grid(row=0, column=1, fill="x", pady=4, padx=5)
        self.combo_group.bind("<<ComboboxSelected>>", self.update_block_options)
        
        ttk.Label(frame_select, text="Target Block:").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_block = ttk.Combobox(frame_select, state="readonly")
        self.combo_block.grid(row=1, column=1, fill="x", pady=4, padx=5)
        
        btn_load = ttk.Button(frame_select, text="Load Point Cloud Dataset Target", command=self.load_dataset)
        btn_load.grid(row=2, column=0, columnspan=2, pady=10)

        # --- Progress & File Info Frame ---
        self.frame_info = ttk.LabelFrame(self.root, text=" 2. Performance Tracking & Active Render ", padding=10)
        self.frame_info.pack(fill="x", padx=15, pady=5)
        
        self.lbl_progress = ttk.Label(self.frame_info, text="Progress: 0 / 0", font=("Arial", 10, "bold"))
        self.lbl_progress.pack(anchor="w")
        
        self.lbl_file = ttk.Label(self.frame_info, text="File: No target file queued", wraplength=460, foreground="#1a73e8")
        self.lbl_file.pack(anchor="w", pady=5)
        
        self.btn_view = ttk.Button(self.frame_info, text="▶ Render Side-by-Side 3D Views", command=self.visualize_current, state="disabled")
        self.btn_view.pack(fill="x", pady=5)

        # --- Annotation Form Frame ---
        self.frame_form = ttk.LabelFrame(self.root, text=" 3. Dimension Matrices Entry Form ", padding=10)
        self.frame_form.pack(fill="both", expand=True, padx=15, pady=10)
        
        canvas = tk.Canvas(self.frame_form, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame_form, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.dropdowns = {}
        
        for col in COLUMNS[1:-1]:
            f = ttk.Frame(self.scroll_frame)
            f.pack(fill="x", pady=4)
            lbl = ttk.Label(f, text=f"{col}:", width=24, anchor="w")
            lbl.pack(side="left")
            
            opts = TEXTURE_OPTIONS if col == "Texture Condition" else RATING_OPTIONS
            cb = ttk.Combobox(f, values=opts, state="readonly", width=25)
            cb.set(opts[0])
            cb.pack(side="right", fill="x", expand=True)
            self.dropdowns[col] = cb
            
        f_desc = ttk.Frame(self.scroll_frame)
        f_desc.pack(fill="x", pady=6)
        ttk.Label(f_desc, text="Quality Description Notes:").pack(anchor="w")
        self.txt_desc = tk.Text(f_desc, height=3, width=45)
        self.txt_desc.pack(fill="x", pady=2)

        # --- Submission Action ---
        frame_nav = ttk.Frame(self.root, padding=10)
        frame_nav.pack(fill="x", padx=15, pady=5)
        
        self.btn_submit = ttk.Button(frame_nav, text="Commit Values & Stream Next File", command=self.save_and_next, state="disabled")
        self.btn_submit.pack(fill="x", ipady=6)

    def update_block_options(self, event=None):
        group = self.combo_group.get()
        self.combo_block.config(values=ALLOWED_BLOCKS[group])
        self.combo_block.set(ALLOWED_BLOCKS[group][0])

    def load_dataset(self):
        group = self.combo_group.get()
        block = self.combo_block.get()
        
        if not group or not block:
            messagebox.showwarning("Selection Ambiguity", "Please map out selection groups fully.")
            return
            
        self.excel_save_path = os.path.join(MAIN_DIR, group, f"{block}_annotations.xlsx")
        ppc_dir = os.path.join(MAIN_DIR, "PointClouds", "PPC")
        self.ppc_files = sorted(glob.glob(os.path.join(ppc_dir, "*.ply")))
        
        if not self.ppc_files:
            messagebox.showerror("IO Pipeline Error", f"Failed to catch target files under path: {ppc_dir}")
            return
            
        self.current_index = 0
        
        if os.path.exists(self.excel_save_path):
            try:
                df_existing = pd.read_excel(self.excel_save_path)
                annotated_names = df_existing["Ply_name"].astype(str).tolist()
                while self.current_index < len(self.ppc_files):
                    basename = os.path.basename(self.ppc_files[self.current_index])
                    if basename in annotated_names:
                        self.current_index += 1
                    else:
                        break
            except Exception:
                pass
                
        self.btn_view.config(state="normal")
        self.btn_submit.config(state="normal")
        self.update_file_display()

    def update_file_display(self):
        if self.current_index >= len(self.ppc_files):
            self.lbl_progress.config(text=f"Progress: {len(self.ppc_files)} / {len(self.ppc_files)}")
            self.lbl_file.config(text="🎉 Block Completed! All entities indexed successfully.")
            self.btn_view.config(state="disabled")
            self.btn_submit.config(state="disabled")
            return
            
        self.lbl_progress.config(text=f"Progress: {self.current_index + 1} / {len(self.ppc_files)}")
        current_file = os.path.basename(self.ppc_files[self.current_index])
        self.lbl_file.config(text=f"File: {current_file}")
        
        for cb in self.dropdowns.values():
            cb.set(cb['values'][0])
        self.txt_desc.delete("1.0", tk.END)

    def find_reference_file(self, distorted_filename):
        src_dir = os.path.join(MAIN_DIR, "PointClouds", "SRC")
        src_files = glob.glob(os.path.join(src_dir, "*.ply"))
        for src_path in src_files:
            src_base = os.path.splitext(os.path.basename(src_path))[0]
            if src_base in distorted_filename:
                return src_path
        return src_files[0] if src_files else None

    def visualize_current(self):
        if self.current_index >= len(self.ppc_files):
            return
            
        dist_path = self.ppc_files[self.current_index]
        ref_path = self.find_reference_file(os.path.basename(dist_path))
        
        if not ref_path or not os.path.exists(ref_path):
            messagebox.showerror("Reference Error", "Unable to pull matching model sequence out of SRC folder.")
            return

        pcd_ref = o3d.io.read_point_cloud(ref_path)
        pcd_dist = o3d.io.read_point_cloud(dist_path)

        vis1 = o3d.visualization.Visualizer()
        vis1.create_window(window_name="Reference Source Base", width=750, height=550, left=40, top=40)
        vis1.add_geometry(pcd_ref)

        vis2 = o3d.visualization.Visualizer()
        vis2.create_window(window_name=f"Distorted Vector: {os.path.basename(dist_path)}", width=750, height=550, left=810, top=40)
        vis2.add_geometry(pcd_dist)

        vis1.get_render_option().point_size = 2.0
        vis2.get_render_option().point_size = 2.0

        while True:
            vis1.update_geometry(pcd_ref)
            vis2.update_geometry(pcd_dist)
            
            if not vis1.poll_events() or not vis2.poll_events():
                break
                
            vis1.update_renderer()
            vis2.update_renderer()
            self.root.update()

        vis1.destroy_window()
        vis2.destroy_window()

    def save_and_next(self):
        current_file = os.path.basename(self.ppc_files[self.current_index])
        row_data = {"Ply_name": current_file}
        for col, cb in self.dropdowns.items():
            row_data[col] = cb.get()
        row_data["Quality Description"] = self.txt_desc.get("1.0", "end-1c").strip()
        
        new_row_df = pd.DataFrame([row_data], columns=COLUMNS)
        
        try:
            if os.path.exists(self.excel_save_path):
                df_existing = pd.read_excel(self.excel_save_path)
                df_existing = df_existing[df_existing["Ply_name"] != current_file]
                df_final = pd.concat([df_existing, new_row_df], ignore_index=True)
            else:
                os.makedirs(os.path.dirname(self.excel_save_path), exist_ok=True)
                df_final = new_row_df
                
            df_final.to_excel(self.excel_save_path, index=False)
            self.current_index += 1
            self.update_file_display()
        except Exception as e:
            messagebox.showerror("Database Lock Exception", f"Error outputting variables: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PCQAAnnotatorUI(root)
    root.mainloop()
```

---

## 6. Execution Instructions for Replicated Runs

### Dependencies Installation
Run the following script to provision local virtual contexts:
```bash
pip install open3d pandas openpyxl
```

### Prompt-to-Reconstruct Instruction for Future Sessions
If you feed this asset context into a new model, invoke it with the following directive:
> *"Read this `agent.md` file comprehensively to understand our directory bounds, dataset rules, and target Excel schema matrices. Use the existing tkinter structural blueprint to iterate or introduce structural functionality without shifting file paths or altering evaluation rules."*