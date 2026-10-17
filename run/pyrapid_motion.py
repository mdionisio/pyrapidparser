"""Motion of the robot for the programs translated by rapid2py.

The comment "!robot: <model>" in a module selects the robot model (robotmodel.py);
rapid2py translates it into a call of UseRobot. The motion instructions of
default/standard.sys (MoveAbsJ, MoveJ, MoveL, MoveC, CJointT, CRobT, ...) call the
functions of this module with the RAPID data objects.

The motion is simulated: every instruction computes the trajectory of the axes,
sampled every SAMPLE_TIME seconds, with a trapezoidal speed profile limited by
the speed data of the instruction and by the velocity and acceleration of the
axes. The zones are run as fine points (the robot stops at every point).

Environment variables:

    PYRAPID_MOTION_LOG=1      print one line for each motion instruction
    PYRAPID_VIEWER=meshcat    show the robot in the browser (MeshCat), in real time
    PYRAPID_VIEWER_HOLD=0     do not wait for Ctrl+C at the end of the program
"""

import atexit
import math
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import numpy as np
import pinocchio as pin

import robotmodel

# trajectory sampling (s)
SAMPLE_TIME = 0.01
# acceleration time of the cartesian (linear and circular) movements (s)
CARTESIAN_RAMP = 0.2
# frames per second of the viewer
VIEWER_RATE = 30.0
# largest change of an axis between two points of a cartesian path (rad): more means
# that the path crosses a singularity
MAX_PATH_STEP = 0.2
# RAPID value of the external axes that are not used
NO_EXTERNAL_AXIS = 9e9


class MotionError(Exception):
    """the robot cannot execute the movement: the program stops"""


# ------------------------------------------------------------------ RAPID data


def num(value: Any) -> float:
    return float(value.Get())


def component(record: Any, *path: str) -> Any:
    for name in path:
        record = record.GetElem(name)
    return record


def pose_of(record: Any) -> Any:
    """pin.SE3 of a RAPID pose (trans in mm, rot quaternion q1..q4 = w, x, y, z)"""
    trans = component(record, "trans")
    rot = component(record, "rot")
    position = np.array([num(trans.GetElem(c)) for c in ("x", "y", "z")]) / 1000.0
    w, x, y, z = (num(rot.GetElem(c)) for c in ("q1", "q2", "q3", "q4"))
    quaternion = pin.Quaternion(w, x, y, z)
    if quaternion.norm() < 1e-9:
        raise MotionError("orientation [%g, %g, %g, %g] is not a quaternion" % (w, x, y, z))
    quaternion.normalize()
    return pin.SE3(quaternion.matrix(), position)


def pose_values(placement: Any) -> list[list[float]]:
    """[[x, y, z], [q1, q2, q3, q4]] of a pin.SE3 in RAPID units (q1 >= 0)"""
    quaternion = pin.Quaternion(placement.rotation)
    x, y, z, w = (float(c) for c in quaternion.coeffs())
    if w < 0:
        w, x, y, z = -w, -x, -y, -z
    position = [round(float(c) * 1000.0, 6) for c in placement.translation]
    return [position, [round(c, 9) for c in (w, x, y, z)]]


def confdata_of(robtarget: Any) -> tuple[int, int, int, int]:
    conf = component(robtarget, "robconf")
    cf1, cf4, cf6, cfx = (int(round(num(conf.GetElem(c)))) for c in ("cf1", "cf4", "cf6", "cfx"))
    return (cf1, cf4, cf6, cfx)


@dataclass
class Tool:
    frame: Any  # pin.SE3 of the TCP in the flange frame
    mass: float
    cog: Any  # m, flange frame
    inertia: Any

    @classmethod
    def of(cls, tooldata: Any) -> "Tool":
        if not bool(component(tooldata, "robhold").Get()):
            raise MotionError("stationary tools (robhold FALSE) are not supported")
        load = component(tooldata, "tload")
        cog = component(load, "cog")
        return cls(
            pose_of(component(tooldata, "tframe")),
            num(load.GetElem("mass")),
            np.array([num(cog.GetElem(c)) for c in ("x", "y", "z")]) / 1000.0,
            np.array([num(load.GetElem(c)) for c in ("ix", "iy", "iz")]),
        )


