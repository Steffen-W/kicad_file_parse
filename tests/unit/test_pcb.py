"""
Test PCB (Board) parsing functionality

Progress:
✅ LayerStackup, BoardSetup classes
✅ TrackSegment, Via, TrackArc classes
✅ NetConnection, ZoneFill, Zone classes
✅ BoardGroup, KiCadPCB classes
"""

import pytest

from kicad_parser import KiCadPCB, create_basic_pcb, load_pcb, save_pcb
from kicad_parser.kicad_board_elements import ZoneFillSettings
from kicad_parser.kicad_common import (
    UUID,
    CoordinatePoint,
    CoordinatePointList,
    Position,
)
from kicad_parser.kicad_pcb import (
    BoardLayer,
    BoardNet,
    BoardSetup,
    GeneralSettings,
    Group,
    LayerType,
    PadConnection,
    TrackArc,
    TrackSegment,
    TrackVia,
    ViaType,
    Zone,
    ZoneConnect,
)
from kicad_parser.sexpdata import Symbol


class TestPCBParsing:
    """Test PCB file parsing and generation"""

    def test_basic_pcb_creation(self):
        """Test creating a basic PCB"""
        pcb = create_basic_pcb()

        assert isinstance(pcb, KiCadPCB)
        assert pcb.version == 20230121
        assert pcb.generator == "kicad-parser"
        assert isinstance(pcb.general, GeneralSettings)
        assert isinstance(pcb.layers, list)

    def test_pcb_round_trip(self):
        """Test PCB serialization and deserialization"""
        # Create a basic PCB
        original_pcb = create_basic_pcb()

        # Add some basic components for testing
        original_pcb.layers.append(
            BoardLayer(
                ordinal=0,
                canonical_name="F.Cu",
                layer_type=LayerType.SIGNAL,
                user_name="Front Copper",
            )
        )

        original_pcb.nets.append(BoardNet(ordinal=0, name=""))

        # Convert to S-expression and back
        sexpr = original_pcb.to_sexpr()
        parsed_pcb = KiCadPCB.from_sexpr(sexpr)

        # Verify basic properties
        assert parsed_pcb.version == original_pcb.version
        assert parsed_pcb.generator == original_pcb.generator
        assert len(parsed_pcb.layers) == len(original_pcb.layers)
        assert len(parsed_pcb.nets) == len(original_pcb.nets)

        # Verify layer properties
        if parsed_pcb.layers:
            assert parsed_pcb.layers[0].canonical_name == "F.Cu"
            assert parsed_pcb.layers[0].layer_type == LayerType.SIGNAL

    def test_pcb_with_tracks(self):
        """Test PCB with track segments"""
        pcb = create_basic_pcb()

        # Add a track segment
        track = TrackSegment(
            start=(10.0, 10.0), end=(20.0, 20.0), width=0.25, layer="F.Cu", net=1
        )
        pcb.track_segments.append(track)

        # Test round-trip
        sexpr = pcb.to_sexpr()
        parsed_pcb = KiCadPCB.from_sexpr(sexpr)

        assert len(parsed_pcb.track_segments) == 1
        parsed_track = parsed_pcb.track_segments[0]
        assert parsed_track.start == (10.0, 10.0)
        assert parsed_track.end == (20.0, 20.0)
        assert parsed_track.width == 0.25
        assert parsed_track.layer == "F.Cu"
        assert parsed_track.net == 1

    def test_pcb_with_vias(self):
        """Test PCB with vias"""
        pcb = create_basic_pcb()

        # Add a via
        via = TrackVia(
            position=(15.0, 15.0),
            size=0.8,
            drill=0.4,
            layers=("F.Cu", "B.Cu"),
            net=1,
            via_type=ViaType.THROUGH,
        )
        pcb.track_vias.append(via)

        # Test round-trip
        sexpr = pcb.to_sexpr()
        parsed_pcb = KiCadPCB.from_sexpr(sexpr)

        assert len(parsed_pcb.track_vias) == 1
        parsed_via = parsed_pcb.track_vias[0]
        assert parsed_via.position == (15.0, 15.0)
        assert parsed_via.size == 0.8
        assert parsed_via.drill == 0.4
        assert parsed_via.layers == ("F.Cu", "B.Cu")
        assert parsed_via.net == 1
        assert parsed_via.via_type == ViaType.THROUGH

    def test_pcb_file_io(self, tmp_path):
        """Test PCB file save and load operations"""
        # Create a PCB with some content
        original_pcb = create_basic_pcb()
        original_pcb.layers.append(
            BoardLayer(
                ordinal=0,
                canonical_name="F.Cu",
                layer_type=LayerType.SIGNAL,
                user_name="Front Copper",
            )
        )

        # Save to file
        pcb_file = tmp_path / "test_board.kicad_pcb"
        save_pcb(original_pcb, pcb_file)

        # Verify file exists and has content
        assert pcb_file.exists()
        assert pcb_file.stat().st_size > 0

        # Load from file
        loaded_pcb = load_pcb(pcb_file)

        # Verify loaded PCB matches original
        assert loaded_pcb.version == original_pcb.version
        assert loaded_pcb.generator == original_pcb.generator
        assert len(loaded_pcb.layers) == len(original_pcb.layers)

        if loaded_pcb.layers:
            assert loaded_pcb.layers[0].canonical_name == "F.Cu"

    def test_layer_type_enum(self):
        """Test LayerType enum values"""
        assert LayerType.SIGNAL.value == "signal"
        assert LayerType.POWER.value == "power"
        assert LayerType.MIXED.value == "mixed"
        assert LayerType.JUMPER.value == "jumper"
        assert LayerType.USER.value == "user"

    def test_via_type_enum(self):
        """Test ViaType enum values"""
        assert ViaType.THROUGH.value == "through"
        assert ViaType.BLIND.value == "blind"
        assert ViaType.MICRO.value == "micro"

    def test_pad_connection_enum(self):
        """Test PadConnection enum values"""
        assert PadConnection.SOLID.value == "solid"
        assert PadConnection.THERMAL.value == "thermal"
        assert PadConnection.NONE.value == "none"


