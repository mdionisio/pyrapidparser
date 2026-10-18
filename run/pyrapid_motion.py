"""Motion of the robot for the programs translated by rapid2py.

The comment "!robot: <model>" in a module selects the robot model (run/robotmodel.py);
rapid2py translates it into a call of UseRobot. The motion instructions of
default/standard.sys (MoveAbsJ, MoveJ, MoveL, MoveC, CJointT, CRobT, ...) call the
functions of this module with the RAPID data objects.

As on the robot controller, the program and the robot run concurrently (RAPID
overview 2.3, "Synchronization with logical instructions"):

- a movement instruction plans the movement (inverse kinematics, reach,
  configuration, speed) in the program thread and queues it to the robot thread;
- the program continues when the robot reaches a stop point (zone fine), some time
  (PREFETCH_TIME) before the robot enters the zone of a fly-by point, or at once
  with \\Conc (at most MAX_CONC movements in the queue);
- the robot passes a fly-by point on a corner path when the next movement is
  queued before the robot enters the zone; otherwise the fly-by point becomes a
  stop point ("corner path failure"). The zone (pzone_tcp, or \\Z) is reduced to
  half the distance to the neighbor points; the corner path superposes the end of
  a movement and the start of the next in the axis space.

The robot thread samples the movement every SAMPLE_TIME seconds. Without the
viewer the time is simulated: the robot moves only while the program waits (the
logical instructions take no time), so the execution is fast and reproducible.
With the viewer, or PYRAPID_REALTIME=1, the robot moves in real time while the
program runs.

Each movement has a trapezoidal speed profile limited by the speed data of the
instruction and by the velocity and acceleration of the axes.

Environment variables:

    PYRAPID_MOTION_LOG=1      print one line at the end of each movement
    PYRAPID_REALTIME=1        run the robot in real time
    PYRAPID_VIEWER=meshcat    show the robot in the browser (MeshCat), in real time
    PYRAPID_VIEWER_HOLD=0     do not wait for Ctrl+C at the end of the program
"""

import atexit
import collections
import heapq
import importlib.util
import math
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np
import pinocchio as pin

from run import robotmodel

# trajectory sampling (s)
SAMPLE_TIME = 0.01
# acceleration time of the cartesian (linear and circular) movements (s)
CARTESIAN_RAMP = 0.2
# time to plan the next movement: the program continues this time before the robot
# enters the zone of a fly-by point (RAPID overview 2.3: "approximately 0.1 seconds")
PREFETCH_TIME = 0.1
# movement instructions with \Conc in succession (MoveL, argument \Conc)
MAX_CONC = 5
# frames per second of the viewer
VIEWER_RATE = 30.0
# points of the path of the TCP shown by the viewer
TRACE_POINTS = 1500
# largest change of an axis between two points of a cartesian path (rad): more means
# that the path crosses a singularity
MAX_PATH_STEP = 0.2
# RAPID value of the external axes that are not used
NO_EXTERNAL_AXIS = 9e9
# shortest TCP movement with a corner path (m)
MIN_ZONE_LENGTH = 1e-4


class MotionError(Exception):
    """the robot cannot execute the movement: the program stops"""


class OutsideReach(MotionError):
    """the position is outside the working area of the robot (ERR_OUTSIDE_REACH)"""


class JointLimit(MotionError):
    """the position is reachable but not with the programmed configuration or inside the
    limits of the axes (ERR_ROBLIMIT)"""


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
    """placement in the base frame of the frame of the programmed points: the object
    frame, displaced by the program displacement (PDispSet)"""
    if wobjdata is None:
        return pin.SE3.Identity()
    if bool(component(wobjdata, "robhold").Get()):
        raise MotionError("work objects held by the robot (robhold TRUE) are not supported")
    frame = pose_of(component(wobjdata, "uframe")) * pose_of(component(wobjdata, "oframe"))
    return frame * CONTROLLER.displacement


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


@dataclass
class Zone:
    radius: Optional[float]  # TCP zone (m), None for a stop point
    name: str

    @classmethod
    def of(cls, zonedata: Any, z: float = -1) -> "Zone":
        if bool(zonedata.GetElem("finep").Get()):
            return cls(None, "fine")
        radius = z if z >= 0 else num(zonedata.GetElem("pzone_tcp"))
        return cls(radius / 1000.0, "z%g" % (radius,))

    @classmethod
    def fine(cls) -> "Zone":
        return cls(None, "fine")


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


# ------------------------------------------------------------------ segments


@dataclass
class Trigger:
    """an output set during a movement (TriggIO, TriggEquip)"""

    distance: float  # m before the end (from the start with at_start); s with by_time
    at_start: bool
    by_time: bool
    lag: float  # s: the signal is set earlier (the equipment needs this time)
    delay: float  # s: the signal is set later (DODelay)
    signal: str
    value: Any
    time: float = 0.0  # time from the start of the movement when the signal is set
    fired: bool = False

    @classmethod
    def of(cls, record: Any) -> "Trigger":
        def field_of(name: str) -> Any:
            return component(record, name).Get()

        by_time = bool(field_of("bytime"))
        return cls(
            float(field_of("distance")) / (1.0 if by_time else 1000.0),
            bool(field_of("atstart")),
            by_time,
            float(field_of("lag")),
            float(field_of("delay")),
            str(field_of("signal")),
            field_of("value"),
        )

    def schedule(self, segment: "Segment") -> None:
        """the time of the segment when the signal is set"""
        if self.by_time:
            moment = segment.duration - self.distance
        elif self.at_start:
            moment = segment.time_at_remaining(max(segment.length - self.distance, 0.0))
        else:
            moment = segment.time_at_remaining(self.distance)
        self.time = min(max(moment - self.lag + self.delay, 0.0), segment.duration)