def wobj_of(wobjdata: Any) -> Any:
    """placement of the object frame in the base frame"""
    if wobjdata is None:
        return pin.SE3.Identity()
    if bool(component(wobjdata, "robhold").Get()):
        raise MotionError("work objects held by the robot (robhold TRUE) are not supported")
    return pose_of(component(wobjdata, "uframe")) * pose_of(component(wobjdata, "oframe"))


@dataclass
class Speed:
    tcp: float  # m/s
    orientation: float  # rad/s
    time: Optional[float] = None  # \T: total time of the movement (s)

    @classmethod
    def of(cls, speeddata: Any, v: float = -1, t: float = -1) -> "Speed":
        tcp = v if v >= 0 else num(speeddata.GetElem("v_tcp"))
        if tcp <= 0 and t <= 0:
            raise MotionError("the TCP speed must be positive")
        return cls(
            tcp / 1000.0,
            math.radians(num(speeddata.GetElem("v_ori"))),
            t if t > 0 else None,
        )


# ------------------------------------------------------------------ trajectories


def trapezoid(total: float, ramp: float) -> Callable[[float], tuple[float, float, float]]:
    """normalized trapezoidal profile from 0 to 1 in total seconds, accelerating for
    ramp seconds: t -> (s, ds/dt, d2s/dt2)"""
    ramp = min(ramp, total / 2)
    if total <= 0:
        return lambda t: (1.0, 0.0, 0.0)
    if ramp <= 0:
        return lambda t: (min(max(t / total, 0.0), 1.0), 1.0 / total, 0.0)
    v = 1.0 / (total - ramp)
    a = v / ramp

    def profile(t: float) -> tuple[float, float, float]:
        if t <= 0:
            return (0.0, 0.0, 0.0)
        if t < ramp:
            return (0.5 * a * t * t, a * t, a)
        if t <= total - ramp:
            return (0.5 * a * ramp * ramp + v * (t - ramp), v, 0.0)
        if t < total:
            r = total - t
            return (1.0 - 0.5 * a * r * r, a * r, -a)
        return (1.0, 0.0, 0.0)

    return profile


def joint_timing(
    delta: Any, velocity: Any, acceleration: Any, minimum: float
) -> tuple[float, float]:
    """(total time, ramp time) of a synchronized joint movement: all the axes start and
    stop together, none exceeds its velocity and acceleration"""
    delta = np.abs(delta)
    if float(np.max(delta, initial=0.0)) < 1e-12:
        return (max(minimum, 0.0), 0.0)
    # minimum time of each axis alone with a trapezoidal profile
    times = np.where(
        delta <= velocity**2 / acceleration,
        2 * np.sqrt(delta / acceleration),
        delta / velocity + velocity / acceleration,
    )
    total = max(minimum, float(np.max(times)))
    for _ in range(1000):
        # ramp time so that every axis is within its acceleration
        disc = np.maximum(total * total - 4 * delta / acceleration, 0.0)
        ramp = float(np.max((total - np.sqrt(disc)) / 2))
        ramp = min(ramp, total / 2)
        if np.all(delta / (total - ramp) <= velocity * (1 + 1e-9)):
            return (total, ramp)
        total *= 1.01
    return (total, total / 2)  # pragma: no cover


@dataclass
class Sample:
    time: float
    axes: Any
    velocity: Any
    acceleration: Any


@dataclass
class Trajectory:
    instruction: str
    samples: list[Sample]

    @property
    def duration(self) -> float:
        return self.samples[-1].time if self.samples else 0.0


def sample_times(total: float) -> list[float]:
    count = max(1, int(math.ceil(total / SAMPLE_TIME - 1e-9)))
    return [total * k / count for k in range(count + 1)]


def joint_trajectory(
    instruction: str, start: Any, end: Any, total: float, ramp: float
) -> Trajectory:
    profile = trapezoid(total, ramp)
    delta = end - start
    samples = []
    for t in sample_times(total):
        s, ds, dds = profile(t)
        samples.append(Sample(t, start + s * delta, ds * delta, dds * delta))
    samples[-1].axes = end.copy()
    return Trajectory(instruction, samples)


