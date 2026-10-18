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
FINE = pyrapid.rapid_zonedata([True, 0, 0, 0, 0, 0, 0])
DOWN = [0, 0, 1, 0]


def zone(radius: float) -> Any:
    return pyrapid.rapid_zonedata([False, radius, radius, radius, 1, radius, 1])


def speed(v_tcp: float, v_ori: float = 500) -> Any:
    return pyrapid.rapid_speeddata([v_tcp, v_ori, 5000, 1000])


def robtarget(trans: Sequence[float], rot: Sequence[float], conf: Sequence[int]) -> Any:
    return pyrapid.rapid_robtarget([list(trans), list(rot), list(conf), EXTAX])


def jointtarget(axes: Sequence[float]) -> Any:
    return pyrapid.rapid_jointtarget([list(axes), EXTAX])


def move_abs_j(
    axes: Sequence[float], v: float = 1000, z: Any = FINE, conc: bool = False, t: float = -1
) -> None:
    motion.MoveAbsJ(conc, jointtarget(axes), speed(v), -1, t, z, -1, TOOL0)


def move_j(
    trans: Sequence[float],
    conf: Sequence[int],
    v: float = 1000,
    z: Any = FINE,
    tool: Any = TOOL0,
    wobj: Any = WOBJ0,
    rot: Sequence[float] = DOWN,
) -> None:
    motion.MoveJ(False, robtarget(trans, rot, conf), speed(v), -1, -1, z, -1, tool, wobj)


def move_l(
    trans: Sequence[float],
    conf: Sequence[int],
    v: float = 100,
    z: Any = FINE,
    conc: bool = False,
    rot: Sequence[float] = DOWN,
) -> None:
    motion.MoveL(conc, robtarget(trans, rot, conf), speed(v), -1, -1, z, -1, TOOL0, WOBJ0)


def tcp() -> Any:
    """current TCP position (m)"""
    return motion.CONTROLLER.tcp(motion.CONTROLLER.current(), motion.CONTROLLER.tool).translation


@pytest.fixture
def controller(monkeypatch: pytest.MonkeyPatch) -> Any:
    """a new controller with the IRB 120 at the home position, simulated time"""
    monkeypatch.delenv("PYRAPID_VIEWER", raising=False)
    monkeypatch.delenv("PYRAPID_REALTIME", raising=False)
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    motion.UseRobot("irb120_3_58")
    return motion.CONTROLLER


def check_limits(robot: Any, segment: Any) -> None:
    for velocity, acceleration, axes in zip(segment.velocity, segment.acceleration, segment.axes):
        assert np.all(np.abs(velocity) <= robot.velocity * 1.001)
        assert np.all(np.abs(acceleration) <= robot.acceleration * 1.05)
        assert robot.within_limits(axes)


class Recorder:
    """the TCP positions of the robot thread, sample by sample"""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.points: list[Any] = []
        step = motion.Controller.step

        def recording(this: Any) -> None:
            step(this)
            self.points.append(this.tcp(this.axes, this.tool).translation.copy())

        monkeypatch.setattr(motion.Controller, "step", recording)

    def distance_to(self, point: Sequence[float]) -> float:
        p = np.array(point) / 1000.0
        return float(min(np.linalg.norm(q - p) for q in self.points))


def test_trapezoid() -> None:
    profile = motion.trapezoid(2.0, 0.5)
    assert profile(0) == (0.0, 0.0, 0.0)
    assert profile(2.0)[0] == 1.0
    assert profile(1.0)[0] == pytest.approx(0.5)
    # cruise speed: the distance 1 in 2 s with 0.5 s of acceleration
    assert profile(1.0)[1] == pytest.approx(1 / 1.5)


def test_move_abs_j(controller: Any) -> None:
    move_abs_j([90, 0, 0, 0, 0, 0], v=5000)
    assert np.allclose(np.degrees(controller.current()), [90, 0, 0, 0, 0, 0])
    segment = controller.completed[-1]
    check_limits(controller.robot, segment)
    # axis 1 at its maximum speed of 250 deg/s with 0.5 s to reach it: 0.36 + 0.5 s
    assert segment.duration == pytest.approx(90 / 250 + 0.5, abs=0.02)
    assert controller.time == pytest.approx(segment.duration, abs=0.011)