@dataclass
class Watch:
    """the search of a signal during a movement (SearchL)"""

    read: Callable[[], Any]  # the value of the signal
    edge: str  # "pos", "neg", "both"
    supervision: bool  # the signal at the start must not be active (pos and neg only)
    stop: str  # "", "stop", "pstop", "sstop": the movement stops at the first hit
    last: Any = None
    hits: list[Any] = field(default_factory=list)  # the axes at each hit
    error: str = ""  # "supervision": the signal was active at the start
    finished: bool = False  # the movement is stopping

    def poll(self, axes: Any) -> bool:
        """called at every step; True at the first hit that stops the movement"""
        if self.finished:
            return False
        value = self.read()
        if self.last is None:
            self.last = value
            active = value if self.edge == "pos" else not value
            if self.supervision and active:
                self.error = "supervision"
                return True
            return False
        changed = value != self.last
        rising = bool(value) and not bool(self.last)
        falling = bool(self.last) and not bool(value)
        self.last = value
        if not changed:
            return False
        if (
            self.edge == "both"
            or (self.edge == "pos" and rising)
            or (self.edge == "neg" and falling)
        ):
            self.hits.append(axes.copy())
            return bool(self.stop)
        return False


@dataclass
class Segment:
    """a planned movement: the axes from rest to rest, sampled in time"""

    instruction: str
    zone: Zone
    times: Any  # (n,)
    axes: Any  # (n, axes)
    velocity: Any
    acceleration: Any
    remaining: Any  # (n,) TCP path length to the end (m)
    # set by the robot thread
    start: Optional[float] = None  # time of the start
    blend: Optional[float] = None  # time (from the start) when the next movement starts
    done: bool = False
    corner_failure: bool = False
    torque: Any = None
    watch: Optional[Watch] = None
    triggers: list[Trigger] = field(default_factory=list)

    @classmethod
    def of(cls, trajectory: Trajectory, zone: Zone, tcp: Callable[[Any], Any]) -> "Segment":
        samples = trajectory.samples
        axes = np.array([s.axes for s in samples])
        points = np.array([tcp(a) for a in axes])
        steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
        remaining = np.concatenate([np.cumsum(steps[::-1])[::-1], [0.0]])
        return cls(
            trajectory.instruction,
            zone,
            np.array([s.time for s in samples]),
            axes,
            np.array([s.velocity for s in samples]),
            np.array([s.acceleration for s in samples]),
            remaining,
        )

    @property
    def duration(self) -> float:
        return float(self.times[-1])

    @property
    def length(self) -> float:
        return float(self.remaining[0])

    def at(self, t: float) -> tuple[Any, Any, Any]:
        """axes, velocity and acceleration t seconds after the start"""
        if t >= self.duration:
            zero = np.zeros(self.axes.shape[1])
            return self.axes[-1], zero, zero
        t = max(t, 0.0)
        i = min(int(np.searchsorted(self.times, t, side="right")) - 1, len(self.times) - 2)
        f = (t - self.times[i]) / (self.times[i + 1] - self.times[i])
        return (
            self.axes[i] * (1 - f) + self.axes[i + 1] * f,
            self.velocity[i] * (1 - f) + self.velocity[i + 1] * f,
            self.acceleration[i] * (1 - f) + self.acceleration[i + 1] * f,
        )

    def stop_at(self, t: float, deceleration: Any) -> None:
        """the movement stops from the time t: the axes decelerate to rest"""
        q, v, _ = self.at(t)
        stop = max(float(np.max(np.abs(v) / deceleration)), SAMPLE_TIME)
        count = max(1, int(math.ceil(stop / SAMPLE_TIME - 1e-9)))
        tau = np.linspace(0.0, stop, count + 1)[1:, None]
        keep = self.times <= t
        self.times = np.concatenate([self.times[keep], t + tau[:, 0]])
        self.axes = np.concatenate([self.axes[keep], q + v * tau - v * tau**2 / (2 * stop)])
        self.velocity = np.concatenate([self.velocity[keep], v * (1 - tau / stop)])
        self.acceleration = np.concatenate(
            [self.acceleration[keep], np.tile(-v / stop, (count, 1))]
        )
        self.remaining = np.concatenate([self.remaining[keep], np.zeros(count)])

    def time_at_remaining(self, distance: float) -> float:
        """time from the start when the TCP is distance from the end of the path"""
        index = int(np.argmax(self.remaining <= distance + 1e-12))
        return float(self.times[index])

    def zone_radius(self) -> Optional[float]:
        """the programmed zone, at most half the movement"""
        if self.zone.radius is None or self.length < MIN_ZONE_LENGTH:
            return None
        return min(self.zone.radius, self.length / 2)

    def release_time(self) -> float:
        """time from the start when the program continues after a fly-by point"""
        radius = self.zone_radius()
        if radius is None:
            return self.duration
        return max(0.0, self.time_at_remaining(radius) - PREFETCH_TIME)


