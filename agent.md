# Agent Specification & Project Replication Guide: PCQA Automation System

This document serves as the complete technical blueprint and system specification for the **Point Cloud Quality Assessment (PCQA) Annotation Assistant**. It defines the project architecture, directory structure, workflow logic, data schema, user interface behavior, and operational constraints required to reconstruct or extend the application.

> **Note:** Source code is intentionally omitted from this specification. Any future implementation should strictly adhere to the architectural and structural constraints described in this document.

---

# 1. System Overview

The Point Cloud Quality Assessment (PCQA) Annotation Assistant is a desktop application designed to streamline the manual annotation workflow for perceptual quality assessment of distorted 3D point clouds.

Traditionally, the annotation process requires an evaluator to:

- Locate distorted point cloud files from predefined research blocks.
- Load both distorted and reference point clouds into an Open3D visualization environment.
- Manually determine the corresponding reference model.
- Record multiple subjective distortion ratings into an Excel spreadsheet.
- Keep track of previously completed annotations to avoid duplicate work.

This application automates those repetitive tasks by integrating:

- **Open3D** for side-by-side point cloud visualization
- **Tkinter** for the desktop annotation interface
- **Pandas** for CSV processing
- **OpenPyXL** for Excel logging

The system automatically:

- loads annotation queues,
- resolves reference models,
- saves structured annotations,
- resumes interrupted sessions,
- maintains progress across multiple datasets.

---

# 2. Project Directory Structure

The application relies on a fixed directory hierarchy. Relative paths should remain unchanged.

```text
main_folder/
│
├── PointClouds/
│   ├── SRC/
│   │   ├── p01.ply
│   │   ├── p02.ply
│   │   └── ...
│   │
│   └── PPC/
│       ├── p01_geocnn_r01.ply
│       ├── p01_noise_r02.ply
│       ├── p02_blur_r03.ply
│       └── ...
│
├── LS_PCQA_block_files/
│   ├── LS_PCQA_block_1.csv
│   ├── LS_PCQA_block_6.csv
│   ├── LS_PCQA_block_7.csv
│   ├── block 1_annotations.xlsx
│   ├── block 6_annotations.xlsx
│   └── block 7_annotations.xlsx
│
├── Basics_block_files/
│   ├── basics_block_1.csv
│   ├── basics_block_5.csv
│   ├── basics_block_6.csv
│   ├── basics_block_7.csv
│   ├── block 1_annotations.xlsx
│   ├── block 5_annotations.xlsx
│   ├── block 6_annotations.xlsx
│   └── block 7_annotations.xlsx
│
├── Calibration/
│   ├── Calibration_Set_Basics.csv
│   ├── Calibration_Set_LS_PCQA.csv
│   ├── Calibration_Set_Basics_annotations.xlsx
│   └── Calibration_Set_LS_PCQA_annotations.xlsx
│
└── pcqa_annotator.py
```

---

# 3. Annotation Scope

The application only operates on approved evaluation datasets.

## Supported Dataset Groups

| Dataset Folder | Supported Blocks | CSV Source |
|----------------|------------------|------------|
| `LS_PCQA_block_files` | Block 1, Block 6, Block 7 | `LS_PCQA_block_{#}.csv` |
| `Basics_block_files` | Block 1, Block 5, Block 6, Block 7 | `basics_block_{#}.csv` |
| `Calibration` | Calibration Set Basics, Calibration Set LS_PCQA | `{dataset_name}.csv` |

The application must **not** iterate over every file in the `PPC` directory. Instead, annotation targets are determined exclusively by the selected CSV file.

---

# 4. Workflow

## 4.1 CSV-Driven Target Queue

Each annotation session begins by selecting one dataset/block.

The corresponding CSV file contains the ordered list of distorted point clouds.

Example:

```text
LS_PCQA_block_1.csv
```

The application reads the **`Ply_name`** column and constructs an ordered annotation queue.

Example:

```text
p01_geocnn_r01.ply
p01_noise_r02.ply
p02_blur_r01.ply
...
```

Only these files are loaded during the annotation session.

---

## 4.2 Reference Point Cloud Resolution