def path_trajectory(
    instruction: str, path_axes: list[Any], total: float, ramp: float
) -> Trajectory:
    """time law on a path of axis positions sampled at equal steps of the path parameter"""
    profile = trapezoid(total, ramp)
    points = np.array(path_axes)
    steps = len(points) - 1
    derivative = np.gradient(points, 1.0 / steps, axis=0) if steps > 1 else points * 0
    samples = []
    for t in sample_times(total):
        s, ds, dds = profile(t)
        x = s * steps
        i = min(int(x), steps - 1)
        f = x - i
        axes = points[i] * (1 - f) + points[i + 1] * f
        slope = derivative[i] * (1 - f) + derivative[i + 1] * f
        samples.append(Sample(t, axes, slope * ds, slope * dds))
    samples[-1].axes = points[-1].copy()
    # second derivative of the path: finite differences of the velocity
    for k in range(1, len(samples) - 1):
        dt = samples[k + 1].time - samples[k - 1].time
        samples[k].acceleration = (samples[k + 1].velocity - samples[k - 1].velocity) / dt
    return Trajectory(instruction, samples)


# ------------------------------------------------------------------ controller


class Viewer:
    """the robot in the browser (MeshCat), in real time"""

    def __init__(self, robot: robotmodel.RobotModel) -> None:
        from pinocchio.visualize import MeshcatVisualizer

        self.robot = robot
        self.visualizer = MeshcatVisualizer(robot.model, robot.collision_model, robot.visual_model)
        # MeshCat prints the URL of the viewer
        self.visualizer.initViewer(open=False)
        self.visualizer.loadViewerModel()
        self.start_wall: Optional[float] = None
        self.start_sim = 0.0
        self.next_frame = 0.0
        # path of the TCP
        self.trace: list[Any] = []

    def show(self, axes: Any) -> None:
        self.visualizer.display(self.robot.configuration(axes))

    def show_trace(self) -> None:
        import meshcat.geometry as geometry

        if len(self.trace) < 2:
            return
        points = np.array(self.trace).T
        self.visualizer.viewer["pyrapid/trace"].set_object(
            geometry.Line(
                geometry.PointsGeometry(points), geometry.LineBasicMaterial(color=0xFF8800)
            )
        )

    def play(self, trajectory: Trajectory, start: float, tcp: Callable[[Any], Any]) -> None:
        """display the samples at the time of the simulation, tcp(axes) is the position
        of the TCP"""
        if self.start_wall is None:
            self.start_wall = time.monotonic()
            self.start_sim = start
        for sample in trajectory.samples:
            sim = start + sample.time
            if sim < self.next_frame and sample is not trajectory.samples[-1]:
                continue
            delay = (sim - self.start_sim) - (time.monotonic() - self.start_wall)
            if delay > 0:
                time.sleep(delay)
            self.show(sample.axes)
            self.trace.append(tcp(sample.axes))
            self.show_trace()
            self.next_frame = sim + 1.0 / VIEWER_RATE

    def wait(self, duration: float, start: float) -> None:
        """keep the real time during WaitTime"""
        if self.start_wall is None:
            return
        delay = (start + duration - self.start_sim) - (time.monotonic() - self.start_wall)
        if delay > 0:
            time.sleep(delay)