# ------------------------------------------------------------------ viewer


class Viewer:
    """the robot in the browser (MeshCat)"""

    def __init__(self, robot: robotmodel.RobotModel) -> None:
        from pinocchio.visualize import MeshcatVisualizer

        self.robot = robot
        self.visualizer = MeshcatVisualizer(robot.model, robot.collision_model, robot.visual_model)
        # MeshCat prints the URL of the viewer
        self.visualizer.initViewer(open=False)
        self.visualizer.loadViewerModel()
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

    def update(self, now: float, axes: Any, tcp: Any, moving: bool) -> bool:
        """a frame every 1 / VIEWER_RATE seconds of the robot time"""
        if now < self.next_frame:
            return False
        self.next_frame = now + 1.0 / VIEWER_RATE
        self.show(axes)
        if moving:
            self.trace.append(tcp)
            del self.trace[:-TRACE_POINTS]
            self.show_trace()
        return True


# ------------------------------------------------------------------ simulation of the cell


class World:
    """what the simulation of the cell (PYRAPID_SIMULATION=file.py) sees of the robot
    controller. The simulation is a Python file with a function setup(world): it
    registers its actions and uses the viewer to draw. The actions run with the lock
    of the controller, the step and frame actions in the robot thread.

    - world.robot, world.time, world.axes(), world.flange(): the robot and its flange
      (pin.SE3 in the base frame, m);
    - world.viewer(): the MeshCat viewer (meshcat.Visualizer) or None;
    - world.signal(name), world.set_signal(name, value): the I/O signals of the
      program (the simulation sets the inputs, reads the outputs);
    - world.on_step(action), world.on_frame(action): action(world) after every
      sample of the robot, at every frame of the viewer;
    - world.on_signal(action): action(world, name, value) when a signal changes;
    - world.on_finish(action): action(world) at the end of the program;
    - world.after(delay, action): action() after delay seconds of the robot time.
    """

    def __init__(self, controller: "Controller") -> None:
        self.controller = controller
        self.io: Any = None
        self.step_actions: list[Callable[["World"], Any]] = []
        self.frame_actions: list[Callable[["World"], Any]] = []
        self.finish_actions: list[Callable[["World"], Any]] = []

    @property
    def robot(self) -> robotmodel.RobotModel:
        return self.controller.require_robot()

    @property
    def time(self) -> float:
        return float(self.controller.time)

    def axes(self) -> Any:
        return self.controller.axes.copy()

    def flange(self) -> Any:
        return self.robot.fk(self.controller.axes)

    def viewer(self) -> Any:
        viewer = self.controller.viewer
        return None if viewer is None else viewer.visualizer.viewer

    def require_io(self) -> Any:
        if self.io is None:
            raise MotionError("the program has no I/O signals (rapid2py --eio)")
        return self.io

    def signal(self, name: str) -> Any:
        return self.require_io().get(name)

    def set_signal(self, name: str, value: Any) -> None:
        with self.controller.condition:
            self.require_io().set(name, value)
            self.controller.condition.notify_all()

    def on_step(self, action: Callable[["World"], Any]) -> None:
        self.step_actions.append(action)

    def on_frame(self, action: Callable[["World"], Any]) -> None:
        self.frame_actions.append(action)

    def on_finish(self, action: Callable[["World"], Any]) -> None:
        self.finish_actions.append(action)

    def on_signal(self, action: Callable[["World", str, Any], Any]) -> None:
        def listener(name: str, value: Any) -> None:
            with self.controller.condition:
                action(self, name, value)

        self.require_io().listeners.append(listener)

    def after(self, delay: float, action: Callable[[], Any]) -> None:
        self.controller.after(delay, action)


def load_simulation(path: str, world: World) -> None:
    """the simulation of the cell: a Python file with setup(world), relative to the
    current folder or to the project folder"""
    if not os.path.exists(path):
        project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(project, path)
    spec = importlib.util.spec_from_file_location("pyrapid_simulation", path)
    if spec is None or spec.loader is None or not os.path.exists(path):
        raise MotionError("simulation %s not found" % (path,))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    setup = getattr(module, "setup", None)
    if setup is None:
        raise MotionError("simulation %s has no function setup(world)" % (path,))
    setup(world)


# ------------------------------------------------------------------ controller