class TestPCBComponents:
    """Test individual PCB components"""

    def test_board_layer(self):
        """Test BoardLayer class"""
        layer = BoardLayer(
            ordinal=0,
            canonical_name="F.Cu",
            layer_type=LayerType.SIGNAL,
            user_name="Front Copper",
        )

        assert layer.ordinal == 0
        assert layer.canonical_name == "F.Cu"
        assert layer.layer_type == LayerType.SIGNAL
        assert layer.user_name == "Front Copper"

        # Test S-expression conversion
        sexpr = layer.to_sexpr()
        parsed_layer = BoardLayer.from_sexpr(sexpr)
        assert parsed_layer.ordinal == layer.ordinal
        assert parsed_layer.canonical_name == layer.canonical_name
        assert parsed_layer.layer_type == layer.layer_type
        assert parsed_layer.user_name == layer.user_name

    def test_board_net(self):
        """Test BoardNet class"""
        net = BoardNet(ordinal=1, name="VCC")

        assert net.ordinal == 1
        assert net.name == "VCC"

        # Test S-expression conversion
        sexpr = net.to_sexpr()
        parsed_net = BoardNet.from_sexpr(sexpr)
        assert parsed_net.ordinal == net.ordinal
        assert parsed_net.name == net.name

    def test_track_segment(self):
        """Test TrackSegment class"""
        track = TrackSegment(
            start=(0.0, 0.0), end=(10.0, 10.0), width=0.25, layer="F.Cu", net=1
        )

        assert track.start == (0.0, 0.0)
        assert track.end == (10.0, 10.0)
        assert track.width == 0.25
        assert track.layer == "F.Cu"
        assert track.net == 1

        # Test S-expression conversion
        sexpr = track.to_sexpr()
        parsed_track = TrackSegment.from_sexpr(sexpr)
        assert parsed_track.start == track.start
        assert parsed_track.end == track.end
        assert parsed_track.width == track.width
        assert parsed_track.layer == track.layer
        assert parsed_track.net == track.net

    def test_general_settings(self):
        """Test GeneralSettings class"""
        settings = GeneralSettings(thickness=1.6)

        assert settings.thickness == 1.6

        # Test S-expression conversion
        sexpr = settings.to_sexpr()
        parsed_settings = GeneralSettings.from_sexpr(sexpr)
        assert parsed_settings.thickness == settings.thickness