def test_move_abs_j_time(controller: Any) -> None:
    """\\T sets the time of the movement"""
    move_abs_j([10, 0, 0, 0, 0, 0], v=100, t=3.0)
    assert controller.completed[-1].duration == pytest.approx(3.0)


def test_move_j_configuration(controller: Any) -> None:
    """MoveJ reaches the target with the configuration of the robtarget (ConfJ \\On)"""
    robot = controller.robot
    axes = np.radians([0, 10, 10, -30, 40, 20])
    trans, rot = motion.pose_values(robot.fk(axes))
    move_j(trans, [0, -1, 0, 0], rot=rot)
    assert np.allclose(controller.current(), axes)
    # the same pose with the wrist turned: axis 4 + 180, axis 5 negative, axis 6 + 180
    move_j(trans, [0, 1, 2, 1], rot=rot)
    assert np.allclose(np.degrees(controller.current()), [0, 10, 10, 150, -40, 200])
    assert robot.confdata(controller.current()) == (0, 1, 2, 1)


def test_move_j_wrong_configuration(controller: Any) -> None:
    with pytest.raises(motion.MotionError, match="no solution with the configuration"):
        move_j([400, 0, 400], [2, 0, 0, 0])


def test_outside_reach(controller: Any) -> None:
    with pytest.raises(motion.MotionError, match="outside reach"):
        move_j([2000, 0, 400], [0, 0, 0, 0])


