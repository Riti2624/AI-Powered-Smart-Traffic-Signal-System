@echo off
REM Run from simulation\sumo folder after installing SUMO
netconvert --node-files corridor.nod.xml --edge-files corridor.edg.xml --output-file corridor.net.xml
