"""Motion instructions (run/pyrapid_motion.py) on the robot models."""

import math
from typing import Any, Sequence

import pytest

np = pytest.importorskip("numpy")
pin = pytest.importorskip("pinocchio")

import robotmodel  # noqa: E402
import run.pyrapid as pyrapid  # noqa: E402
from run import pyrapid_motion as motion  # noqa: E402

if "irb120_3_58" not in robotmodel.available_models():
    pytest.skip(
        "submodule third_party/abb not checked out", allow_module_level=True
    )  # pragma: no cover

EXTAX = [9e9] * 6
TOOL0 = pyrapid.rapid_tooldata(
    [True, [[0, 0, 0], [1, 0, 0, 0]], [0.001, [0, 0, 0.001], [1, 0, 0, 0], 0, 0, 0]]
)
WOBJ0 = pyrapid.rapid_wobjdata(
    [False, True, "", [[0, 0, 0], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]]
)


def speed(v_tcp: float, v_ori: float = 500) -> Any:
    return pyrapid.rapid_speeddata([v_tcp, v_ori, 5000, 1000])


def robtarget(trans: Sequence[float], rot: Sequence[float], conf: Sequence[int]) -> Any:
    return pyrapid.rapid_robtarget([trans, rot, conf, EXTAX])


def jointtarget(axes: Sequence[float]) -> Any:
    return pyrapid.rapid_jointtarget([axes, EXTAX])


@pytest.fixture
def controller(monkeypatch: pytest.MonkeyPatch) -> Any:
    """a new controller with the IRB 120 at the home position"""
    monkeypatch.delenv("PYRAPID_VIEWER", raising=False)
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    motion.UseRobot("irb120_3_58")
    return motion.CONTROLLER


def record(executed: list[Any]) -> Any:
    def execute(self: Any, trajectory: Any) -> None:
        executed.append(trajectory)
        original(self, trajectory)

    original = motion.Controller.execute
    return execute


@pytest.fixture
def trajectories(monkeypatch: pytest.MonkeyPatch, controller: Any) -> list[Any]:
    executed: list[Any] = []
    monkeypatch.setattr(motion.Controller, "execute", record(executed))
    return executed


def check_limits(robot: Any, trajectory: Any) -> None:
    for sample in trajectory.samples:
        assert np.all(np.abs(sample.velocity) <= robot.velocity * 1.001)
        assert np.all(np.abs(sample.acceleration) <= robot.acceleration * 1.05)
        assert robot.within_limits(sample.axes)


def test_trapezoid() -> None:
    profile = motion.trapezoid(2.0, 0.5)
    assert profile(0) == (0.0, 0.0, 0.0)
    assert profile(2.0)[0] == 1.0
    assert profile(1.0)[0] == pytest.approx(0.5)
    # cruise speed: the distance 1 in 2 s with 0.5 s of acceleration
    assert profile(1.0)[1] == pytest.approx(1 / 1.5)


def test_move_abs_j(controller: Any, trajectories: list[Any]) -> None:
    motion.MoveAbsJ(jointtarget([90, 0, 0, 0, 0, 0]), speed(5000), -1, -1, TOOL0)
    robot = controller.robot
    assert np.allclose(np.degrees(controller.axes), [90, 0, 0, 0, 0, 0])
    trajectory = trajectories[-1]
    check_limits(robot, trajectory)
    # axis 1 at its maximum speed of 250 deg/s with 0.5 s to reach it: 0.36 + 0.5 s
    assert trajectory.duration == pytest.approx(90 / 250 + 0.5, abs=0.02)


def test_move_abs_j_time(controller: Any, trajectories: list[Any]) -> None:
    """\\T sets the time of the movement"""
    motion.MoveAbsJ(jointtarget([10, 0, 0, 0, 0, 0]), speed(100), -1, 3.0, TOOL0)
    assert trajectories[-1].duration == pytest.approx(3.0)


def test_move_j_configuration(controller: Any) -> None:
    """MoveJ reaches the target with the configuration of the robtarget (ConfJ \\On)"""
    robot = controller.robot
    axes = np.radians([0, 10, 10, -30, 40, 20])
    trans, rot = motion.pose_values(robot.fk(axes))
    motion.MoveJ(robtarget(trans, rot, [0, -1, 0, 0]), speed(1000), -1, -1, TOOL0, WOBJ0)
    assert np.allclose(controller.axes, axes)
    # the same pose with the wrist turned: axis 4 + 180, axis 5 negative, axis 6 + 180
    motion.MoveJ(robtarget(trans, rot, [0, 1, 2, 1]), speed(1000), -1, -1, TOOL0, WOBJ0)
    assert np.allclose(np.degrees(controller.axes), [0, 10, 10, 150, -40, 200])
    assert robot.confdata(controller.axes) == (0, 1, 2, 1)


