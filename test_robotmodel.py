"""Robot models (robotmodel.py): loading, warnings, kinematics, confdata, dynamics."""

import math

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("pinocchio")

import robotmodel  # noqa: E402

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


def test_irb460_approximate() -> None:
    """the approximate 4 axis palletizer matches the reach and the height of the
    data sheet, the flange stays horizontal"""
    robot = robotmodel.load("irb460_approx", verbose=False)
    assert robot.rapid_axes == [1, 2, 3, 6]
    assert robot.warnings[0].startswith("approximate model:")
    reach = robot.fk(np.radians([0, 85, 0, 0]))
    assert reach.translation[0] == pytest.approx(2.403, abs=0.005)
    top = robot.fk(np.radians([0, 0, -20, 0]))
    assert top.translation[2] == pytest.approx(1.786, abs=0.005)
    for axes in ([0, 30, 60, 0], [40, -20, 100, 90]):
        flange = robot.fk(np.radians(axes))
        assert np.allclose(flange.rotation @ [0, 0, 1], [0, 0, -1])


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