class Controller:
    """the robot of the task: model, position of the axes, time of the simulation"""

    def __init__(self) -> None:
        self.robot: Optional[robotmodel.RobotModel] = None
        self.axes: Any = None
        self.time = 0.0
        self.conf_j = True
        self.conf_l = True
        self.log = os.environ.get("PYRAPID_MOTION_LOG", "") not in ("", "0")
        self.viewer: Optional[Viewer] = None
        self.payload: Optional[tuple[float, ...]] = None
        self.tool = Tool(pin.SE3.Identity(), 0.0, np.zeros(3), np.zeros(3))
        self.max_torque: Any = None

    def use_robot(self, name: str) -> None:
        if self.robot is not None and self.robot.name.lower() == name.lower():
            return
        viewer = os.environ.get("PYRAPID_VIEWER", "").lower()
        self.robot = robotmodel.load(name, geometry=viewer == "meshcat")
        self.axes = self.robot.home.copy()
        self.time = 0.0
        self.max_torque = np.zeros(self.robot.naxes)
        if viewer == "meshcat":
            self.viewer = Viewer(self.robot)
            self.viewer.show(self.axes)
            if os.environ.get("PYRAPID_VIEWER_HOLD", "1") not in ("", "0"):
                atexit.register(hold_viewer)
        elif viewer:
            raise MotionError("unknown viewer %s (PYRAPID_VIEWER=meshcat)" % (viewer,))

    def require_robot(self) -> robotmodel.RobotModel:
        if self.robot is None:
            raise MotionError("no robot model: add the comment !robot: <model> to a module")
        return self.robot

    # positions

    def set_tool(self, tool: Tool) -> None:
        robot = self.require_robot()
        self.tool = tool
        payload = (tool.mass, *tool.cog, *tool.inertia)
        if payload != self.payload and robot.has_dynamics:
            robot.set_payload(tool.mass, tool.cog, tool.inertia)
        self.payload = payload

    def tcp(self, axes: Any, tool: Tool) -> Any:
        """TCP placement in the base frame"""
        return self.require_robot().fk(axes) * tool.frame

    def solve(
        self,
        target: Any,
        tool: Tool,
        conf: Optional[tuple[int, int, int, int]],
        reference: Any,
    ) -> Any:
        """axis positions placing the TCP at target (base frame): with the configuration
        conf when given, otherwise the nearest to reference"""
        robot = self.require_robot()
        solutions = robot.ik(target * tool.frame.inverse(), reference)
        if not solutions:
            raise MotionError("position outside reach: %s" % (pose_values(target),))
        if conf is not None:
            matching = [s for s in solutions if robot.matches(s.axes, conf)]
            if not matching:
                found = sorted({robot.confdata(s.axes) for s in solutions})
                raise MotionError(
                    "no solution with the configuration %s (possible: %s)" % (list(conf), found)
                )
            solutions = matching
        return solutions[0].axes

    # movements

    def joint_move(self, instruction: str, end: Any, speed: Speed, tool: Tool) -> None:
        robot = self.require_robot()
        if not robot.within_limits(end):
            raise MotionError("%s: joint position outside the limits of the axes" % (instruction,))
        start = self.axes
        begin, finish = self.tcp(start, tool), self.tcp(end, tool)
        distance = float(np.linalg.norm(finish.translation - begin.translation))
        angle = float(np.linalg.norm(pin.log3(begin.rotation.T @ finish.rotation)))
        minimum = speed.time or max(distance / speed.tcp, angle / speed.orientation)
        total, ramp = joint_timing(end - start, robot.velocity, robot.acceleration, minimum)
        self.execute(joint_trajectory(instruction, start, end, total, ramp))

    def path_move(
        self,
        instruction: str,
        path: Callable[[float], Any],
        length: float,
        angle: float,
        speed: Speed,
        tool: Tool,
        conf: Optional[tuple[int, int, int, int]],
    ) -> None:
        """linear or circular movement of the TCP: path(s) is the TCP placement in the
        base frame for s from 0 to 1"""
        robot = self.require_robot()
        count = max(20, int(math.ceil(max(length / 0.002, angle / 0.01))))
        path_axes = [self.axes.copy()]
        for k in range(1, count + 1):
            target = path(k / count)
            solutions = robot.ik(target * tool.frame.inverse(), path_axes[-1])
            if not solutions:
                raise MotionError(
                    "%s: position outside reach on the path: %s"
                    % (instruction, pose_values(target))
                )
            axes = solutions[0].axes
            if float(np.max(np.abs(axes - path_axes[-1]))) > MAX_PATH_STEP:
                raise MotionError(
                    "%s: the path crosses a singularity near %s"
                    % (instruction, pose_values(target))
                )
            path_axes.append(axes)
        if conf is not None and self.conf_l and not robot.matches(path_axes[-1], conf):
            raise MotionError(
                "%s: the end point is reached with the configuration %s, programmed %s "
                "(use ConfL \\Off)" % (instruction, list(robot.confdata(path_axes[-1])), list(conf))
            )
        total = speed.time or max(length / speed.tcp, angle / speed.orientation)
        ramp = min(CARTESIAN_RAMP, total)
        total += ramp
        # slow down when an axis would exceed its velocity or acceleration
        for _ in range(20):
            trajectory = path_trajectory(instruction, path_axes, total, ramp)
            ratio = max(
                max(float(np.max(np.abs(s.velocity) / robot.velocity)) for s in trajectory.samples),
                math.sqrt(
                    max(
                        float(np.max(np.abs(s.acceleration) / robot.acceleration))
                        for s in trajectory.samples
                    )
                ),
            )
            if ratio <= 1.0 + 1e-6:
                break
            total *= ratio * 1.01
            ramp *= ratio * 1.01
        self.execute(trajectory)

    def execute(self, trajectory: Trajectory) -> None:
        robot = self.require_robot()
        torque = np.zeros(robot.naxes)
        if robot.has_dynamics:
            for sample in trajectory.samples:
                tau = robot.torques(sample.axes, sample.velocity, sample.acceleration)
                torque = np.maximum(torque, np.abs(tau))
            self.max_torque = np.maximum(self.max_torque, torque)
            if robot.effort is not None and np.any(torque > robot.effort):
                print(
                    "warning: %s: torque above the limit of the axes %s"
                    % (
                        trajectory.instruction,
                        [robot.rapid_axes[i] for i in np.flatnonzero(torque > robot.effort)],
                    ),
                    file=sys.stderr,
                )
        if self.viewer is not None:
            tool = self.tool
            self.viewer.play(
                trajectory, self.time, lambda axes: self.tcp(axes, tool).translation.copy()
            )
        self.axes = trajectory.samples[-1].axes.copy()
        self.time += trajectory.duration
        if self.log:
            line = "%-8s %6.2f s  axes [%s] deg" % (
                trajectory.instruction,
                trajectory.duration,
                ", ".join(number(math.degrees(a)) for a in self.axes),
            )
            if robot.has_dynamics:
                line += "  max torque [%s] Nm" % (", ".join(number(t) for t in torque),)
            print(line)

    def wait(self, duration: float) -> None:
        if self.viewer is not None:
            self.viewer.wait(duration, self.time)
        self.time += duration