class TestBoardSetupComprehensive:
    """Comprehensive tests for BoardSetup class based on specification"""

    def test_board_setup_minimal(self):
        """Test minimal board setup with default values"""
        # Based on spec: (setup ...)
        setup = BoardSetup()

        assert setup.pad_to_mask_clearance == 0.0  # Default
        assert setup.solder_mask_min_width is None  # Default
        assert setup.aux_axis_origin is None  # Default

        # Test round-trip serialization
        result_sexpr = setup.to_sexpr()
        assert isinstance(result_sexpr, list)

    def test_board_setup_comprehensive(self):
        """Test comprehensive board setup with all parameters"""
        # Based on spec: (setup (pad_to_mask_clearance CLEARANCE) (solder_mask_min_width WIDTH) (aux_axis_origin X Y) (grid_origin X Y))
        sexpr = [
            Symbol("setup"),
            [Symbol("pad_to_mask_clearance"), 0.1],
            [Symbol("solder_mask_min_width"), 0.25],
            [Symbol("pad_to_paste_clearance"), 0.05],
            [Symbol("pad_to_paste_clearance_ratio"), -0.05],
            [Symbol("aux_axis_origin"), 50.0, 25.0],
            [Symbol("grid_origin"), 0.0, 0.0],
        ]
        setup = BoardSetup.from_sexpr(sexpr)

        assert setup.pad_to_mask_clearance == 0.1
        assert setup.solder_mask_min_width == 0.25
        assert setup.pad_to_paste_clearance == 0.05
        assert setup.pad_to_paste_clearance_ratio == -0.05
        assert setup.aux_axis_origin == (50.0, 25.0)
        assert setup.grid_origin == (0.0, 0.0)


class TestTrackArcComprehensive:
    """Comprehensive tests for TrackArc class based on specification"""

    def test_track_arc_minimal(self):
        """Test minimal track arc with start/mid/end and width"""
        # Based on spec: (arc (start X Y) (mid X Y) (end X Y) (width WIDTH) (layer LAYER) (net NET))
        arc = TrackArc(
            start=(0.0, 0.0),
            mid=(5.0, 5.0),
            end=(10.0, 0.0),
            width=0.25,
            layer="F.Cu",
            net=1,
        )

        assert arc.start == (0.0, 0.0)
        assert arc.mid == (5.0, 5.0)
        assert arc.end == (10.0, 0.0)
        assert arc.width == 0.25
        assert arc.layer == "F.Cu"
        assert arc.net == 1

    def test_track_arc_comprehensive(self):
        """Test comprehensive track arc with all attributes"""
        # Based on spec with timestamps and UUIDs
        sexpr = [
            Symbol("arc"),
            [Symbol("start"), 0.0, 0.0],
            [Symbol("mid"), 5.0, 5.0],
            [Symbol("end"), 10.0, 0.0],
            [Symbol("width"), 0.25],
            [Symbol("layer"), "B.Cu"],
            [Symbol("net"), 2],
            [Symbol("tstamp"), "550e8400-e29b-41d4-a716-446655440000"],
        ]
        arc = TrackArc.from_sexpr(sexpr)

        assert arc.start == (0.0, 0.0)
        assert arc.mid == (5.0, 5.0)
        assert arc.end == (10.0, 0.0)
        assert arc.width == 0.25
        assert arc.layer == "B.Cu"
        assert arc.net == 2
        assert arc.tstamp == "550e8400-e29b-41d4-a716-446655440000"


class TestZoneFillSettingsComprehensive:
    """Comprehensive tests for ZoneFillSettings class based on specification"""

    def test_zone_fill_settings_minimal(self):
        """Test minimal zone fill settings"""
        fill_settings = ZoneFillSettings()

        assert fill_settings.mode is None  # Default
        assert fill_settings.thermal_gap is None  # Default
        assert fill_settings.thermal_bridge_width is None  # Default

    def test_zone_fill_settings_comprehensive(self):
        """Test comprehensive zone fill settings with all parameters"""
        # Based on spec: complex fill settings with thermal reliefs, hatching, smoothing
        sexpr = [
            Symbol("fill"),
            Symbol("yes"),
            [Symbol("mode"), Symbol("hatch")],
            [Symbol("thermal_gap"), 0.5],
            [Symbol("thermal_bridge_width"), 0.5],
            [Symbol("hatch_thickness"), 0.508],
            [Symbol("hatch_gap"), 0.508],
            [Symbol("hatch_orientation"), 45],
            [Symbol("hatch_smoothing_level"), 3],
            [Symbol("hatch_smoothing_value"), 0.1],
            [Symbol("hatch_border_algorithm"), Symbol("hatch_thickness")],
            [Symbol("hatch_min_hole_area"), 0.3],
            [Symbol("smoothing"), Symbol("chamfer")],
            [Symbol("radius"), 1.0],
            [Symbol("island_removal_mode"), 1],
            [Symbol("island_area_min"), 10.0],
        ]
        fill_settings = ZoneFillSettings.from_sexpr(sexpr)

        assert fill_settings.filled is True
        assert fill_settings.mode == "hatch"
        assert fill_settings.thermal_gap == 0.5
        assert fill_settings.thermal_bridge_width == 0.5
        assert fill_settings.hatch_thickness == 0.508
        assert fill_settings.hatch_gap == 0.508
        assert fill_settings.hatch_orientation == 45
        assert fill_settings.smoothing == "chamfer"
        assert fill_settings.radius == 1.0
        assert fill_settings.island_removal_mode == 1
        assert fill_settings.island_area_min == 10.0