class Controller:
    """the robot of the task: the program thread plans and queues the movements, the
    robot thread executes them"""

    def __init__(self) -> None:
        self.robot: Optional[robotmodel.RobotModel] = None
        self.condition = threading.Condition()
        self.time = 0.0
        self.axes: Any = None
        self.velocity: Any = None
        # end of the last planned movement: the start of the next one
        self.planned: Any = None
        self.queue: collections.deque[Segment] = collections.deque()
        self.active: list[Segment] = []
        self.completed: list[Segment] = []
        self.waiting: Optional[Callable[[], bool]] = None
        self.finished = False
        self.failed = False
        self.error: Optional[BaseException] = None
        self.thread: Optional[threading.Thread] = None
        self.realtime = False
        self.conf_j = True
        self.conf_l = True
        self.log = os.environ.get("PYRAPID_MOTION_LOG", "") not in ("", "0")
        self.viewer: Optional[Viewer] = None
        self.tool = Tool(pin.SE3.Identity(), 0.0, np.zeros(3), np.zeros(3))
        self.payload: Optional[tuple[float, ...]] = None
        # timed events: (time, sequence, action)
        self.events: list[tuple[float, int, Callable[[], Any]]] = []
        self.sequence = 0
        self.pending_triggers: list[Trigger] = []
        # AccSet: factor of the accelerations; VelSet: factor of the speeds, maximum TCP speed (m/s)
        self.acc_factor = 1.0
        # program displacement: placement in the object frame of the displaced points
        self.displacement = pin.SE3.Identity()
        self.vel_override = 1.0
        self.vel_max: Optional[float] = None
        self.world = World(self)

    def use_robot(self, name: str, io: Any = None) -> None:
        if self.robot is not None and self.robot.name.lower() == name.lower():
            return
        if self.robot is not None:
            raise MotionError("the task already moves the robot %s" % (self.robot.name,))
        viewer = os.environ.get("PYRAPID_VIEWER", "").lower()
        if viewer not in ("", "meshcat"):
            raise MotionError("unknown viewer %s (PYRAPID_VIEWER=meshcat)" % (viewer,))
        self.robot = robotmodel.load(name, geometry=viewer == "meshcat")
        self.axes = self.robot.home.copy()
        self.velocity = np.zeros(self.robot.naxes)
        self.planned = self.axes.copy()
        self.realtime = viewer == "meshcat" or os.environ.get("PYRAPID_REALTIME", "") not in (
            "",
            "0",
        )
        if viewer == "meshcat":
            self.viewer = Viewer(self.robot)
            self.viewer.show(self.axes)
        if io is not None:
            # the I/O instructions wait in the time of the robot
            self.world.io = io
            io.clock = self
        simulation = os.environ.get("PYRAPID_SIMULATION", "")
        if simulation:
            load_simulation(simulation, self.world)
        install_exit_hooks(viewer == "meshcat")
        self.thread = threading.Thread(target=self.run, name="robot", daemon=True)
        self.thread.start()

    def require_robot(self) -> robotmodel.RobotModel:
        if self.robot is None:
            raise MotionError("no robot model: add the comment !robot: <model> to a module")
        return self.robot

    # ---------------------------------------------------------- program thread

    def block(self, condition: Callable[[], bool]) -> None:
        """block the program until the condition is true (called with the lock)"""
        while True:
            if self.error is not None:
                raise MotionError("robot: %s" % (self.error,))
            if condition():
                break
            self.waiting = condition
            self.condition.notify_all()
            self.condition.wait()
        self.waiting = None

    def idle(self) -> bool:
        return not self.queue and not self.active

    def submit(self, segment: Segment, conc: bool) -> None:
        """queue a planned movement and wait as the zone requires"""
        for trigger in self.pending_triggers:
            trigger.schedule(segment)
        segment.triggers = self.pending_triggers
        self.pending_triggers = []
        with self.condition:
            if conc:
                self.block(lambda: len(self.queue) < MAX_CONC)
            self.queue.append(segment)
            self.planned = segment.axes[-1].copy()
            self.condition.notify_all()
            if conc:
                return
            if segment.zone.radius is None:
                self.block(lambda: segment.done)
            else:
                self.block(
                    lambda: (
                        segment.done
                        or (
                            segment.start is not None
                            and self.time >= segment.start + segment.release_time() - 1e-9
                        )
                    )
                )

    def wait_time(self, duration: float, inpos: bool) -> None:
        with self.condition:
            if inpos:
                self.block(self.idle)
            end = self.time + duration
            self.block(lambda: self.time >= end - 1e-9)

    def wait_robot(self) -> None:
        with self.condition:
            self.block(self.idle)

    def finish(self) -> None:
        """end of the program: the robot completes the queued movements"""
        if self.robot is None or self.failed:
            return
        with self.condition:
            self.finished = True
            self.block(self.idle)
            for action in self.world.finish_actions:
                action(self.world)

    # ---------------------------------------------------------- clock of the I/O
    # (pyrapid.IO.clock): the waits of the I/O instructions and the timed events
    # follow the time of the robot

    def now(self) -> float:
        return self.time

    def wait_until(self, condition: Callable[[], bool], max_time: Optional[float] = None) -> bool:
        """the program waits until condition() is true; False when max_time expires"""
        with self.condition:
            end = None if max_time is None else self.time + max_time
            self.block(lambda: condition() or (end is not None and self.time >= end - 1e-9))
            return bool(condition())

    def after(self, delay: float, action: Callable[[], Any]) -> None:
        """action() after delay seconds of the robot time (in the robot thread)"""
        with self.condition:
            self.sequence += 1
            heapq.heappush(self.events, (self.time + delay, self.sequence, action))
            self.condition.notify_all()

    def current(self) -> Any:
        with self.condition:
            if self.error is not None:
                raise MotionError("robot: %s" % (self.error,))
            return self.axes.copy()

    def start_axes(self) -> Any:
        """the start of the next movement: the end of the movements already planned"""
        with self.condition:
            return self.planned.copy()

    # ---------------------------------------------------------- robot thread

    def may_advance(self) -> bool:
        if self.realtime:
            return True
        # simulated time: the robot moves while the program waits
        return self.waiting is not None and not self.waiting()

    def run(self) -> None:
        start_wall = time.monotonic()
        try:
            while True:
                with self.condition:
                    while not self.may_advance():
                        self.condition.wait()
                    self.step()
                    self.condition.notify_all()
                    now = self.time
                if self.realtime:
                    delay = now - (time.monotonic() - start_wall)
                    if delay > 0:
                        time.sleep(delay)
        except BaseException as error:  # pragma: no cover
            with self.condition:
                self.error = error
                self.condition.notify_all()

    def step(self) -> None:
        """advance the robot of SAMPLE_TIME (called with the lock)"""
        robot = self.require_robot()
        now = self.time + SAMPLE_TIME
        if not self.active and self.queue:
            segment = self.queue.popleft()
            segment.start = self.time
            self.active.append(segment)
        if self.active:
            last = self.active[-1]
            assert last.start is not None
            radius = last.zone_radius()
            if radius is not None and last.blend is None and not last.corner_failure:
                if self.queue:
                    following = self.queue[0]
                    reduced = radius
                    if following.length >= MIN_ZONE_LENGTH:
                        reduced = min(radius, following.length / 2)
                        last.blend = max(last.time_at_remaining(reduced), self.time - last.start)
                    else:
                        # no corner path to a movement without TCP movement
                        last.corner_failure = True
                elif now >= last.start + last.time_at_remaining(radius):
                    # the next movement is not planned in time: stop point
                    last.corner_failure = True
                    if not self.finished:
                        print(
                            "warning: %s %s: corner path failure, the fly-by point is a "
                            "stop point" % (last.instruction, last.zone.name),
                            file=sys.stderr,
                        )
            if last.blend is not None and self.queue and now >= last.start + last.blend:
                segment = self.queue.popleft()
                segment.start = last.start + last.blend
                self.active.append(segment)
        # the axes: superposition of the active movements
        axes: Any = None
        velocity: Any = None
        acceleration: Any = None
        for segment in self.active:
            assert segment.start is not None
            q, v, a = segment.at(now - segment.start)
            if axes is None:
                axes, velocity, acceleration = q.copy(), v.copy(), a.copy()
            else:
                axes += q - segment.axes[0]
                velocity += v
                acceleration += a
        self.time = now
        while self.events and self.events[0][0] <= now + 1e-9:
            _, _, action = heapq.heappop(self.events)
            action()
        if axes is not None:
            self.axes, self.velocity = axes, velocity
            if robot.has_dynamics:
                torque = np.abs(robot.torques(axes, velocity, acceleration))
                for segment in self.active:
                    segment.torque = (
                        torque if segment.torque is None else np.maximum(segment.torque, torque)
                    )
        # the triggers at the end of a movement fire before it is removed
        self.fire_triggers(now)
        for segment in list(self.active):
            assert segment.start is not None
            if now >= segment.start + segment.duration - 1e-9:
                self.active.remove(segment)
                segment.done = True
                self.completed.append(segment)
                self.report(segment)
        if not self.active and not self.queue:
            self.velocity = np.zeros(robot.naxes)
        for step_action in self.world.step_actions:
            step_action(self.world)
        self.poll_watches(now)
        if self.viewer is not None and self.viewer.update(
            now,
            self.axes,
            self.tcp(self.axes, self.tool).translation.copy(),
            bool(self.active),
        ):
            for frame_action in self.world.frame_actions:
                frame_action(self.world)

    def fire_triggers(self, now: float) -> None:
        """set the outputs of the triggers of the active movements (called with the lock)"""
        for segment in self.active:
            assert segment.start is not None
            for trigger in segment.triggers:
                if not trigger.fired and now >= segment.start + trigger.time - 1e-9:
                    trigger.fired = True
                    self.world.require_io().set(trigger.signal, trigger.value)

    def poll_watches(self, now: float) -> None:
        """the searches of the active movements: stop the movement at a hit (called with
        the lock)"""
        for segment in self.active:
            watch = segment.watch
            if watch is None or self.axes is None:
                continue
            assert segment.start is not None
            if watch.poll(self.axes):
                # a hard stop is shorter than a stop on the path
                factor = 2.0 if watch.stop == "stop" else 1.0
                robot = self.require_robot()
                segment.stop_at(now - segment.start, self.accelerations() * factor)
                watch.finished = True

    def report(self, segment: Segment) -> None:
        robot = self.require_robot()
        torque = segment.torque
        if torque is not None and robot.effort is not None and np.any(torque > robot.effort):
            print(
                "warning: %s: torque above the limit of the axes %s"
                % (
                    segment.instruction,
                    [robot.rapid_axes[i] for i in np.flatnonzero(torque > robot.effort)],
                ),
                file=sys.stderr,
            )
        if self.log:
            assert segment.start is not None
            zone = segment.zone.name
            if segment.zone.radius is not None and (
                segment.corner_failure or segment.blend is None
            ):
                zone += " stop"
            line = "%7.2f s  %-8s %-9s axes [%s] deg" % (
                segment.start + segment.duration,
                segment.instruction,
                zone,
                ", ".join(number(math.degrees(a)) for a in segment.axes[-1]),
            )
            if torque is not None:
                line += "  max torque [%s] Nm" % (", ".join(number(t) for t in torque),)
            print(line, flush=True)

    # ---------------------------------------------------------- planning

    def set_tool(self, tool: Tool) -> None:
        robot = self.require_robot()
        with self.condition:
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
            raise OutsideReach("position outside reach: %s" % (pose_values(target),))
        if conf is not None:
            matching = [s for s in solutions if robot.matches(s.axes, conf)]
            if not matching:
                found = sorted({robot.confdata(s.axes) for s in solutions})
                raise JointLimit(
                    "no solution with the configuration %s (possible: %s)" % (list(conf), found)
                )
            solutions = matching
        return solutions[0].axes

    def accelerations(self) -> Any:
        """the accelerations of the axes with AccSet"""
        return self.require_robot().acceleration * self.acc_factor

    def scaled(self, speed: Speed) -> Speed:
        """the speed with VelSet: the override of the speeds and the maximum TCP speed"""
        tcp = speed.tcp * self.vel_override
        if self.vel_max is not None:
            tcp = min(tcp, self.vel_max)
        time = None if speed.time is None else speed.time / max(self.vel_override, 1e-6)
        return Speed(tcp, speed.orientation * self.vel_override, time)

    def joint_move(
        self, instruction: str, start: Any, end: Any, speed: Speed, zone: Zone, tool: Tool
    ) -> Segment:
        robot = self.require_robot()
        speed = self.scaled(speed)
        if not robot.within_limits(end):
            raise JointLimit("%s: joint position outside the limits of the axes" % (instruction,))
        begin, finish = self.tcp(start, tool), self.tcp(end, tool)
        distance = float(np.linalg.norm(finish.translation - begin.translation))
        angle = float(np.linalg.norm(pin.log3(begin.rotation.T @ finish.rotation)))
        minimum = speed.time or max(distance / speed.tcp, angle / speed.orientation)
        total, ramp = joint_timing(end - start, robot.velocity, self.accelerations(), minimum)
        trajectory = joint_trajectory(instruction, start, end, total, ramp)
        return Segment.of(trajectory, zone, lambda a: self.tcp(a, tool).translation.copy())

    def path_move(
        self,
        instruction: str,
        start: Any,
        path: Callable[[float], Any],
        length: float,
        angle: float,
        speed: Speed,
        zone: Zone,
        tool: Tool,
        conf: Optional[tuple[int, int, int, int]],
    ) -> Segment:
        """linear or circular movement of the TCP: path(s) is the TCP placement in the
        base frame for s from 0 to 1"""
        robot = self.require_robot()
        speed = self.scaled(speed)
        count = max(20, int(math.ceil(max(length / 0.002, angle / 0.01))))
        path_axes = [start.copy()]
        for k in range(1, count + 1):
            target = path(k / count)
            solutions = robot.ik(target * tool.frame.inverse(), path_axes[-1])
            if not solutions:
                raise OutsideReach(
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
                        float(np.max(np.abs(s.acceleration) / self.accelerations()))
                        for s in trajectory.samples
                    )
                ),
            )
            if ratio <= 1.0 + 1e-6:
                break
            total *= ratio * 1.01
            ramp *= ratio * 1.01
        return Segment.of(trajectory, zone, lambda a: self.tcp(a, tool).translation.copy())


