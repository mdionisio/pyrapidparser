"""Robot models (robotmodel.py): loading, warnings, kinematics, confdata, dynamics."""

import math
import xml.etree.ElementTree as ET
from typing import Any

import pytest

np = pytest.importorskip("numpy")
pin = pytest.importorskip("pinocchio")

from run import robotmodel  # noqa: E402

if "irb120_3_58" not in robotmodel.available_models():
    pytest.skip(
        "submodule third_party/abb not checked out", allow_module_level=True
    )  # pragma: no cover

MODELS = sorted(robotmodel.available_models())


@pytest.mark.parametrize("name", MODELS)
def test_inverse_kinematics(name: str) -> None:
    """the solutions of the inverse kinematics reach the pose, one of them has the
    configuration (confdata) of the original axis positions"""
    robot = robotmodel.load(name, verbose=False)
    rng = np.random.default_rng(0)
    for _ in range(5):
        axes = rng.uniform(np.maximum(robot.lower, -math.pi), np.minimum(robot.upper, math.pi))
        target = robot.fk(axes)
        solutions = robot.ik(target, axes)
        assert solutions
        for solution in solutions:
            assert robot.within_limits(solution.axes)
            assert np.allclose(robot.fk(solution.axes).homogeneous, target.homogeneous, atol=1e-5)
        assert any(robot.matches(s.axes, robot.confdata(axes)) for s in solutions)


def test_irb120_zero_position() -> None:
    """tool0 at the calibration position: z of the flange pointing forward"""
    robot = robotmodel.load("irb120_3_58", verbose=False)
    assert robot.analytic is not None
    flange = robot.fk(np.zeros(6))
    assert np.allclose(flange.translation, [0.374, 0, 0.630])
    assert np.allclose(flange.rotation @ [0, 0, 1], [1, 0, 0])
    assert robot.confdata(np.zeros(6)) == (0, 0, 0, 0)


def test_confdata() -> None:
    """RAPID instructions manual, confdata: quadrants of the axes 1, 4, 6 and cfx"""
    robot = robotmodel.load("irb120_3_58", verbose=False)
    deg = np.radians
    assert robot.confdata(deg([100, 0, 0, -10, 30, 200])) == (1, -1, 2, 0)
    # axis 5 negative
    assert robot.confdata(deg([0, 0, 0, 0, -30, 0])) == (0, 0, 0, 1)
    # wrist center behind axis 1 and behind the lower arm: upper arm bent backwards
    assert robot.confdata(deg([0, 0, -100, 0, 30, 0]))[3] == 6
    # wrist center behind the lower arm only: lower arm forwards, upper arm upwards
    assert robot.confdata(deg([0, 70, -110, 0, 30, 0]))[3] == 2
    # wrist center behind axis 1 only: lower arm backwards
    assert robot.confdata(deg([0, -100, 60, 0, 30, 0]))[3] == 4


def test_warnings() -> None:
    irb120 = robotmodel.load("irb120_3_58", verbose=False)
    assert irb120.has_dynamics
    assert any("acceleration" in w for w in irb120.warnings)
    assert any("torque limits" in w for w in irb120.warnings)
    assert not any("inertial" in w for w in irb120.warnings)

    irb4600 = robotmodel.load("irb4600_60_205", verbose=False)
    assert not irb4600.has_dynamics
    assert any("no inertial data" in w for w in irb4600.warnings)


def test_warnings_printed(capsys: pytest.CaptureFixture[str]) -> None:
    robotmodel.load("irb4600_60_205")
    err = capsys.readouterr().err
    assert "warning: irb4600_60_205: no inertial data" in err