def test_move_j_wrong_configuration(controller: Any) -> None:
    with pytest.raises(motion.MotionError, match="no solution with the configuration"):
        motion.MoveJ(
            robtarget([400, 0, 400], [0, 0, 1, 0], [2, 0, 0, 0]),
            speed(1000),
            -1,
            -1,
            TOOL0,
            WOBJ0,
        )


def test_outside_reach(controller: Any) -> None:
    with pytest.raises(motion.MotionError, match="outside reach"):
        motion.MoveJ(
            robtarget([2000, 0, 400], [0, 0, 1, 0], [0, 0, 0, 0]),
            speed(1000),
            -1,
            -1,
            TOOL0,
            WOBJ0,
        )


def test_move_l_straight_line(controller: Any, trajectories: list[Any]) -> None:
    rot = [0, 0, 1, 0]
    motion.MoveJ(
        robtarget([400, -100, 400], rot, [-1, 0, -1, 0]), speed(1000), -1, -1, TOOL0, WOBJ0
    )
    motion.MoveL(robtarget([400, -100, 200], rot, [-1, 0, -1, 0]), speed(100), -1, -1, TOOL0, WOBJ0)
    robot = controller.robot
    trajectory = trajectories[-1]
    check_limits(robot, trajectory)
    # 200 mm at 100 mm/s, 0.2 s of acceleration
    assert trajectory.duration == pytest.approx(2.2, abs=0.01)
    for sample in trajectory.samples:
        flange = robot.fk(sample.axes)
        assert flange.translation[0] == pytest.approx(0.4, abs=1e-4)
        assert flange.translation[1] == pytest.approx(-0.1, abs=1e-4)
        assert np.allclose(flange.rotation @ [0, 0, 1], [0, 0, -1], atol=1e-4)


def test_move_l_slows_down(controller: Any, trajectories: list[Any]) -> None:
    """a fast linear movement is slowed down to the speed of the axes"""
    rot = [0, 0, 1, 0]
    motion.MoveJ(
        robtarget([300, -200, 300], rot, [-1, 0, -1, 0]), speed(1000), -1, -1, TOOL0, WOBJ0
    )
    motion.ConfL(False)
    motion.MoveL(robtarget([300, 200, 300], rot, [0, 0, 0, 0]), speed(7000), -1, -1, TOOL0, WOBJ0)
    trajectory = trajectories[-1]
    check_limits(controller.robot, trajectory)
    assert trajectory.duration > 0.4 / 7.0 + 0.2


def test_conf_l(controller: Any) -> None:
    """ConfL \\On: the end point must have the programmed configuration"""
    rot = [0, 0, 1, 0]
    motion.MoveJ(
        robtarget([400, -100, 400], rot, [-1, 0, -1, 0]), speed(1000), -1, -1, TOOL0, WOBJ0
    )
    with pytest.raises(motion.MotionError, match="ConfL"):
        motion.MoveL(
            robtarget([400, 100, 400], rot, [-1, 0, -1, 0]), speed(100), -1, -1, TOOL0, WOBJ0
        )


def test_move_c(controller: Any, trajectories: list[Any]) -> None:
    rot = [0, 0, 1, 0]
    motion.MoveJ(robtarget([400, 100, 300], rot, [0, 0, 0, 0]), speed(1000), -1, -1, TOOL0, WOBJ0)
    motion.ConfL(False)
    motion.MoveC(
        robtarget([450, 50, 300], rot, [0, 0, 0, 0]),
        robtarget([400, 0, 300], rot, [0, 0, 0, 0]),
        speed(100),
        -1,
        -1,
        TOOL0,
        WOBJ0,
    )
    trajectory = trajectories[-1]
    assert trajectory.duration == pytest.approx(math.pi * 50 / 100 + 0.2, abs=0.02)
    for sample in trajectory.samples:
        p = controller.robot.fk(sample.axes).translation
        assert math.hypot(p[0] - 0.4, p[1] - 0.05) == pytest.approx(0.05, abs=1e-4)
        assert p[0] >= 0.4 - 1e-6