CONTROLLER = Controller()


def number(value: float) -> str:
    text = "%.1f" % (value,)
    return "0.0" if text == "-0.0" else text


EXIT_HOOKS = False


def install_exit_hooks(viewer: bool) -> None:
    """at the end of the program the robot completes its movements (not after an
    error); with the viewer the program waits for Ctrl+C"""
    global EXIT_HOOKS
    if EXIT_HOOKS:
        return
    EXIT_HOOKS = True
    previous = sys.excepthook

    def excepthook(kind: Any, value: Any, traceback: Any) -> None:
        CONTROLLER.failed = True
        if issubclass(kind, KeyboardInterrupt):
            print("program interrupted", file=sys.stderr)
            return
        previous(kind, value, traceback)

    sys.excepthook = excepthook

    def at_exit() -> None:
        CONTROLLER.finish()
        if viewer and os.environ.get("PYRAPID_VIEWER_HOLD", "1") not in ("", "0"):
            hold_viewer()

    atexit.register(at_exit)


def hold_viewer() -> None:
    print("viewer: the program is finished, Ctrl+C to exit", file=sys.stderr)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


# ------------------------------------------------------------------ RAPID interface


def UseRobot(name: str, io: Any = None) -> None:
    """the robot model of the task (comment !robot: <model>); io is pyrapid.IO, the I/O
    signals of the program"""
    CONTROLLER.use_robot(name, io)


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


