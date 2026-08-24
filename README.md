# The-Ashcombe-Murder-Game
A 3D locked-room murder mystery game built with Python and PyOpenGL (GLUT). Features dual camera modes, interactive clues, and dynamic HUD.
# The Ashcombe Murder: A 3D Locked-Room Mystery

**The Ashcombe Murder** is a 3D interactive mystery game built in Python using PyOpenGL and GLUT. Set in November 1923, players take on the role of Detective Eleanor Cray to explore a storm-isolated mansion, inspect interactive 3D clues, interview suspects, and solve the locked-room murder of Cornelius Vane.

---

## Technical Overview

* **Engine / Framework:** PyOpenGL (`OpenGL.GL`, `OpenGL.GLUT`, `OpenGL.GLU`)
* **Graphics Architecture:** Fixed-function pipeline utilizing 3D primitives, dynamic projection switching (2D HUD overlays & 3D perspective world rendering), custom matrix transformations, and view vector aiming math.
* **Language:** Python 3.x

---

## Game Mechanics & Features

### Dual Camera Modes
* **Third-Person Orbit View:** Free-orbit camera around the room with zoom control.
* **First-Person View:** True eye-level perspective (`FIRST_PERSON_EYE_HEIGHT`) featuring 3D vector-based line-of-sight cone checking for direct clue inspection.

### Investigation & Detective System
* **Detective Mode (`V` key):** Triggers dynamic visual pulse cues above interactable clues in range.
* **3D Clue Inspection & Dialogue System:** Near-field interaction detection for inspecting evidence and questioning household members.
* **Notebook & Floor Map:** Tracks collected clues and real-time locations of suspects across all 5 interconnected room shells.
* **Accusation Gate:** Deductive victory condition requiring all 11 clues to be uncovered before making a final verdict.

---

## Room Layout

The game features 5 fully modeled rooms with spatial collision boundaries and custom furniture:

1. **Room 1: The Study** – The crime scene containing the victim, desk evidence, and wax residue.
2. **Room 2: The Hallway** – Central hub connecting all rooms, containing the shared temperature control panel.
3. **Room 3: The Parlor** – Featuring parquet floors, a piano, and sitting areas.
4. **Room 4: The Dining Room** – Tiled dining area with place settings and sideboards.
5. **Room 5: Toby's Bedroom** – Paler wood environment containing toy shelves and the empty terrarium stand.

---

## Control Scheme

| Action | Third-Person Mode | First-Person Mode |
| :--- | :--- | :--- |
| **Move Detective** | `W` / `A` / `S` / `D` | `W` / `S` (Step), `A` / `D` (Turn) |
| **Camera Orbit / Pitch** | Arrow Keys (`Left`/`Right`/`Up`/`Down`) | `Up` / `Down` (Look Pitch), `Left` / `Right` (Turn) |
| **Zoom In / Out** | `Page Up` / `Page Down` | N/A |
| **Toggle View Mode** | Right Mouse Click | Right Mouse Click |
| **Interact / Examine / Talk** | `F` Key | `F` Key (Requires direct 3D aim cone match) |
| **Detective Mode Glow** | `V` Key | `V` Key |
| **Fast Travel Rooms** | Keys `1` through `5` | Keys `1` through `5` |
| **Debug: Unlock Notebook** | `N` Key | `N` Key |
| **Close Overlay / Menu** | `Esc` Key | `Esc` Key |

---

## Setup & Installation

### Prerequisites

Ensure Python 3.8+ is installed on your system along with PyOpenGL and GLUT.

```bash
pip install PyOpenGL PyOpenGL_accelerate