CONTROLLER = Controller()


def number(value: float) -> str:
    text = "%.1f" % (value,)
    return "0.0" if text == "-0.0" else text


def hold_viewer() -> None:
    print("viewer: the program is finished, Ctrl+C to exit", file=sys.stderr)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


# ------------------------------------------------------------------ RAPID interface


def UseRobot(name: str) -> None:
    """the robot model of the task (comment !robot: <model>)"""
    CONTROLLER.use_robot(name)


def axes_of(jointtarget: Any) -> Any:
    robot = CONTROLLER.require_robot()
    robax = component(jointtarget, "robax")
    return np.radians([num(robax.GetElem("rax_%d" % a)) for a in robot.rapid_axes])


def jointtarget_values(axes: Any) -> list[list[float]]:
    robot = CONTROLLER.require_robot()
    robax = [0.0] * 6
    for i, axis in enumerate(robot.rapid_axes):
        robax[axis - 1] = round(math.degrees(float(axes[i])), 9)
    return [robax, [NO_EXTERNAL_AXIS] * 6]


def robtarget_values(axes: Any, tool: Tool, wobj: Any) -> list[Any]:
    robot = CONTROLLER.require_robot()
    placement = wobj.inverse() * CONTROLLER.tcp(axes, tool)
    return [*pose_values(placement), list(robot.confdata(axes)), [NO_EXTERNAL_AXIS] * 6]


def MoveAbsJ(jointtarget: Any, speeddata: Any, v: float, t: float, tooldata: Any) -> None:
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    CONTROLLER.joint_move("MoveAbsJ", axes_of(jointtarget), Speed.of(speeddata, v, t), tool)


def MoveJ(robtarget: Any, speeddata: Any, v: float, t: float, tooldata: Any, wobjdata: Any) -> None:
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    target = wobj_of(wobjdata) * pose_of(robtarget)
    conf = confdata_of(robtarget) if CONTROLLER.conf_j else None
    end = CONTROLLER.solve(target, tool, conf, CONTROLLER.axes)
    CONTROLLER.joint_move("MoveJ", end, Speed.of(speeddata, v, t), tool)


def MoveL(robtarget: Any, speeddata: Any, v: float, t: float, tooldata: Any, wobjdata: Any) -> None:
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    start = CONTROLLER.tcp(CONTROLLER.axes, tool)
    end = wobj_of(wobjdata) * pose_of(robtarget)
    rotation = pin.log3(start.rotation.T @ end.rotation)

    def path(s: float) -> Any:
        return pin.SE3(
            start.rotation @ pin.exp3(s * rotation),
            start.translation + s * (end.translation - start.translation),
        )

    CONTROLLER.path_move(
        "MoveL",
        path,
        float(np.linalg.norm(end.translation - start.translation)),
        float(np.linalg.norm(rotation)),
        Speed.of(speeddata, v, t),
        tool,
        confdata_of(robtarget),
    )