def MoveAbsJ(
    conc: bool,
    jointtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    zonedata: Any,
    z: float,
    tooldata: Any,
) -> None:
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    start = CONTROLLER.start_axes()
    segment = CONTROLLER.joint_move(
        "MoveAbsJ",
        start,
        axes_of(jointtarget),
        Speed.of(speeddata, v, t),
        Zone.of(zonedata, z),
        tool,
    )
    CONTROLLER.submit(segment, conc)


def MoveJ(
    conc: bool,
    robtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    zonedata: Any,
    z: float,
    tooldata: Any,
    wobjdata: Any,
) -> None:
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    start = CONTROLLER.start_axes()
    target = wobj_of(wobjdata) * pose_of(robtarget)
    conf = confdata_of(robtarget) if CONTROLLER.conf_j else None
    end = CONTROLLER.solve(target, tool, conf, start)
    segment = CONTROLLER.joint_move(
        "MoveJ", start, end, Speed.of(speeddata, v, t), Zone.of(zonedata, z), tool
    )
    CONTROLLER.submit(segment, conc)


def linear_segment(
    instruction: str,
    robtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    zone: Zone,
    tool: Tool,
    wobjdata: Any,
) -> Segment:
    """the planned linear movement of the TCP from the end of the movements already
    planned to the robtarget"""
    axes = CONTROLLER.start_axes()
    start = CONTROLLER.tcp(axes, tool)
    end = wobj_of(wobjdata) * pose_of(robtarget)
    rotation = pin.log3(start.rotation.T @ end.rotation)

    def path(s: float) -> Any:
        return pin.SE3(
            start.rotation @ pin.exp3(s * rotation),
            start.translation + s * (end.translation - start.translation),
        )

    return CONTROLLER.path_move(
        instruction,
        axes,
        path,
        float(np.linalg.norm(end.translation - start.translation)),
        float(np.linalg.norm(rotation)),
        Speed.of(speeddata, v, t),
        zone,
        tool,
        confdata_of(robtarget),
    )