class TestZoneComprehensive:
    """Comprehensive tests for Zone class based on specification"""

    def test_zone_minimal(self):
        """Test minimal zone with outline points"""
        # Based on spec: (zone (net NET) (net_name "NAME") (layers LAYERS) (polygon POINTS))
        zone = Zone(
            net=1,
            net_name="VCC",
            layers=["F.Cu"],
            polygon_points=CoordinatePointList(
                [
                    CoordinatePoint(0, 0),
                    CoordinatePoint(10, 0),
                    CoordinatePoint(10, 10),
                    CoordinatePoint(0, 10),
                ]
            ),
        )

        assert zone.net == 1
        assert zone.net_name == "VCC"
        assert zone.layers == ["F.Cu"]
        assert len(zone.polygon_points.points) == 4

    def test_zone_comprehensive(self):
        """Test comprehensive zone with all features"""
        # Based on spec: zone with fills, keepouts, thermal settings
        sexpr = [
            Symbol("zone"),
            [Symbol("net"), 1],
            [Symbol("net_name"), "VCC"],
            [Symbol("layers"), "F.Cu"],
            [
                Symbol("hatch"),
                [Symbol("thickness"), 0.508],
                [Symbol("gap"), 0.508],
                [Symbol("orientation"), 45],
            ],
            [Symbol("connect_pads"), [Symbol("clearance"), 0.5]],
            [Symbol("min_thickness"), 0.254],
            [Symbol("filled_areas_thickness"), Symbol("no")],
            [
                Symbol("keepout"),
                [Symbol("tracks"), Symbol("allowed")],
                [Symbol("vias"), Symbol("allowed")],
                [Symbol("pads"), Symbol("allowed")],
                [Symbol("copperpour"), Symbol("not_allowed")],
                [Symbol("footprints"), Symbol("allowed")],
            ],
            [
                Symbol("fill"),
                Symbol("yes"),
                [Symbol("thermal_gap"), 0.508],
                [Symbol("thermal_bridge_width"), 0.508],
            ],
            [
                Symbol("polygon"),
                [
                    Symbol("pts"),
                    [Symbol("xy"), 0, 0],
                    [Symbol("xy"), 25.4, 0],
                    [Symbol("xy"), 25.4, 25.4],
                    [Symbol("xy"), 0, 25.4],
                ],
            ],
        ]
        zone = Zone.from_sexpr(sexpr)

        assert zone.net == 1
        assert zone.net_name == "VCC"
        assert zone.layers == ["F.Cu"]
        assert zone.hatch_thickness == 0.508
        assert zone.hatch_gap == 0.508
        assert zone.fill_settings.hatch_orientation == 45
        assert zone.connect_pads_clearance == 0.5
        assert zone.min_thickness == 0.254
        assert zone.filled_areas_thickness is False
        assert zone.keepout is not None
        assert zone.fill_settings is not None
        assert len(zone.polygon_points) == 4


class TestGroupComprehensive:
    """Comprehensive tests for Group class based on specification"""

    def test_group_minimal(self):
        """Test minimal group with name only"""
        # Based on spec: (group "NAME" ...)
        group = Group(name="PCB_Group")

        assert group.name == "PCB_Group"
        assert group.uuid.uuid == ""  # Default empty UUID
        assert len(group.members) == 0

    def test_group_comprehensive(self):
        """Test comprehensive group with members and UUID"""
        # Based on spec: (group "NAME" (uuid UUID) (members UUID1 UUID2 ...) [locked])
        sexpr = [
            Symbol("group"),
            "PCB_Group",
            [Symbol("uuid"), "group-uuid-123"],
            [Symbol("members"), "member-uuid-1", "member-uuid-2", "member-uuid-3"],
            Symbol("locked"),
        ]
        group = Group.from_sexpr(sexpr)

        assert group.name == "PCB_Group"
        assert group.uuid.uuid == "group-uuid-123"
        assert len(group.members) == 3
        assert any(m.uuid == "member-uuid-1" for m in group.members)
        assert any(m.uuid == "member-uuid-3" for m in group.members)
        assert group.locked is True