def test_irb460() -> None:
    """the 4 axis palletizer (lengths of the ABB CAD model): the flange at the zero
    position and the top of the working range of the data sheet (1786 mm), the flange
    stays horizontal, the parallel linkage closes"""
    robot = robotmodel.load("irb460_110_240", verbose=False)
    assert robot.rapid_axes == [1, 2, 3, 6]
    assert robot.warnings[0].startswith("approximate model:")
    assert np.allclose(robot.fk(np.zeros(4)).translation, [1.505, 0, 1.436])
    top = robot.fk(np.radians([0, 0, -20, 0]))
    assert top.translation[2] == pytest.approx(1.786, abs=0.001)
    model, data = robot.model, robot.data

    def world(frame: str, local: list[float]) -> Any:
        return data.oMf[model.getFrameId(frame)].act(np.array(local))

    for axes in ([0, 30, 60, 0], [40, -20, 100, 90], [-100, 80, -10, -200]):
        flange = robot.fk(np.radians(axes))
        assert np.allclose(flange.rotation @ [0, 0, 1], [0, 0, -1])
        # first parallelogram: p_arm, p_link, the rear lever of the upper arm
        assert np.allclose(world("p_link", [0, 0, 0.945]), world("link_3", [-0.4, 0, 0]))
        # second: the swing, lower_link, link_plate; then upper_link, the wrist
        assert np.allclose(
            world("lower_link", [0, 0, 0.945]), world("link_plate", [-0.2649, 0, 0.1408])
        )
        assert np.allclose(world("upper_link", [1.025, 0, 0]), world("link_4", [0.2298, 0, 0.1928]))


def test_osj6() -> None:
    """the oblique swivel joint robot (the modular kit of examples/osj6/cad): the tube
    straight up is singular (the joint axes in one plane); the numeric inverse kinematics
    finds the pen-down positions from the home position (random starting positions); the
    parts of the view are found"""
    robot = robotmodel.load("osj6", geometry=True, verbose=False)
    assert robot.analytic is None
    assert np.allclose(robot.fk(np.zeros(6)).translation, [0, 0, 0.7696], atol=1e-4)
    q = robot.configuration(np.zeros(6))
    jacobian = pin.computeFrameJacobian(
        robot.model, robot.data, q, robot.flange_frame, pin.ReferenceFrame.LOCAL
    )
    assert np.linalg.matrix_rank(jacobian, tol=1e-6) == 3
    # a 180 degree turn of an oblique joint bends the tube by 90 degrees
    bent = robot.fk(np.radians([0, 180, 0, 0, 0, 0]))
    assert np.allclose(bent.rotation @ [0, 0, 1], [0, -1, 0], atol=1e-6)
    assert np.allclose(bent.translation, [0, -0.6156, 0.154], atol=1e-4)
    down = pin.SE3(np.diag([-1.0, 1.0, -1.0]), np.array([0.25, -0.05, 0.15]))
    solutions = robot.ik(down, robot.home)
    assert solutions
    assert np.allclose(robot.fk(solutions[0].axes).homogeneous, down.homogeneous, atol=1e-5)
    assert len(robot.visual_model.geometryObjects) > 20


def test_cad_meshes(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """cad_meshes: a CAD part at the zero position replaces the geometry of its link,
    placed in the link frame"""
    stl = tmp_path / "part.stl"
    # a binary STL with one triangle
    stl.write_bytes(b"\0" * 80 + (1).to_bytes(4, "little") + b"\0" * 50)
    monkeypatch.setattr(robotmodel, "MODELS_DIR", str(tmp_path))
    robot = robotmodel.load("irb120_3_58", verbose=False)
    xml = robotmodel._cad_xml(robot, robot.xml, {"scale": 0.001, "links": {"link_3": "part.stl"}})
    link = [e for e in ET.fromstring(xml).iter("link") if e.get("name") == "link_3"][0]
    visuals = link.findall("visual")
    assert len(visuals) == 1
    mesh = visuals[0].find("geometry/mesh")
    origin_element = visuals[0].find("origin")
    assert mesh is not None and origin_element is not None
    assert mesh.get("filename") == str(stl)
    # link_3 is at x 0, z 0.56 at the zero position: the mesh origin is the opposite
    origin = [float(v) for v in origin_element.get("xyz", "").split()]
    assert origin == pytest.approx([0, 0, -0.56])


def test_torques() -> None:
    robot = robotmodel.load("irb120_3_58", verbose=False)
    zero = np.zeros(6)
    static = robot.torques(zero, zero, zero)
    # gravity: the arm stretched forward loads the axes 2 and 3, not the axis 1
    assert abs(static[0]) < 1e-9
    assert abs(static[1]) > 1 and abs(static[2]) > 1
    robot.set_payload(3.0, np.array([0, 0, 0.1]), np.zeros(3))
    loaded = robot.torques(zero, zero, zero)
    assert abs(loaded[1]) > abs(static[1])
    robot.set_payload(0.0, np.zeros(3), np.zeros(3))
    assert np.allclose(robot.torques(zero, zero, zero), static)


def test_unknown_model() -> None:
    with pytest.raises(robotmodel.ModelError):
        robotmodel.find_model("irb999")