def MoveL(
    conc: bool,
    robtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    zonedata: Any,
    z: float,
    tooldata: Any,
    wobjdata: Any,
) -> None:
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    zone = Zone.of(zonedata, z)
    segment = linear_segment("MoveL", robtarget, speeddata, v, t, zone, tool, wobjdata)
    CONTROLLER.submit(segment, conc)


SEARCH_OK = 0
SEARCH_NO_HIT = 1
SEARCH_SUPERVISION = 2


def SearchL(
    stop: str,
    sup: bool,
    signal: str,
    edge: str,
    supervision: bool,
    searchpoint: Any,
    robtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    tooldata: Any,
    wobjdata: Any,
) -> int:
    """linear movement to the robtarget that stores the position of the TCP (searchpoint)
    when the signal changes. stop: "", "stop", "pstop" or "sstop" (the movement stops at
    the hit); edge: "pos", "neg" or "both". Returns SEARCH_OK, SEARCH_NO_HIT (no change
    of the signal, or more than one with sup) or SEARCH_SUPERVISION (the signal was
    active at the start; the robot stops at once)."""
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    io = CONTROLLER.world.require_io()
    segment = linear_segment("SearchL", robtarget, speeddata, v, t, Zone.fine(), tool, wobjdata)
    watch = Watch(lambda: io.get(signal), edge, supervision, stop)
    segment.watch = watch
    CONTROLLER.submit(segment, False)
    if watch.error:
        return SEARCH_SUPERVISION
    if not watch.hits or (sup and len(watch.hits) > 1):
        return SEARCH_NO_HIT
    searchpoint.Set(robtarget_values(watch.hits[0], tool, wobj_of(wobjdata)))
    return SEARCH_OK


def MoveC(
    conc: bool,
    cirpoint: Any,
    robtarget: Any,
    speeddata: Any,
    v: float,
    t: float,
    zonedata: Any,
    z: float,
    tooldata: Any,
    wobjdata: Any,
) -> None:
    """circular movement from the current position through cirpoint to robtarget; the
    orientation goes from the start to the end orientation"""
    tool = Tool.of(tooldata)
    CONTROLLER.set_tool(tool)
    wobj = wobj_of(wobjdata)
    axes = CONTROLLER.start_axes()
    start = CONTROLLER.tcp(axes, tool)
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

    segment = CONTROLLER.path_move(
        "MoveC",
        axes,
        path,
        radius * sweep,
        float(np.linalg.norm(rotation)),
        Speed.of(speeddata, v, t),
        Zone.of(zonedata, z),
        tool,
        confdata_of(robtarget),
    )
    CONTROLLER.submit(segment, conc)


def Triggered(records: list[Any], movement: Callable[..., None], *arguments: Any) -> None:
    """a movement instruction with the triggers of the triggdata records (TriggL, ...)"""
    CONTROLLER.pending_triggers = [Trigger.of(r) for r in records]
    try:
        movement(*arguments)
    finally:
        CONTROLLER.pending_triggers = []