class TestKiCadPCBComprehensive:
    """Comprehensive tests for KiCadPCB class based on specification"""

    def test_kicad_pcb_minimal(self):
        """Test minimal KiCadPCB with version and generator"""
        # Based on spec: (kicad_pcb (version VERSION) (generator GENERATOR) (general ...) (layers ...) ...)
        pcb = KiCadPCB(version=20230121, generator="pytest")

        assert pcb.version == 20230121
        assert pcb.generator == "pytest"
        assert pcb.general is not None
        assert len(pcb.layers) >= 0
        assert len(pcb.nets) >= 0

    def test_kicad_pcb_comprehensive(self):
        """Test comprehensive KiCadPCB with all major components"""
        # Create comprehensive PCB with all features
        pcb = KiCadPCB(version=20230121, generator="comprehensive_test")

        # Add general settings
        pcb.general = GeneralSettings(thickness=1.6)

        # Add layers
        pcb.layers.extend(
            [
                BoardLayer(0, "F.Cu", LayerType.SIGNAL, "Front Copper"),
                BoardLayer(31, "B.Cu", LayerType.SIGNAL, "Back Copper"),
                BoardLayer(32, "B.Adhes", LayerType.USER, "Bottom Adhesive"),
                BoardLayer(33, "F.Adhes", LayerType.USER, "Front Adhesive"),
            ]
        )

        # Add nets
        pcb.nets.extend(
            [
                BoardNet(0, ""),
                BoardNet(1, "VCC"),
                BoardNet(2, "GND"),
                BoardNet(3, "SIGNAL_A"),
            ]
        )

        # Add board setup
        pcb.setup = BoardSetup(
            pad_to_mask_clearance=0.1,
            solder_mask_min_width=0.25,
            aux_axis_origin=(50.0, 25.0),
            grid_origin=(0.0, 0.0),
        )

        # Add track segments
        pcb.track_segments.extend(
            [
                TrackSegment((0, 0), (10, 10), 0.25, "F.Cu", 1),
                TrackSegment((10, 10), (20, 10), 0.25, "F.Cu", 1),
                TrackSegment((5, 5), (15, 15), 0.5, "B.Cu", 2),
            ]
        )

        # Add vias
        pcb.track_vias.extend(
            [
                TrackVia(
                    (10, 10), 0.8, 0.4, ("F.Cu", "B.Cu"), 1, via_type=ViaType.THROUGH
                ),
                TrackVia(
                    (15, 15), 0.6, 0.3, ("F.Cu", "In1.Cu"), 2, via_type=ViaType.BLIND
                ),
            ]
        )

        # Add track arcs
        pcb.track_arcs.append(TrackArc((0, 0), (5, 5), (10, 0), 0.25, "F.Cu", 3))

        # Add zones
        pcb.zones.append(
            Zone(
                net=1,
                net_name="VCC",
                layers=["F.Cu"],
                polygon_points=CoordinatePointList(
                    [
                        CoordinatePoint(0, 0),
                        CoordinatePoint(50, 0),
                        CoordinatePoint(50, 50),
                        CoordinatePoint(0, 50),
                    ]
                ),
                fill_settings=ZoneFillSettings(
                    filled=True, thermal_gap=0.5, thermal_bridge_width=0.5
                ),
            )
        )

        # Add groups
        pcb.groups.append(
            Group(
                name="Power_Components",
                uuid=UUID("power-group-uuid"),
                members=[UUID("component-1"), UUID("component-2")],
                locked=False,
            )
        )

        # Verify all components
        assert pcb.version == 20230121
        assert pcb.generator == "comprehensive_test"
        assert pcb.general.thickness == 1.6
        assert len(pcb.layers) == 4
        assert len(pcb.nets) == 4
        assert pcb.setup.pad_to_mask_clearance == 0.1
        assert len(pcb.track_segments) == 3
        assert len(pcb.track_vias) == 2
        assert len(pcb.track_arcs) == 1
        assert len(pcb.zones) == 1
        assert len(pcb.groups) == 1

        # Verify specific components
        assert pcb.layers[0].canonical_name == "F.Cu"
        assert pcb.nets[1].name == "VCC"
        assert pcb.track_segments[0].width == 0.25
        assert pcb.track_vias[0].via_type == ViaType.THROUGH
        assert pcb.zones[0].net_name == "VCC"
        assert pcb.groups[0].name == "Power_Components"

        # Test round-trip serialization
        result_sexpr = pcb.to_sexpr()
        assert result_sexpr[0] == Symbol("kicad_pcb")

        # Parse back and verify
        parsed_pcb = KiCadPCB.from_sexpr(result_sexpr)
        assert parsed_pcb.version == pcb.version
        assert parsed_pcb.generator == pcb.generator
        assert len(parsed_pcb.layers) == len(pcb.layers)
        assert len(parsed_pcb.nets) == len(pcb.nets)