Each distorted point cloud has a matching reference model stored in:

```text
PointClouds/SRC/
```

The mapping is determined by extracting the filename prefix before the first underscore.

Example:

```text
Distorted:
p01_geocnn_r01.ply

↓

Reference:
p01.ply
```

Algorithm:

```
filename.split("_")[0] + ".ply"
```

This reference model is automatically loaded alongside the distorted point cloud.

---

## 4.3 Incremental Session Resumption

To prevent annotation loss after application closure or interruption, the application resumes automatically.

Workflow:

1. Open the existing annotation workbook.
2. Read the completed `Ply_name` entries.
3. Compare them against the CSV annotation queue.
4. Locate the first unannotated point cloud.
5. Resume rendering from that position.

This enables crash-safe annotation without duplicate entries.

---

# 5. Excel Database Schema

Each annotation workbook stores one row per evaluated point cloud.

The column names must remain unchanged.

| Column | Type | Description |
|---------|------|-------------|
| Ply_name | String | Filename of distorted point cloud |
| Texture Condition | Categorical | Overall recognizability |
| Brightness distortion | Categorical | Brightness artifacts |
| Color Distortion | Categorical | Color artifacts |
| Noise | Categorical | Noise severity |
| Blurriness | Categorical | Blur severity |
| Point Density Distortion | Categorical | Density degradation |
| Scattering Artifact | Categorical | Scattering severity |
| Grid Artifact | Categorical | Grid pattern artifacts |
| Missing Region | Categorical | Missing geometry |
| Deformed Shape | Categorical | Structural deformation |
| Moire Pattern | Categorical | Moiré artifacts |
| Quality Description | Free Text | Subjective observations |

---

# 6. Allowed Annotation Values

## Texture Condition

Exactly one of:

- clearly identifiable
- strongly distorted but identifiable
- distorted but identifiable
- barely identifiable
- completely damaged

---

## Distortion Metrics

Each distortion metric shares the same categorical scale.

Allowed values:

- None
- Low
- Medium
- High
- Severe

These values apply to all ten distortion categories.

---

## Quality Description

A free-text field used to capture subjective observations regarding:

- visible artifacts
- structural defects
- rendering issues
- perceived quality
- unusual distortions

---

# 7. User Interface Architecture

The desktop application is implemented using **Tkinter**.

The interface consists of:

- current point cloud information
- annotation controls
- dropdown menus
- free-text description field
- navigation controls
- automatic save functionality

Layout should be constructed using the Tkinter `grid()` geometry manager.

Recommended layout practice:

```python
widget.grid(..., sticky="ew")
```

rather than using `fill="x"`.

---

# 8. Visualization Pipeline

The visualization subsystem uses **Open3D**.

Two visualization windows are displayed simultaneously:

- Reference point cloud
- Distorted point cloud

Both remain synchronized with the annotation interface.

The rendering loop must remain non-blocking.

Recommended execution pattern:

```python
while application_running:

    reference_window.poll_events()
    reference_window.update_renderer()

    distorted_window.poll_events()
    distorted_window.update_renderer()

    root.update()
```

This prevents the GUI from freezing while maintaining interactive rendering.

---

# 9. Key Functional Requirements

The application shall:

- load annotation targets from CSV files
- never scan the PPC directory directly for annotation order
- automatically resolve source point clouds
- display reference and distorted models simultaneously
- record structured annotations into Excel
- automatically create annotation workbooks if absent
- resume unfinished annotation sessions
- preserve annotation order defined by the CSV
- maintain a responsive GUI during rendering
- support all approved dataset groups

---

# 10. Technologies

| Component | Library |
|-----------|---------|
| GUI | Tkinter |
| Point Cloud Visualization | Open3D |
| CSV Processing | Pandas |
| Excel Writing | OpenPyXL |
| Language | Python 3 |

---

# 11. Summary

The PCQA Annotation Assistant provides a structured, reproducible workflow for subjective point cloud quality assessment. By integrating visualization, annotation, automatic data management, and session recovery into a single desktop application, it significantly reduces manual effort while ensuring consistency across multiple evaluation datasets and research blocks.