def PDispSet(dispframe: Any) -> None:
    """program displacement: the programmed points are displaced by the pose, in the
    object frame"""
    CONTROLLER.displacement = pose_of(dispframe)


def PDispOff() -> None:
    CONTROLLER.displacement = pin.SE3.Identity()


def PDispOn(rot: bool, exep: Any, progpoint: Any, tooldata: Any, wobjdata: Any) -> None:
    """the displacement (in the object frame) that moves the programmed point ProgPoint
    to ExeP, or to the current position; the orientation changes only with \\Rot. It
    replaces the previous displacement."""
    frame = wobj_of(wobjdata) * CONTROLLER.displacement.inverse()
    programmed = pose_of(progpoint)
    if exep is None:
        executed = frame.inverse() * CONTROLLER.tcp(CONTROLLER.current(), Tool.of(tooldata))
    else:
        executed = pose_of(exep)
    rotation = executed.rotation @ programmed.rotation.T if rot else np.eye(3)
    CONTROLLER.displacement = pin.SE3(
        rotation, executed.translation - rotation @ programmed.translation
    )


def ORobT(result: Any, point: Any) -> None:
    """the point without the program displacement"""
    result.Set(point)
    displaced = CONTROLLER.displacement.inverse() * pose_of(point)
    values = pose_values(displaced)
    trans = component(result, "trans")
    for name, v in zip(("x", "y", "z"), values[0]):
        trans.GetElem(name).Set(v)
    rot = component(result, "rot")
    for name, v in zip(("q1", "q2", "q3", "q4"), values[1]):
        rot.GetElem(name).Set(v)


def AccSet(acc: float, ramp: float) -> None:
    """acceleration in percent of the maximum (20 to 100); the ramp is not simulated"""
    if not 20 <= acc <= 100:
        raise MotionError("AccSet: the acceleration is 20 to 100 percent")
    CONTROLLER.acc_factor = acc / 100.0


def VelSet(override: float, maximum: float) -> None:
    """speeds in percent of the programmed ones (0 to 100) and maximum TCP speed (mm/s)"""
    if not 0 < override <= 100:
        raise MotionError("VelSet: the override is more than 0 and at most 100 percent")
    CONTROLLER.vel_override = override / 100.0
    CONTROLLER.vel_max = maximum / 1000.0 if maximum > 0 else None


def MoveWithOutput(signal: str, value: Any, movement: Callable[..., None], *arguments: Any) -> None:
    """MoveLDO, ...: the movement sets the output at its end (at the middle of the
    corner path for a fly-by point)"""
    CONTROLLER.pending_triggers = [Trigger(0.0, False, False, 0.0, 0.0, signal, value)]
    try:
        movement(*arguments)
    finally:
        CONTROLLER.pending_triggers = []


def ConfJ(on: bool) -> None:
    CONTROLLER.conf_j = on


def ConfL(on: bool) -> None:
    CONTROLLER.conf_l = on


def WaitTime(duration: float, inpos: bool = False) -> None:
    """the program waits, the robot continues its movements; \\InPos waits first for
    the robot to stop"""
    CONTROLLER.wait_time(duration, inpos)


def WaitRob() -> None:
    """wait until the robot has completed its movements (\\InPos, \\ZeroSpeed)"""
    CONTROLLER.wait_robot()


def CJointT(result: Any) -> None:
    CONTROLLER.require_robot()
    result.Set(jointtarget_values(CONTROLLER.current()))


def CRobT(result: Any, tooldata: Any, wobjdata: Any) -> None:
    CONTROLLER.require_robot()
    result.Set(robtarget_values(CONTROLLER.current(), Tool.of(tooldata), wobj_of(wobjdata)))


def CalcJointT(result: Any, robtarget: Any, tooldata: Any, wobjdata: Any) -> None:
    target = wobj_of(wobjdata) * pose_of(robtarget)
    CONTROLLER.require_robot()
    axes = CONTROLLER.solve(target, Tool.of(tooldata), confdata_of(robtarget), CONTROLLER.current())
    # at a wrist singularity (axis 5 at 0) axis 4 is set to 0 (manual, CalcJointT)
    if len(axes) == 6 and abs(axes[4]) < 1e-6:
        axes = axes.copy()
        axes[5] += axes[3]
        axes[3] = 0.0
    result.Set(jointtarget_values(axes))


def CalcRobT(result: Any, jointtarget: Any, tooldata: Any, wobjdata: Any) -> None:
    result.Set(robtarget_values(axes_of(jointtarget), Tool.of(tooldata), wobj_of(wobjdata)))


def OrientZYX(result: Any, z: float, y: float, x: float) -> None:
    """orientation from Euler angles in degrees: around z, then the new y, then the new x"""
    rotation = (
        pin.utils.rotate("z", math.radians(z))
        @ pin.utils.rotate("y", math.radians(y))
        @ pin.utils.rotate("x", math.radians(x))
    )
    result.Set(pose_values(pin.SE3(rotation, np.zeros(3)))[1])


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
