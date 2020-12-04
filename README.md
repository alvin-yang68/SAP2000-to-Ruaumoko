# Convert from SAP2000 to Ruaumoko

SAP2000 is general-purpose civil-engineering software ideal for the analysis and design of any type of structural system. Basic and advanced systems, ranging from 2D to 3D, of simple geometry to complex, may be modeled, analyzed, designed, and optimized using a practical and intuitive object-based modeling environment that simplifies and streamlines the engineering process. 

The program RUAUMOKO is designed to produce a piece-wise time-history response of non-linear general two-dimensional and three-dimensional structures to ground accelerations, ground displacements or time varying force excitations. The program may also be used for static or pushover analyses of structures.

## Python script for conversion

A Python script to convert .S2K file to Ruaumoko text input file was developed.

The main obstacle with using RUAUMOKO is that it lacks a 3D interactive interface, since it is mainly a text-based software. The aim of developing this Python script is to allow structural engineers to develop a structural model in SAP2000 which can then be exported to RUAUMOKO for performing Non-Linear Time History Analysis (NLTHA). Unlike SAP2000 which is FEM-based, RUAUMOKO is CP-based, which has the advantage of having a lower computational load while carrying out analyses.

The Python script is currently capable of supporting "Frame", "Bracing", and "Spring" elements in SAP2000, since they have direct equivalents in RUAUMOKO. All other elements in SAP2000 that are not supported will still be converted into members in RUAUMOKO, although the modeler must manually specify the properties. Keep in mind that the main purpose of this script is to transfer the geometrical properties of nodes and elements to compensate for the lack of 3D interface of RUAUMOKO rather than to have a complete conversion process.

## Steps to use

1) Develop initial model in SAP2000 and export it in a .S2K file format
2) Run *converter.py* and select the exported .S2K file via a pop-up dialog
3) The converter will run and save the result in *output.txt*
