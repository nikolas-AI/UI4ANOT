# PCQA Annotation Assistant

A desktop application for **Point Cloud Quality Assessment (PCQA)** annotation that streamlines the subjective evaluation of distorted 3D point clouds. The tool integrates **Open3D** visualization with a **Tkinter**-based annotation interface, enabling researchers to efficiently compare distorted point clouds against their reference models and record structured quality assessments.

---

## Features

- Interactive side-by-side visualization of reference and distorted point clouds using **Open3D**
- Desktop annotation interface built with **Tkinter**
- CSV-driven annotation workflow
- Automatic reference point cloud resolution
- Automatic Excel workbook creation and updates
- Crash-safe session resumption
- Support for multiple dataset groups (Basics, LS_PCQA, Calibration)
- Structured annotation schema for perceptual quality assessment

---

## Project Structure

```text
main_folder/
│
├── PointClouds/
│   ├── SRC/
│   ├── PPC/
│   ├── LS_PCQA/
│   └── LS_PCQA_PPC/
│
├── Basics_block_files/
├── LS_PCQA_block_files/
├── Calibration/
│
├── pcqa_annotator.py
├── README.md
└── Agent_Specification.md
```

---

## Supported Datasets

The application supports three dataset categories:

| Dataset | Supported Blocks |
|----------|------------------|
| Basics | Block 1, 5, 6, 7 |
| LS_PCQA | Block 1, 6, 7 |
| Calibration | Basics & LS_PCQA |

Each annotation session is driven by the corresponding CSV file rather than scanning directories.

---

## Annotation Workflow

1. Select a dataset and block.
2. The application loads the associated CSV file.
3. Point cloud filenames are read from the **`Ply_name`** column.
4. The corresponding reference model is automatically located.
5. Reference and distorted point clouds are displayed simultaneously.
6. Complete the quality assessment using the annotation form.
7. Results are automatically written to an Excel workbook.
8. If the application is closed, progress is restored automatically the next time the dataset is opened.

---

## Annotation Categories

### Texture Condition

- Clearly identifiable
- Strongly distorted but identifiable
- Distorted but identifiable
- Barely identifiable
- Completely damaged

### Distortion Metrics

Each metric is rated using:

- None
- Low
- Medium
- High
- Severe

Metrics include:

- Brightness Distortion
- Color Distortion
- Noise
- Blurriness
- Point Density Distortion
- Scattering Artifact
- Grid Artifact
- Missing Region
- Deformed Shape
- Moiré Pattern

An additional free-text **Quality Description** field is available for subjective observations.

---

## Technologies

- Python 3
- Open3D
- Tkinter
- Pandas
- OpenPyXL

---

## Installation

Clone the repository:

```bash
git clone https://github.com/nikolas-AI/UI4ANOT.git
cd UI4ANOT
```

Install the required dependencies:

```bash
pip install open3d pandas openpyxl
```

---

## Running the Application

Run the annotation interface:

```bash
python pcqa_annotator.py
```

---

## Documentation

A complete description of the system architecture, workflow, data schema, and implementation details is available in:

- **agent.md**

This document serves as the primary technical reference for understanding, reproducing, or extending the application.

---

## Future Improvements

- Keyboard shortcuts for faster annotation
- Automatic backup of annotation workbooks
- Configurable annotation templates
- Additional visualization controls
- Support for new PCQA datasets

---

## Acknowledgments

This project was developed to support research in **Point Cloud Quality Assessment (PCQA)** by reducing the manual effort required for subjective annotation while ensuring a consistent and reproducible evaluation workflow.