def MoveC(
    cirpoint: Any,
    robtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    tooldata: Any,
    wobjdata: Any,
) -> None:
    """circular movement from the current position through cirpoint to robtarget; the
    orientation goes from the start to the end orientation"""
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    wobj = wobj_of(wobjdata)
    start = CONTROLLER.tcp(CONTROLLER.axes, tool)
    middle = (wobj * pose_of(cirpoint)).translation
    end = wobj * pose_of(robtarget)
    p0, p1, p2 = start.translation, middle, end.translation
    a, b = p1 - p0, p2 - p0
    normal = np.cross(a, b)
    if float(np.linalg.norm(normal)) < 1e-9:
        raise MotionError("MoveC: the three points are on a line")
    # center of the circle through p0, p1, p2
    center = p0 + (np.cross(normal, a) * float(b @ b) + np.cross(b, normal) * float(a @ a)) / (
        2 * float(normal @ normal)
    )
    radius = float(np.linalg.norm(p0 - center))
    axis = normal / np.linalg.norm(normal)
    u = (p0 - center) / radius
    w = np.cross(axis, u)

    def angle_of(p: Any) -> float:
        d = p - center
        return math.atan2(float(d @ w), float(d @ u)) % (2 * math.pi)

    # the normal makes p0, p1, p2 counterclockwise: p1 is between p0 and p2
    sweep = angle_of(p2)
    rotation = pin.log3(start.rotation.T @ end.rotation)

    def path(s: float) -> Any:
        phi = s * sweep
        position = center + radius * (math.cos(phi) * u + math.sin(phi) * w)
        return pin.SE3(start.rotation @ pin.exp3(s * rotation), position)

    CONTROLLER.path_move(
        "MoveC",
        path,
        radius * sweep,
        float(np.linalg.norm(rotation)),
        Speed.of(speeddata, v, t),
        tool,
        confdata_of(robtarget),
    )


def ConfJ(on: bool) -> None:
    CONTROLLER.conf_j = on


def ConfL(on: bool) -> None:
    CONTROLLER.conf_l = on


def WaitTime(duration: float) -> None:
    """the time of the simulation advances; with the viewer the wait is real"""
    CONTROLLER.wait(duration)


def CJointT(result: Any) -> None:
    CONTROLLER.require_robot()
    result.Set(jointtarget_values(CONTROLLER.axes))


def CRobT(result: Any, tooldata: Any, wobjdata: Any) -> None:
    CONTROLLER.require_robot()
    result.Set(robtarget_values(CONTROLLER.axes, Tool.of(tooldata), wobj_of(wobjdata)))


def CalcJointT(result: Any, robtarget: Any, tooldata: Any, wobjdata: Any) -> None:
    target = wobj_of(wobjdata) * pose_of(robtarget)
    CONTROLLER.require_robot()
    axes = CONTROLLER.solve(target, Tool.of(tooldata), confdata_of(robtarget), CONTROLLER.axes)
    result.Set(jointtarget_values(axes))


def CalcRobT(result: Any, jointtarget: Any, tooldata: Any, wobjdata: Any) -> None:
    result.Set(robtarget_values(axes_of(jointtarget), Tool.of(tooldata), wobj_of(wobjdata)))


def Offs(result: Any, point: Any, dx: float, dy: float, dz: float) -> None:
    """the point displaced in the work object frame (mm)"""
    result.Set(point)
    trans = component(result, "trans")
    for name, d in (("x", dx), ("y", dy), ("z", dz)):
        trans.GetElem(name).Set(num(trans.GetElem(name)) + d)


def RelTool(
    result: Any, point: Any, dx: float, dy: float, dz: float, rx: float, ry: float, rz: float
) -> None:
    """the point displaced (mm) and rotated (degrees: around x, then the new y, then the
    new z) in the tool frame"""
    result.Set(point)
    displacement = pin.SE3(
        pin.utils.rotate("x", math.radians(rx))
        @ pin.utils.rotate("y", math.radians(ry))
        @ pin.utils.rotate("z", math.radians(rz)),
        np.array([dx, dy, dz]) / 1000.0,
    )
    placement = pose_of(point) * displacement
    position, rotation = pose_values(placement)
    trans, rot = component(result, "trans"), component(result, "rot")
    for name, value in zip(("x", "y", "z"), position):
        trans.GetElem(name).Set(value)
    for name, value in zip(("q1", "q2", "q3", "q4"), rotation):
        rot.GetElem(name).Set(value)
