
# Welding Simulation and Aruco Marker Tracking

This repository contains code for simulating welding physics and tracking Aruco markers for 3D object estimation. The code is organized into modules for vision-based tracking, graphics pipeline integration, and physics simulation.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)

## Introduction

The project aims to provide a comprehensive solution for welding simulation and object tracking using Aruco markers. It combines computer vision techniques, graphics rendering, and physics simulation to simulate welding processes accurately and estimate 3D object positions in real-time.

## Features

- **Vision-based Object Tracking**: Utilize Aruco markers and stereo vision system to estimate 3D vertices of objects.
- **Graphics Pipeline Integration**: Map estimated points to a known model and compute object transformation matrix.
- **Real-time Rendering**: Project known models onto the screen and estimate object aspect ratio.
- **Physics Simulation**: Implement 3D collision detection algorithms and simulate welding physics, including heat transfer and material deformation.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/username/repo.git
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Configure camera calibration and Aruco marker settings.
2. Run the AR_Render.py for vision-based object tracking and graphics rendering.
3. Adjust parameters for physics simulation and welding process optimization.