def test_move_l_straight_line(controller: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    move_j([400, -100, 400], [-1, 0, -1, 0])
    recorder = Recorder(monkeypatch)
    move_l([400, -100, 200], [-1, 0, -1, 0])
    segment = controller.completed[-1]
    check_limits(controller.robot, segment)
    # 200 mm at 100 mm/s, 0.2 s of acceleration
    assert segment.duration == pytest.approx(2.2, abs=0.01)
    for point in recorder.points:
        assert point[0] == pytest.approx(0.4, abs=1e-4)
        assert point[1] == pytest.approx(-0.1, abs=1e-4)
    # stop point: the program continues with the robot at the point
    assert np.allclose(tcp(), [0.4, -0.1, 0.2], atol=1e-9)


def test_move_l_slows_down(controller: Any) -> None:
    """a fast linear movement is slowed down to the speed of the axes"""
    move_j([300, -200, 300], [-1, 0, -1, 0])
    motion.ConfL(False)
    move_l([300, 200, 300], [0, 0, 0, 0], v=7000)
    segment = controller.completed[-1]
    check_limits(controller.robot, segment)
    assert segment.duration > 0.4 / 7.0 + 0.2


def test_conf_l(controller: Any) -> None:
    """ConfL \\On: the end point must have the programmed configuration"""
    move_j([400, -100, 400], [-1, 0, -1, 0])
    with pytest.raises(motion.MotionError, match="ConfL"):
        move_l([400, 100, 400], [-1, 0, -1, 0])


def test_move_c(controller: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    move_j([400, 100, 300], [0, 0, 0, 0])
    motion.ConfL(False)
    recorder = Recorder(monkeypatch)
    motion.MoveC(
        False,
        robtarget([450, 50, 300], DOWN, [0, 0, 0, 0]),
        robtarget([400, 0, 300], DOWN, [0, 0, 0, 0]),
        speed(100),
        -1,
        -1,
        FINE,
        -1,
        TOOL0,
        WOBJ0,
    )
    assert controller.completed[-1].duration == pytest.approx(math.pi * 50 / 100 + 0.2, abs=0.02)
    for p in recorder.points:
        assert math.hypot(p[0] - 0.4, p[1] - 0.05) == pytest.approx(0.05, abs=1e-4)
        assert p[0] >= 0.4 - 1e-6


def test_fly_by_point(controller: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """z50: the program continues before the robot enters the zone, the next movement
    starts in the zone, the robot passes near the point without stopping"""
    move_j([400, -150, 400], [-1, 0, -1, 0])
    start = controller.time
    recorder = Recorder(monkeypatch)
    move_l([400, -150, 250], [-1, 0, -1, 0], z=zone(50))
    # the program continues PREFETCH_TIME before the zone: the robot is still outside
    distance = float(np.linalg.norm(tcp() - [0.4, -0.15, 0.25]))
    assert 0.05 < distance < 0.05 + 0.1 * motion.PREFETCH_TIME + 0.002
    move_l([400, -50, 250], [-1, 0, -1, 0])
    # corner path: not through the point, inside the zone
    assert 0.005 < recorder.distance_to([400, -150, 250]) < 0.05
    corner = [p for p in recorder.points if np.linalg.norm(p - [0.4, -0.15, 0.25]) < 0.05]
    assert corner and all(p[2] >= 0.25 - 1e-6 and p[1] >= -0.15 - 1e-6 for p in corner)
    # out of the zone the robot is on the line from the programmed point
    after = [p for p in recorder.points if p[1] > -0.15 + 0.05 + 0.001]
    assert after and all(abs(p[2] - 0.25) < 1e-4 and abs(p[0] - 0.4) < 1e-4 for p in after)
    assert np.allclose(tcp(), [0.4, -0.05, 0.25], atol=1e-9)
    # faster than two stop points: 150 mm and 100 mm at 100 mm/s with 0.2 s ramps
    assert controller.time - start < 1.5 + 0.2 + 1.0 + 0.2
    first, second = controller.completed[-2:]
    assert first.blend is not None and second.start < first.start + first.duration


def test_zone_reduced(controller: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """the zone is at most half the movement: z200 between two 40 mm movements"""
    move_j([400, -150, 300], [-1, 0, -1, 0])
    recorder = Recorder(monkeypatch)
    move_l([400, -110, 300], [-1, 0, -1, 0], z=zone(200))
    move_l([400, -110, 260], [-1, 0, -1, 0])
    distance = recorder.distance_to([400, -110, 300])
    assert 0.001 < distance < 0.02


def test_corner_path_failure(
    controller: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """the next movement comes too late: the fly-by point becomes a stop point"""
    move_j([400, -150, 400], [-1, 0, -1, 0])
    recorder = Recorder(monkeypatch)
    move_l([400, -150, 250], [-1, 0, -1, 0], z=zone(50))
    motion.WaitTime(2.0)
    move_l([400, -50, 250], [-1, 0, -1, 0])
    assert recorder.distance_to([400, -150, 250]) < 1e-6
    assert "corner path failure" in capsys.readouterr().err


def test_conc(controller: Any) -> None:
    """\\Conc: the program continues at once, the robot moves while the program runs"""
    move_j([400, -150, 400], [-1, 0, -1, 0])
    before = tcp().copy()
    move_l([400, -150, 200], [-1, 0, -1, 0], conc=True)
    assert np.allclose(tcp(), before)
    motion.WaitTime(1.0)
    middle = tcp()
    assert 0.2 < middle[2] < 0.4
    motion.WaitRob()
    assert np.allclose(tcp(), [0.4, -0.15, 0.2], atol=1e-9)


def test_conc_queue(controller: Any) -> None:
    """at most MAX_CONC movements with \\Conc in the queue"""
    for i in range(8):
        move_abs_j([10 * (i % 2), 0, 0, 0, 30, 0], conc=True)
        assert len(controller.queue) <= motion.MAX_CONC
    motion.WaitRob()
    assert len(controller.completed) == 8


def test_wait_time_inpos(controller: Any) -> None:
    move_abs_j([90, 0, 0, 0, 0, 0], conc=True)
    motion.WaitTime(0.0, True)
    assert np.allclose(np.degrees(controller.current()), [90, 0, 0, 0, 0, 0])


def test_finish(controller: Any) -> None:
    """the end of the program: the robot completes the movements"""
    move_abs_j([45, 0, 0, 0, 30, 0], conc=True)
    controller.finish()
    assert np.allclose(np.degrees(controller.current()), [45, 0, 0, 0, 30, 0])


def test_tool_and_wobj(controller: Any) -> None:
    """robtargets are TCP positions in the work object"""
    tool = pyrapid.rapid_tooldata(
        [True, [[0, 0, 100], [1, 0, 0, 0]], [1, [0, 0, 50], [1, 0, 0, 0], 0, 0, 0]]
    )
    wobj = pyrapid.rapid_wobjdata(
        [False, True, "", [[300, 0, 100], [1, 0, 0, 0]], [[0, 0, 0], [1, 0, 0, 0]]]
    )
    move_j([100, 0, 200], [0, 0, 0, 0], tool=tool, wobj=wobj)
    # TCP at [400, 0, 300] in the base frame, tool z pointing down: flange 100 mm higher
    flange = controller.robot.fk(controller.current())
    assert np.allclose(flange.translation, [0.4, 0, 0.4], atol=1e-6)
    result = pyrapid.rapid_robtarget()
    motion.CRobT(result, tool, wobj)
    assert [result.GetElem("trans").GetElem(c).Get() for c in "xyz"] == pytest.approx([100, 0, 200])


def test_offs_reltool() -> None:
    point = robtarget([400, 0, 300], DOWN, [0, 0, 0, 0])
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
    point = robtarget([400, 0, 400], DOWN, [0, 0, 0, 0])
    joints = pyrapid.rapid_jointtarget()
    motion.CalcJointT(joints, point, TOOL0, WOBJ0)
    back = pyrapid.rapid_robtarget()
    motion.CalcRobT(back, joints, TOOL0, WOBJ0)
    assert [back.GetElem("trans").GetElem(c).Get() for c in "xyz"] == pytest.approx([400, 0, 400])
    conf = [back.GetElem("robconf").GetElem(c).Get() for c in ("cf1", "cf4", "cf6", "cfx")]
    assert conf == [0, 0, 0, 0]


def test_palletizer(monkeypatch: pytest.MonkeyPatch) -> None:
    """the 4 axis robot: axes 1, 2, 3 and 6, the flange stays horizontal"""
    monkeypatch.delenv("PYRAPID_VIEWER", raising=False)
    monkeypatch.delenv("PYRAPID_REALTIME", raising=False)
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    motion.UseRobot("irb460_approx")
    controller: Any = motion.CONTROLLER
    move_j([1500, 0, 800], [0, 0, 0, 0], v=2000)
    move_l([1500, 0, 300], [0, 0, 0, 0], v=1000)
    flange = controller.robot.fk(controller.current())
    assert np.allclose(flange.translation, [1.5, 0, 0.3], atol=1e-5)
    joints = pyrapid.rapid_jointtarget()
    motion.CJointT(joints)
    robax = [joints.GetElem("robax").GetElem("rax_%d" % i).Get() for i in range(1, 7)]
    assert robax[3] == robax[4] == 0
    check_limits(controller.robot, controller.completed[-1])


def test_no_robot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    with pytest.raises(motion.MotionError, match="!robot:"):
        move_abs_j([0, 0, 0, 0, 0, 0])


def test_viewer(monkeypatch: pytest.MonkeyPatch) -> None:
    """PYRAPID_VIEWER=meshcat: the robot and the path of the TCP in the browser, in
    real time"""
    pytest.importorskip("meshcat")
    monkeypatch.setenv("PYRAPID_VIEWER", "meshcat")
    monkeypatch.setenv("PYRAPID_VIEWER_HOLD", "0")
    monkeypatch.setattr(motion, "CONTROLLER", motion.Controller())
    motion.UseRobot("irb120_3_58")
    controller: Any = motion.CONTROLLER
    assert controller.realtime
    viewer = controller.viewer
    assert viewer is not None and viewer.robot.visual_model.ngeoms > 0
    move_abs_j([30, 0, 0, 0, 30, 0], conc=True)
    # real time: the robot is moving while the program runs
    assert not np.allclose(np.degrees(controller.current()), [30, 0, 0, 0, 30, 0])
    motion.WaitRob()
    assert np.allclose(np.degrees(controller.current()), [30, 0, 0, 0, 30, 0])
    assert len(viewer.trace) > 5
    assert np.allclose(viewer.trace[-1], tcp(), atol=0.01)


def test_orient_zyx() -> None:
    """OrientZYX(z, y, x): around z, then the new y, then the new x"""
    result = pyrapid.rapid_orient()
    motion.OrientZYX(result, 90, 0, 0)
    q = [result.GetElem(c).Get() for c in ("q1", "q2", "q3", "q4")]
    assert q == pytest.approx([math.sqrt(0.5), 0, 0, math.sqrt(0.5)])
    # the tool pointing down: 180 degrees around y
    motion.OrientZYX(result, 0, 180, 0)
    q = [result.GetElem(c).Get() for c in ("q1", "q2", "q3", "q4")]
    assert q == pytest.approx([0, 0, 1, 0], abs=1e-9)
