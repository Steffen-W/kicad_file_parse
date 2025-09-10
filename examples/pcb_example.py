#!/usr/bin/env python3
"""
PCB (Board) Example - Demonstrate KiCad PCB file handling

This example shows how to:
1. Create a basic PCB from scratch
2. Add layers, nets, tracks, and vias
3. Save and load PCB files
4. Manipulate PCB elements programmatically

Run with: python examples/pcb_example.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kicad_parser import (
    UUID,
    BoardLayer,
    BoardNet,
    BoardSetup,
    GeneralSettings,
    KiCadPCB,
    LayerType,
    TrackSegment,
    TrackVia,
    ViaType,
    create_basic_pcb,
    load_pcb,
    save_pcb,
)


def create_example_pcb():
    """Create a simple PCB with basic elements"""
    print("Creating example PCB...")
    
    # Create a basic PCB
    pcb = create_basic_pcb()
    
    # Set up general settings
    pcb.general = GeneralSettings(thickness=1.6)
    
    # Define standard 4-layer stackup
    layers = [
        BoardLayer(ordinal=0, canonical_name="F.Cu", layer_type=LayerType.SIGNAL, user_name="Front Copper"),
        BoardLayer(ordinal=31, canonical_name="B.Cu", layer_type=LayerType.SIGNAL, user_name="Back Copper"),
        BoardLayer(ordinal=32, canonical_name="B.Adhes", layer_type=LayerType.USER, user_name="B.Adhesive"),
        BoardLayer(ordinal=33, canonical_name="F.Adhes", layer_type=LayerType.USER, user_name="F.Adhesive"),
        BoardLayer(ordinal=34, canonical_name="B.Paste", layer_type=LayerType.USER, user_name="B.Paste"),
        BoardLayer(ordinal=35, canonical_name="F.Paste", layer_type=LayerType.USER, user_name="F.Paste"),
        BoardLayer(ordinal=36, canonical_name="B.SilkS", layer_type=LayerType.USER, user_name="B.Silkscreen"),
        BoardLayer(ordinal=37, canonical_name="F.SilkS", layer_type=LayerType.USER, user_name="F.Silkscreen"),
        BoardLayer(ordinal=38, canonical_name="B.Mask", layer_type=LayerType.USER, user_name="B.Mask"),
        BoardLayer(ordinal=39, canonical_name="F.Mask", layer_type=LayerType.USER, user_name="F.Mask"),
        BoardLayer(ordinal=40, canonical_name="Dwgs.User", layer_type=LayerType.USER, user_name="User Drawings"),
        BoardLayer(ordinal=41, canonical_name="Cmts.User", layer_type=LayerType.USER, user_name="User Comments"),
        BoardLayer(ordinal=42, canonical_name="Eco1.User", layer_type=LayerType.USER, user_name="User Eco1"),
        BoardLayer(ordinal=43, canonical_name="Eco2.User", layer_type=LayerType.USER, user_name="User Eco2"),
        BoardLayer(ordinal=44, canonical_name="Edge.Cuts", layer_type=LayerType.USER, user_name="Edge Cuts"),
        BoardLayer(ordinal=45, canonical_name="Margin", layer_type=LayerType.USER, user_name="Margin"),
        BoardLayer(ordinal=46, canonical_name="B.CrtYd", layer_type=LayerType.USER, user_name="B.Courtyard"),
        BoardLayer(ordinal=47, canonical_name="F.CrtYd", layer_type=LayerType.USER, user_name="F.Courtyard"),
        BoardLayer(ordinal=48, canonical_name="B.Fab", layer_type=LayerType.USER, user_name="B.Fabrication"),
        BoardLayer(ordinal=49, canonical_name="F.Fab", layer_type=LayerType.USER, user_name="F.Fabrication"),
    ]
    
    pcb.layers = layers
    
    # Create nets
    nets = [
        BoardNet(ordinal=0, name=""),  # Net 0 is always the unconnected net
        BoardNet(ordinal=1, name="GND"),
        BoardNet(ordinal=2, name="VCC"),
        BoardNet(ordinal=3, name="SIGNAL"),
    ]
    
    pcb.nets = nets
    
    # Add some track segments
    tracks = [
        # GND trace from (10,10) to (20,10)
        TrackSegment(
            start=(10.0, 10.0),
            end=(20.0, 10.0),
            width=0.25,
            layer="F.Cu",
            net=1,  # GND
            uuid=UUID("12345678-1234-1234-1234-123456789012")
        ),
        # VCC trace from (10,15) to (20,15)
        TrackSegment(
            start=(10.0, 15.0),
            end=(20.0, 15.0),
            width=0.25,
            layer="F.Cu",
            net=2,  # VCC
            uuid=UUID("12345678-1234-1234-1234-123456789013")
        ),
        # Signal trace from (10,20) to (20,20)
        TrackSegment(
            start=(10.0, 20.0),
            end=(20.0, 20.0),
            width=0.20,
            layer="F.Cu",
            net=3,  # SIGNAL
            uuid=UUID("12345678-1234-1234-1234-123456789014")
        ),
    ]
    
    pcb.track_segments = tracks
    
    # Add some vias
    vias = [
        # Via for GND connection
        TrackVia(
            position=(15.0, 10.0),
            size=0.8,
            drill=0.4,
            layers=("F.Cu", "B.Cu"),
            net=1,  # GND
            via_type=ViaType.THROUGH,
            uuid=UUID("87654321-4321-4321-4321-210987654321")
        ),
        # Via for VCC connection
        TrackVia(
            position=(15.0, 15.0),
            size=0.8,
            drill=0.4,
            layers=("F.Cu", "B.Cu"),
            net=2,  # VCC
            via_type=ViaType.THROUGH,
            uuid=UUID("87654321-4321-4321-4321-210987654322")
        ),
    ]
    
    pcb.track_vias = vias
    
    print(f"Created PCB with:")
    print(f"  - {len(pcb.layers)} layers")
    print(f"  - {len(pcb.nets)} nets")
    print(f"  - {len(pcb.track_segments)} track segments")
    print(f"  - {len(pcb.track_vias)} vias")
    
    return pcb


def demonstrate_pcb_operations():
    """Demonstrate various PCB operations"""
    print("=" * 60)
    print("KiCad PCB Parser - PCB Example")
    print("=" * 60)
    
    # Create example PCB
    pcb = create_example_pcb()
    
    # Display PCB information
    print(f"\nPCB Version: {pcb.version}")
    print(f"Generator: {pcb.generator}")
    print(f"Board thickness: {pcb.general.thickness}mm")
    
    # Display layers
    print(f"\nLayers ({len(pcb.layers)}):")
    for layer in pcb.layers[:10]:  # Show first 10 layers
        print(f"  {layer.ordinal:2d}: {layer.canonical_name:12s} ({layer.layer_type.value}) - {layer.user_name}")
    if len(pcb.layers) > 10:
        print(f"  ... and {len(pcb.layers) - 10} more layers")
    
    # Display nets
    print(f"\nNets ({len(pcb.nets)}):")
    for net in pcb.nets:
        print(f"  Net {net.ordinal}: {net.name or '(unnamed)'}")
    
    # Display tracks
    print(f"\nTrack Segments ({len(pcb.track_segments)}):")
    for i, track in enumerate(pcb.track_segments):
        print(f"  {i+1}: {track.start} -> {track.end}, width={track.width}mm, layer={track.layer}, net={track.net}")
    
    # Display vias
    print(f"\nVias ({len(pcb.track_vias)}):")
    for i, via in enumerate(pcb.track_vias):
        print(f"  {i+1}: pos={via.position}, size={via.size}mm, drill={via.drill}mm, {via.layers[0]}->{via.layers[1]}, net={via.net}")
    
    # Save PCB to file
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    pcb_file = output_dir / "example_board.kicad_pcb"
    
    print(f"\nSaving PCB to: {pcb_file}")
    save_pcb(pcb, pcb_file)
    print("PCB saved successfully!")
    
    # Load and verify
    print(f"\nLoading PCB from: {pcb_file}")
    loaded_pcb = load_pcb(pcb_file)
    
    print("Verification:")
    print(f"  Layers match: {len(loaded_pcb.layers) == len(pcb.layers)}")
    print(f"  Nets match: {len(loaded_pcb.nets) == len(pcb.nets)}")
    print(f"  Tracks match: {len(loaded_pcb.track_segments) == len(pcb.track_segments)}")
    print(f"  Vias match: {len(loaded_pcb.track_vias) == len(pcb.track_vias)}")
    
    # Demonstrate modification
    print("\nDemonstrating PCB modifications...")
    
    # Add a new net
    new_net = BoardNet(ordinal=4, name="DATA")
    loaded_pcb.nets.append(new_net)
    
    # Add a new track for the new net
    new_track = TrackSegment(
        start=(25.0, 10.0),
        end=(35.0, 10.0),
        width=0.15,
        layer="F.Cu",
        net=4,  # DATA
        uuid=UUID("12345678-1234-1234-1234-123456789015")
    )
    loaded_pcb.track_segments.append(new_track)
    
    print(f"Added net '{new_net.name}' and connected track")
    print(f"PCB now has {len(loaded_pcb.nets)} nets and {len(loaded_pcb.track_segments)} tracks")
    
    # Save modified PCB
    modified_pcb_file = output_dir / "modified_board.kicad_pcb"
    print(f"\nSaving modified PCB to: {modified_pcb_file}")
    save_pcb(loaded_pcb, modified_pcb_file)
    
    print("\nPCB example completed successfully!")
    print(f"Files created:")
    print(f"  - {pcb_file}")
    print(f"  - {modified_pcb_file}")


if __name__ == "__main__":
    demonstrate_pcb_operations()