class TestNetConnectionsAndConnectivity:
    """Test net connections and PCB connectivity features"""

    def test_net_connectivity_through_tracks(self):
        """Test net connectivity through track segments and vias"""
        pcb = create_basic_pcb()

        # Add nets
        pcb.nets.extend([BoardNet(0, ""), BoardNet(1, "VCC"), BoardNet(2, "GND")])

        # Add connected track segments
        pcb.track_segments.extend(
            [
                TrackSegment((0, 0), (10, 0), 0.25, "F.Cu", 1),  # VCC on F.Cu
                TrackSegment((10, 0), (10, 10), 0.25, "F.Cu", 1),  # VCC continuation
                TrackSegment((5, 5), (15, 5), 0.25, "B.Cu", 2),  # GND on B.Cu
            ]
        )

        # Add via connecting layers
        pcb.track_vias.append(
            TrackVia((10, 5), 0.8, 0.4, ("F.Cu", "B.Cu"), 1, ViaType.THROUGH)
        )

        # Verify connectivity
        vcc_segments = [seg for seg in pcb.track_segments if seg.net == 1]
        gnd_segments = [seg for seg in pcb.track_segments if seg.net == 2]
        vcc_vias = [via for via in pcb.track_vias if via.net == 1]

        assert len(vcc_segments) == 2
        assert len(gnd_segments) == 1
        assert len(vcc_vias) == 1
        assert vcc_vias[0].position == (10, 5)

    def test_zone_connectivity_and_fills(self):
        """Test zone connectivity with thermal reliefs and copper fills"""
        pcb = create_basic_pcb()

        # Add power and ground nets
        pcb.nets.extend([BoardNet(0, ""), BoardNet(1, "VCC"), BoardNet(2, "GND")])

        # Add power plane zone
        power_zone = Zone(
            net=1,
            net_name="VCC",
            layers=["In1.Cu"],
            polygon_points=CoordinatePointList(
                [
                    CoordinatePoint(0, 0),
                    CoordinatePoint(100, 0),
                    CoordinatePoint(100, 80),
                    CoordinatePoint(0, 80),
                ]
            ),
            fill_settings=ZoneFillSettings(
                filled=True,
                thermal_gap=0.5,
                thermal_bridge_width=0.4,
                island_removal_mode=1,
                island_area_min=10.0,
            ),
            connect_pads_clearance=0.2,
            min_thickness=0.254,
        )

        # Add ground plane zone
        ground_zone = Zone(
            net=2,
            net_name="GND",
            layers=["In2.Cu"],
            polygon_points=CoordinatePointList(
                [
                    CoordinatePoint(0, 0),
                    CoordinatePoint(100, 0),
                    CoordinatePoint(100, 80),
                    CoordinatePoint(0, 80),
                ]
            ),
            fill_settings=ZoneFillSettings(
                filled=True, mode="solid", thermal_gap=0.3, thermal_bridge_width=0.3
            ),
        )

        pcb.zones.extend([power_zone, ground_zone])

        # Verify zone properties
        assert len(pcb.zones) == 2

        power = pcb.zones[0]
        assert power.net_name == "VCC"
        assert power.fill_settings.thermal_gap == 0.5
        assert power.fill_settings.island_removal_mode == 1

        ground = pcb.zones[1]
        assert ground.net_name == "GND"
        assert ground.fill_settings.mode == "solid"
        assert ground.fill_settings.thermal_gap == 0.3


if __name__ == "__main__":
    pytest.main([__file__])