def test_tool_and_wobj(controller: Any) -> None:
    """robtargets are TCP positions in the work object"""
    tool = pyrapid.rapid_tooldata(
        [True, [[0, 0, 100], [1, 0, 0, 0]], [1, [0, 0, 50], [1, 0, 0, 0], 0, 0, 0]]
    )
    wobj = pyrapid.rapid_wobjdata(
        [False, True, "", [[300, 0, 100], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]]
    )
    target = robtarget([100, 0, 200], [0, 0, 1, 0], [0, 0, 0, 0])
    motion.MoveJ(target, speed(1000), -1, -1, tool, wobj)
    # TCP at [400, 0, 300] in the base frame, tool z pointing down: flange 100 mm higher
    flange = controller.robot.fk(controller.axes)
    assert np.allclose(flange.translation, [0.4, 0, 0.4], atol=1e-6)
    result = pyrapid.rapid_robtarget()
    motion.CRobT(result, tool, wobj)
    assert [result.GetElem("trans").GetElem(c).Get() for c in "xyz"] == pytest.approx([100, 0, 200])


def test_offs_reltool() -> None:
    point = robtarget([400, 0, 300], [0, 0, 1, 0], [0, 0, 0, 0])
    result = pyrapid.rapid_robtarget()
    motion.Offs(result, point, 10, 20, 30)
    assert [result.GetElem("trans").GetElem(c).Get() for c in "xyz"] == [410, 20, 330]
    # the original point does not change
    assert point.GetElem("trans").GetElem("x").Get() == 400
    # in the tool frame (z pointing down): 50 mm along z is 50 mm lower
    motion.RelTool(result, point, 0, 0, 50, 0, 0, 90)
    assert [result.GetElem("trans").GetElem(c).Get() for c in "xyz"] == pytest.approx([400, 0, 250])
    rot = [result.GetElem("rot").GetElem(c).Get() for c in ("q1", "q2", "q3", "q4")]
    expected = pin.Quaternion(pin.utils.rotate("y", math.pi) @ pin.utils.rotate("z", math.pi / 2))
    x, y, z, w = expected.coeffs()
    assert np.allclose(np.abs(rot), np.abs([w, x, y, z]), atol=1e-9)


def test_calc_joint_t(controller: Any) -> None:
    point = robtarget([400, 0, 400], [0, 0, 1, 0], [0, 0, 0, 0])
    joints = pyrapid.rapid_jointtarget()
    motion.CalcJointT(joints, point, TOOL0, WOBJ0)
    back = pyrapid.rapid_robtarget()
    motion.CalcRobT(back, joints, TOOL0, WOBJ0)
    assert [back.GetElem("trans").GetElem(c).Get() for c in "xyz"] == pytest.approx([400, 0, 400])
    assert [back.GetElem("robconf").GetElem(c).Get() for c in ("cf1", "cf4", "cf6", "cfx")] == [
        0,
        0,
        0,
        0,
    ]


def test_palletizer(monkeypatch: pytest.MonkeyPatch, trajectories: list[Any]) -> None:
    """the 4 axis robot: axes 1, 2, 3 and 6, the flange stays horizontal"""
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    motion.UseRobot("irb460_approx")
    controller: Any = motion.CONTROLLER
    rot = [0, 0, 1, 0]
    motion.MoveJ(robtarget([1500, 0, 800], rot, [0, 0, 0, 0]), speed(2000), -1, -1, TOOL0, WOBJ0)
    motion.MoveL(robtarget([1500, 0, 300], rot, [0, 0, 0, 0]), speed(1000), -1, -1, TOOL0, WOBJ0)
    flange = controller.robot.fk(controller.axes)
    assert np.allclose(flange.translation, [1.5, 0, 0.3], atol=1e-5)
    joints = pyrapid.rapid_jointtarget()
    motion.CJointT(joints)
    robax = [joints.GetElem("robax").GetElem("rax_%d" % i).Get() for i in range(1, 7)]
    assert robax[3] == robax[4] == 0
    check_limits(controller.robot, trajectories[-1])


def test_no_robot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    with pytest.raises(motion.MotionError, match="!robot:"):
        motion.MoveAbsJ(jointtarget([0, 0, 0, 0, 0, 0]), speed(100), -1, -1, TOOL0)
