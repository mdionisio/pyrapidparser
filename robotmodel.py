"""Robot models for the RAPID motion instructions, loaded with Pinocchio.

The models are URDF or xacro files:

- third_party/abb: the ABB models of ROS-Industrial (git submodule
  https://github.com/ros-industrial/abb), named after their xacro file, e.g.
  irb120_3_58 for abb_irb120_support/urdf/irb120_3_58.xacro;
- models/: models of this project, e.g. irb460_110_240.

models/<name>.json, when present, completes or overrides the data of the model:

    {
        "description": "one line",
        "approximate": "why the model is approximate (reported as a warning)",
        "rapid_axes": [1, 2, 3, 6],
        "joints": {"joint_3": {"2": -1, "3": 1}},
        "axis_limits": {"3": [-20, 120, 120]},
        "acceleration": [5.0, 5.0, 5.0, 10.0],
        "effort": [100, 100, 50, 10],
        "home": [0, 0, 0, 0],
        "cad_meshes": {"scale": 0.001, "links": {"link_1": "<model>/cad/swing.stl"}}
    }

rapid_axes are the RAPID axes (rax_1 ... rax_6) moved by the robot, in order;
joints gives the position of a model joint as a linear combination of the RAPID
axes (default: the joints of the URDF that are not <mimic>, in order, one per
axis); axis_limits are [lower, upper, velocity] in degrees and degrees/s;
acceleration (rad/s^2), effort (Nm) and home (degrees) are per axis; cad_meshes
are the parts of a CAD assembly of the robot at the zero position (in the base
frame, scaled by scale, files relative to models/): when the files exist they
replace the geometry of the links in the view.

The data missing from the model is replaced with default values, and a warning
says what is used instead. Units: m, rad, s. The conversion from the RAPID units
(mm, degrees) is in run/pyrapid_motion.py.
"""

from __future__ import annotations

import functools
import glob
import json
import math
import os
import sys
import threading
import types
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

try:
    import numpy as np
    import pinocchio as pin
except ImportError:  # pragma: no cover
    # the model names (available_models, find_model) do not need the motion dependencies
    np = None  # type: ignore[assignment]
    pin = None

if TYPE_CHECKING:
    import numpy.typing as npt

    Vector = npt.NDArray[np.float64]

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ABB_DIR = os.path.join(PROJECT_DIR, "third_party", "abb")
MODELS_DIR = os.path.join(PROJECT_DIR, "models")

# time to reach the maximum speed of an axis when the model has no acceleration limits
DEFAULT_ACCELERATION_TIME = 0.5
# velocity of an axis when the URDF has no velocity limit (rad/s)
DEFAULT_VELOCITY = 1.0
# tolerance of the inverse kinematics solutions
IK_TOLERANCE = 1e-6


class ModelError(Exception):
    pass


def _package_dirs() -> list[str]:
    return [ABB_DIR, MODELS_DIR]


def _share_directory(package: str) -> str:
    for base in _package_dirs():
        path = os.path.join(base, package)
        if os.path.isdir(path):
            return path
    raise ModelError("package %s not found in %s" % (package, ", ".join(_package_dirs())))


def _install_package_resolver() -> None:
    """xacro resolves $(find package) with ament_index_python (ROS 2). Without ROS
    the packages are searched in third_party/abb and models/."""
    try:
        import ament_index_python.packages  # noqa: F401
    except ImportError:
        packages = types.ModuleType("ament_index_python.packages")
        setattr(packages, "get_package_share_directory", _share_directory)
        ament = types.ModuleType("ament_index_python")
        setattr(ament, "packages", packages)
        sys.modules["ament_index_python"] = ament
        sys.modules["ament_index_python.packages"] = packages


@functools.lru_cache(maxsize=None)
def available_models() -> dict[str, str]:
    """model name (lower case) -> URDF or xacro file"""
    models: dict[str, str] = {}
    for path in sorted(glob.glob(os.path.join(ABB_DIR, "*_support", "urdf", "*.xacro"))):
        if not path.endswith("_macro.xacro"):
            models[os.path.basename(path)[: -len(".xacro")].lower()] = path
    for pattern in ("*.urdf", "*.xacro"):
        for path in sorted(glob.glob(os.path.join(MODELS_DIR, pattern))):
            models[os.path.splitext(os.path.basename(path))[0].lower()] = path
    return models


def find_model(name: str) -> str:
    path = available_models().get(name.lower())
    if path is None:
        if not os.path.isdir(os.path.join(ABB_DIR, "abb_irb120_support")):
            raise ModelError(
                "unknown robot model %s: the submodule third_party/abb is not checked out "
                "(git submodule update --init)" % (name,)
            )
        raise ModelError("unknown robot model %s" % (name,))
    return path


def urdf_xml(path: str) -> str:
    if path.endswith(".xacro"):
        import xacro

        _install_package_resolver()
        return str(xacro.process_file(path).toxml())
    with open(path, "r") as f:
        return f.read()


def quadrant(angle: float) -> int:
    """confdata quadrant of a rotating axis: 0 is [0, 90) degrees, -1 is [-90, 0)"""
    return int(math.floor(angle / (math.pi / 2) + 1e-9))


@dataclass
class UrdfJoint:
    name: str
    type: str
    lower: Optional[float] = None
    upper: Optional[float] = None
    velocity: Optional[float] = None
    effort: Optional[float] = None
    mimic: Optional[tuple[str, float, float]] = None


def _parse_joints(xml: str) -> dict[str, UrdfJoint]:
    joints: dict[str, UrdfJoint] = {}
    for element in ET.fromstring(xml).iter("joint"):
        joint = UrdfJoint(element.get("name", ""), element.get("type", ""))
        limit = element.find("limit")
        if limit is not None:
            for attr in ("lower", "upper", "velocity", "effort"):
                value = limit.get(attr)
                if value is not None:
                    setattr(joint, attr, float(value))
        mimic = element.find("mimic")
        if mimic is not None:
            joint.mimic = (
                mimic.get("joint", ""),
                float(mimic.get("multiplier", "1")),
                float(mimic.get("offset", "0")),
            )
        joints[joint.name] = joint
    return joints


@dataclass
class AnalyticArm:
    """geometry of a 6 axis arm with the axes z, y, y, x, y, x at zero and a spherical
    wrist (the ABB serial arms): the inverse kinematics has a closed form"""

    a1: float  # joint 2: distance from axis 1
    c1: float  # joint 2: height
    lower_length: float
    lower_angle: float  # direction of the lower arm (joint 2 -> 3) from the vertical
    upper_length: float
    upper_angle: float  # direction joint 3 -> wrist center from the vertical
    wrist_in_flange: Vector  # wrist center in the flange frame
    flange_rotation: Vector  # flange orientation at zero


@dataclass
class Solution:
    axes: Vector
    error: float = 0.0


@dataclass
class RobotModel:
    name: str
    path: str
    xml: str
    model: Any
    axis_names: list[str]
    rapid_axes: list[int]
    lower: Vector
    upper: Vector
    velocity: Vector
    acceleration: Vector
    effort: Optional[Vector]
    home: Vector
    has_dynamics: bool
    approximate: Optional[str]
    description: str
    warnings: list[str] = field(default_factory=list)
    # model joint position = coupling @ axes + coupling_offset
    coupling: Vector = field(default_factory=lambda: np.zeros((0, 0)))
    coupling_offset: Vector = field(default_factory=lambda: np.zeros(0))
    base_frame: int = 0
    flange_frame: int = 0
    analytic: Optional[AnalyticArm] = None
    visual_model: Any = None
    collision_model: Any = None
    base_inertias: list[Any] = field(default_factory=list)

    # Pinocchio data, one for each thread (the program plans while the robot moves)
    local: threading.local = field(default_factory=threading.local)

    @property
    def data(self) -> Any:
        data = getattr(self.local, "data", None)
        if data is None:
            data = self.model.createData()
            self.local.data = data
        return data

    @property
    def naxes(self) -> int:
        return len(self.rapid_axes)

    # configurations

    def configuration(self, axes: Vector) -> Any:
        """the Pinocchio configuration vector of the axis positions"""
        joint_values = self.coupling @ axes + self.coupling_offset
        q = pin.neutral(self.model)
        for j in range(1, self.model.njoints):
            joint = self.model.joints[j]
            value = joint_values[joint.idx_v]
            if joint.nq == 2:
                q[joint.idx_q] = math.cos(value)
                q[joint.idx_q + 1] = math.sin(value)
            else:
                q[joint.idx_q] = value
        return q

    def joint_velocity(self, axes_velocity: Vector) -> Vector:
        result: Vector = self.coupling @ axes_velocity
        return result

    # kinematics

    def base_placement(self) -> Any:
        return self.data.oMf[self.base_frame]

    def fk(self, axes: Vector) -> Any:
        """flange (tool0) placement in the base frame"""
        q = self.configuration(axes)
        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)
        return self.data.oMf[self.base_frame].actInv(self.data.oMf[self.flange_frame])

    def within_limits(self, axes: Vector) -> bool:
        return bool(np.all(axes >= self.lower - 1e-9) and np.all(axes <= self.upper + 1e-9))

    def ik(self, target: Any, reference: Vector) -> list[Solution]:
        """all the axis positions (within the limits) that place the flange at target
        (in the base frame); the first is the nearest to reference"""
        if self.analytic is not None:
            solutions = self._ik_analytic(target, reference)
        else:
            solutions = self._ik_numeric(target, reference)
        solutions.sort(key=lambda s: float(np.sum(np.abs(s.axes - reference))))
        return solutions

    def _pose_error(self, axes: Vector, target: Any) -> float:
        return float(np.linalg.norm(pin.log6(self.fk(axes).actInv(target)).vector))

    def _turn_variants(self, axes: Vector) -> list[Vector]:
        """the same position with the axes turned of whole revolutions"""
        variants = [axes]
        for i in range(self.naxes):
            more = []
            for v in variants:
                for turns in (-2, -1, 1, 2):
                    w = v.copy()
                    w[i] += turns * 2 * math.pi
                    if self.lower[i] - 1e-9 <= w[i] <= self.upper[i] + 1e-9:
                        more.append(w)
            variants += more
        return variants

    def _ik_analytic(self, target: Any, reference: Vector) -> list[Solution]:
        arm = self.analytic
        assert arm is not None
        world_target = self.base_placement().act(target)
        rotation = world_target.rotation
        center = world_target.translation + rotation @ arm.wrist_in_flange
        found: list[Solution] = []
        if math.hypot(center[0], center[1]) < 1e-9:
            # wrist center on axis 1: any axis 1 position, keep the current one
            first_axes = [float(reference[0])]
        else:
            q1 = math.atan2(center[1], center[0])
            first_axes = [q1, q1 + math.pi]
        for q1 in first_axes:
            x = center[0] * math.cos(q1) + center[1] * math.sin(q1) - arm.a1
            z = center[2] - arm.c1
            distance2 = x * x + z * z
            l1, l2 = arm.lower_length, arm.upper_length
            cos_delta = (distance2 - l1 * l1 - l2 * l2) / (2 * l1 * l2)
            if abs(cos_delta) > 1 + 1e-9:
                continue
            cos_delta = max(-1.0, min(1.0, cos_delta))
            gamma = math.atan2(x, z)
            for delta in {math.acos(cos_delta), -math.acos(cos_delta)}:
                theta1 = gamma - math.atan2(l2 * math.sin(delta), l1 + l2 * math.cos(delta))
                q2 = theta1 - arm.lower_angle
                q3 = theta1 + delta - arm.upper_angle - q2
                arm_rotation = pin.utils.rotate("z", q1) @ pin.utils.rotate("y", q2 + q3)
                wrist = arm_rotation.T @ rotation @ arm.flange_rotation.T
                for q4, q5, q6 in self._wrist_angles(wrist, float(reference[3])):
                    axes = np.array([q1, q2, q3, q4, q5, q6])
                    axes = (axes + math.pi) % (2 * math.pi) - math.pi
                    for variant in self._turn_variants(axes):
                        if not self.within_limits(variant):
                            continue
                        error = self._pose_error(variant, target)
                        if error < 1e-6 and not any(
                            np.allclose(variant, s.axes, atol=1e-7) for s in found
                        ):
                            found.append(Solution(variant, error))
        return found

    @staticmethod
    def _wrist_angles(m: Vector, q4_reference: float) -> list[tuple[float, float, float]]:
        """m = Rx(q4) Ry(q5) Rx(q6)"""
        cos5 = max(-1.0, min(1.0, float(m[0, 0])))
        q5 = math.acos(cos5)
        if abs(math.sin(q5)) < 1e-9:
            # wrist singularity: only q4 + q6 (or q4 - q6) is defined
            total = math.atan2(m[2, 1], m[1, 1])
            if cos5 > 0:
                return [(q4_reference, 0.0, total - q4_reference)]
            return [(q4_reference, math.pi, q4_reference - total)]
        result = []
        for s5 in (q5, -q5):
            sin5 = math.sin(s5)
            q4 = math.atan2(m[1, 0] / sin5, -m[2, 0] / sin5)
            q6 = math.atan2(m[0, 1] / sin5, m[0, 2] / sin5)
            result.append((q4, s5, q6))
        return result

    def _ik_numeric(self, target: Any, reference: Vector) -> list[Solution]:
        """damped least squares from the reference and from the home position"""
        found: list[Solution] = []
        seeds = [reference, self.home, np.clip(np.zeros(self.naxes), self.lower, self.upper)]
        for seed in seeds:
            axes = self._dls(target, seed)
            if axes is None:
                continue
            error = self._pose_error(axes, target)
            if not any(np.allclose(axes, s.axes, atol=1e-6) for s in found):
                found.append(Solution(axes, error))
        return found

    def _dls(self, target: Any, seed: Vector) -> Optional[Vector]:
        world_target = self.base_placement().act(target)
        axes = np.array(seed, dtype=float)
        damping = 1e-9
        for _ in range(500):
            q = self.configuration(axes)
            pin.forwardKinematics(self.model, self.data, q)
            pin.updateFramePlacements(self.model, self.data)
            current = self.data.oMf[self.flange_frame]
            error = pin.log6(current.actInv(world_target)).vector
            if np.linalg.norm(error) < IK_TOLERANCE:
                return axes if self.within_limits(axes) else None
            pin.computeJointJacobians(self.model, self.data, q)
            jacobian = pin.getFrameJacobian(
                self.model, self.data, self.flange_frame, pin.ReferenceFrame.LOCAL
            )
            jacobian = -pin.Jlog6(current.actInv(world_target).inverse()) @ jacobian
            jacobian = jacobian @ self.coupling
            # damped least squares: the 4 axis robots have less axes than the pose
            step = -np.linalg.solve(
                jacobian.T @ jacobian + damping * np.eye(self.naxes), jacobian.T @ error
            )
            norm = float(np.linalg.norm(step))
            if norm > 0.5:
                step *= 0.5 / norm
            axes = np.clip(axes + step, self.lower, self.upper)
        return None

    # configuration data (confdata)

    def confdata(self, axes: Vector) -> tuple[int, int, int, int]:
        """cf1, cf4, cf6, cfx of the RAPID instructions manual (confdata, 3.20)"""
        values = {axis: float(axes[i]) for i, axis in enumerate(self.rapid_axes)}
        cf1 = quadrant(values.get(1, 0.0))
        cf4 = quadrant(values[4]) if 4 in values else 0
        cf6 = quadrant(values[6]) if 6 in values else 0
        cfx = 0
        if self.naxes == 6 and self.analytic is not None:
            arm = self.analytic
            q2 = values[2]
            q23 = values[2] + values[3]
            # wrist center and joint 2 in the arm plane (x forward, z up)
            lower = arm.lower_length * np.array(
                [math.sin(arm.lower_angle + q2), math.cos(arm.lower_angle + q2)]
            )
            upper = arm.upper_length * np.array(
                [math.sin(arm.upper_angle + q23), math.cos(arm.upper_angle + q23)]
            )
            center = lower + upper
            behind_axis1 = arm.a1 + center[0] < 0
            # the front side of the lower arm is on its right looking from joint 2
            normal = np.array([lower[1], -lower[0]])
            behind_lower_arm = float(normal @ center) < 0
            negative5 = values[5] < 0
            cfx = int(4 * behind_axis1 + 2 * behind_lower_arm + negative5)
        return (cf1, cf4, cf6, cfx)

    def matches(self, axes: Vector, conf: tuple[int, int, int, int]) -> bool:
        actual = self.confdata(axes)
        if self.naxes == 6:
            return actual == conf
        if self.naxes == 4:
            # 4-axis serial link robots: only cf6 is used
            return actual[2] == conf[2]
        return True

    # dynamics

    def set_payload(self, mass: float, cog: Vector, inertia: Vector) -> None:
        """the load of the tool, in the flange frame (cog in m, inertia diagonal kg m^2)"""
        frame = self.model.frames[self.flange_frame]
        for j, original in enumerate(self.base_inertias):
            self.model.inertias[j] = original.copy()
        if mass <= 0:
            return
        load = pin.Inertia(mass, np.asarray(cog, dtype=float), np.diag(inertia))
        joint = frame.parentJoint
        self.model.inertias[joint] = self.model.inertias[joint] + frame.placement.act(load)

    def torques(self, axes: Vector, velocity: Vector, acceleration: Vector) -> Vector:
        """motor torques of the axes (inverse dynamics)"""
        q = self.configuration(axes)
        v = self.joint_velocity(velocity)
        a = self.joint_velocity(acceleration)
        tau = pin.rnea(self.model, self.data, q, v, a)
        result: Vector = self.coupling.T @ tau
        return result


def _analytic_arm(robot: RobotModel) -> Optional[AnalyticArm]:
    """the closed form inverse kinematics applies when the flange chain is made of
    the 6 axes, with the axes z, y, y, x, y, x and a spherical wrist"""
    if robot.naxes != 6:
        return None
    model, data = robot.model, robot.data
    chain = [j for j in model.supports[model.frames[robot.flange_frame].parentJoint] if j > 0]
    names = [model.names[j] for j in chain]
    if names != robot.axis_names:
        return None
    if not np.allclose(robot.coupling[:, :], _identity_coupling(robot, chain)):
        return None
    zero = np.zeros(6)
    robot.fk(zero)
    if not np.allclose(robot.base_placement().homogeneous, np.eye(4)):
        return None
    expected = [(2, 1), (1, 1), (1, 1), (0, 1), (1, 1), (0, 1)]
    positions = []
    for j, (axis, _) in zip(chain, expected):
        joint = model.joints[j]
        rotation = data.oMi[j].rotation
        local = np.zeros(3)
        short = joint.shortname()
        if short.startswith("JointModelR") and short[-1] in "XYZ":
            local["XYZ".index(short[-1])] = 1
        elif hasattr(joint.extract(), "axis"):
            local = np.array(joint.extract().axis, dtype=float)
        else:
            return None
        world = rotation @ local
        unit = np.zeros(3)
        unit[axis] = 1
        if not np.allclose(world, unit, atol=1e-6):
            return None
        positions.append(data.oMi[j].translation.copy())
    j1, j2, j3, j4, j5, j6 = positions
    tol = 1e-6
    if abs(j1[0]) > tol or abs(j1[1]) > tol:
        return None
    if any(abs(p[1]) > tol for p in (j2, j3, j4, j5, j6)):
        return None
    # spherical wrist: axes 4 and 6 (along x) pass through the center on axis 5
    if abs(j4[2] - j5[2]) > tol or abs(j6[2] - j5[2]) > tol:
        return None
    center = j5
    lower = j3 - j2
    upper = center - j3
    flange = data.oMf[robot.flange_frame]
    return AnalyticArm(
        a1=float(j2[0]),
        c1=float(j2[2]),
        lower_length=float(np.hypot(lower[0], lower[2])),
        lower_angle=math.atan2(lower[0], lower[2]),
        upper_length=float(np.hypot(upper[0], upper[2])),
        upper_angle=math.atan2(upper[0], upper[2]),
        wrist_in_flange=flange.rotation.T @ (center - flange.translation),
        flange_rotation=flange.rotation.copy(),
    )


def _identity_coupling(robot: RobotModel, chain: list[int]) -> Vector:
    expected = robot.coupling.copy()
    for i, j in enumerate(chain):
        expected[robot.model.joints[j].idx_v, :] = 0
        expected[robot.model.joints[j].idx_v, i] = 1
    return expected


def _load_options(name: str) -> dict[str, Any]:
    path = os.path.join(MODELS_DIR, name + ".json")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        options: dict[str, Any] = json.load(f)
    return options


def _mesh_xml(xml: str) -> str:
    """package:// mesh paths of the models resolved to files"""
    root = ET.fromstring(xml)
    for mesh in root.iter("mesh"):
        filename = mesh.get("filename", "")
        if filename.startswith("package://"):
            package, _, rest = filename[len("package://") :].partition("/")
            try:
                mesh.set("filename", os.path.join(_share_directory(package), rest))
            except ModelError:
                pass
    return ET.tostring(root, encoding="unicode")


def _cad_xml(robot: RobotModel, xml: str, cad: Optional[dict[str, Any]]) -> str:
    """the visual geometry of the links replaced by the meshes of the CAD assembly at the
    zero position, when the files exist"""
    if not cad:
        return xml
    scale = float(cad.get("scale", 1.0))
    files = {
        link: os.path.join(MODELS_DIR, path)
        for link, path in cad.get("links", {}).items()
        if os.path.exists(os.path.join(MODELS_DIR, path))
    }
    if not files:
        return xml
    model, data = robot.model, robot.data
    q = robot.configuration(np.zeros(robot.naxes))
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)
    root = ET.fromstring(xml)
    for link in root.iter("link"):
        name = link.get("name", "")
        if name not in files or not model.existFrame(name):
            continue
        # the mesh is in the base frame: its origin in the link frame
        origin = data.oMf[model.getFrameId(name)].inverse()
        material = link.find("visual/material")
        for visual in link.findall("visual"):
            link.remove(visual)
        visual = ET.SubElement(link, "visual")
        ET.SubElement(
            visual,
            "origin",
            xyz=" ".join("%.6f" % v for v in origin.translation),
            rpy=" ".join("%.6f" % v for v in pin.rpy.matrixToRpy(origin.rotation)),
        )
        geometry = ET.SubElement(visual, "geometry")
        ET.SubElement(geometry, "mesh", filename=files[name], scale="%g %g %g" % ((scale,) * 3))
        if material is not None:
            visual.append(material)
    return ET.tostring(root, encoding="unicode")


def load(name: str, geometry: bool = False, verbose: bool = True) -> RobotModel:
    """load the model name; the warnings about the missing data are printed on stderr
    when verbose"""
    if pin is None:
        raise ModelError(
            "the robot models need Pinocchio: pip install pyrapidparser[motion]"
        )  # pragma: no cover
    path = find_model(name)
    name = os.path.splitext(os.path.basename(path))[0]
    options = _load_options(name)
    xml = urdf_xml(path)
    model = pin.buildModelFromXML(xml)
    urdf_joints = _parse_joints(xml)
    warnings: list[str] = []

    moving = [model.names[j] for j in range(1, model.njoints)]
    if "joints" in options:
        rapid_axes = [int(a) for a in options["rapid_axes"]]
        joint_axes: dict[str, dict[int, float]] = {
            joint: {int(a): float(c) for a, c in combination.items()}
            for joint, combination in options["joints"].items()
        }
        axis_names = ["axis_%d" % a for a in rapid_axes]
    else:
        axis_names = [n for n in moving if urdf_joints.get(n, UrdfJoint(n, "")).mimic is None]
        rapid_axes = [int(a) for a in options.get("rapid_axes", range(1, len(axis_names) + 1))]
        if len(rapid_axes) != len(axis_names):
            raise ModelError(
                "%s: %d axes and %d rapid_axes" % (name, len(axis_names), len(rapid_axes))
            )
        joint_axes = {n: {rapid_axes[i]: 1.0} for i, n in enumerate(axis_names)}

    naxes = len(rapid_axes)
    coupling = np.zeros((model.nv, naxes))
    offset = np.zeros(model.nv)

    def combination(joint_name: str, depth: int = 0) -> tuple[Vector, float]:
        row = np.zeros(naxes)
        if joint_name in joint_axes:
            for axis, coefficient in joint_axes[joint_name].items():
                row[rapid_axes.index(axis)] = coefficient
            return row, 0.0
        joint = urdf_joints.get(joint_name)
        if joint is not None and joint.mimic is not None and depth < 10:
            source, multiplier, mimic_offset = joint.mimic
            source_row, source_offset = combination(source, depth + 1)
            return multiplier * source_row, multiplier * source_offset + mimic_offset
        warnings.append("joint %s is not moved by any axis, it stays at 0" % (joint_name,))
        return row, 0.0

    for j in range(1, model.njoints):
        idx = model.joints[j].idx_v
        coupling[idx, :], offset[idx] = combination(model.names[j])

    lower = np.full(naxes, -math.pi)
    upper = np.full(naxes, math.pi)
    velocity = np.full(naxes, DEFAULT_VELOCITY)
    effort_values: list[Optional[float]] = [None] * naxes
    missing_velocity = []
    for i, axis_name in enumerate(axis_names):
        joint = urdf_joints.get(axis_name)
        if joint is not None:
            if joint.lower is not None and joint.upper is not None and joint.type != "continuous":
                lower[i], upper[i] = joint.lower, joint.upper
            if joint.velocity:
                velocity[i] = joint.velocity
            else:
                missing_velocity.append(rapid_axes[i])
            if joint.effort:
                effort_values[i] = joint.effort
        limits = options.get("axis_limits", {}).get(str(rapid_axes[i]))
        if limits is not None:
            lower[i], upper[i], velocity[i] = (math.radians(v) for v in limits)
            if rapid_axes[i] in missing_velocity:
                missing_velocity.remove(rapid_axes[i])
    if missing_velocity:
        warnings.append(
            "no velocity limit for the axes %s, using %.1f rad/s"
            % (", ".join(map(str, missing_velocity)), DEFAULT_VELOCITY)
        )

    if "acceleration" in options:
        acceleration = np.array(options["acceleration"], dtype=float)
    else:
        acceleration = velocity / DEFAULT_ACCELERATION_TIME
        warnings.append(
            "no acceleration limits, using velocity / %.1f s (full speed in %.1f s)"
            % (DEFAULT_ACCELERATION_TIME, DEFAULT_ACCELERATION_TIME)
        )

    effort: Optional[Vector] = None
    if "effort" in options:
        effort = np.array(options["effort"], dtype=float)
    elif all(e is not None for e in effort_values):
        effort = np.array(effort_values, dtype=float)
    else:
        warnings.append("no motor torque limits (effort), the torques are not checked")

    masses = [model.inertias[j].mass for j in range(1, model.njoints)]
    has_dynamics = all(m > 0 for m in masses)
    if not any(m > 0 for m in masses):
        warnings.append("no inertial data, the joint torques are not computed")
    elif not has_dynamics:
        empty = [model.names[j] for j in range(1, model.njoints) if model.inertias[j].mass <= 0]
        warnings.append(
            "no inertial data for %s, the joint torques are not computed" % (", ".join(empty),)
        )

    approximate = options.get("approximate")
    if approximate:
        warnings.insert(0, "approximate model: %s" % (approximate,))

    home = np.radians(np.array(options.get("home", [0.0] * naxes), dtype=float))

    def frame(names: tuple[str, ...]) -> int:
        for n in names:
            if model.existFrame(n):
                return int(model.getFrameId(n))
        raise ModelError("%s: no frame %s" % (name, " or ".join(names)))

    robot = RobotModel(
        name=name,
        path=path,
        xml=xml,
        model=model,
        axis_names=axis_names,
        rapid_axes=rapid_axes,
        lower=lower,
        upper=upper,
        velocity=velocity,
        acceleration=acceleration,
        effort=effort,
        home=home,
        has_dynamics=has_dynamics,
        approximate=approximate,
        description=str(options.get("description", "")),
        warnings=warnings,
        coupling=coupling,
        coupling_offset=offset,
        base_frame=frame(("base",)) if model.existFrame("base") else 0,
        flange_frame=frame(("tool0", "flange")),
        base_inertias=[model.inertias[j].copy() for j in range(model.njoints)],
    )
    robot.analytic = _analytic_arm(robot)
    if geometry:
        mesh_xml = _mesh_xml(_cad_xml(robot, xml, options.get("cad_meshes")))
        robot.visual_model = pin.buildGeomFromUrdfString(
            model, mesh_xml, pin.GeometryType.VISUAL, package_dirs=_package_dirs()
        )
        robot.collision_model = pin.buildGeomFromUrdfString(
            model, mesh_xml, pin.GeometryType.COLLISION, package_dirs=_package_dirs()
        )
    if verbose:
        for message in warnings:
            print("warning: %s: %s" % (name, message), file=sys.stderr)
    return robot


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="robot models for the motion instructions")
    parser.add_argument("model", nargs="?", help="show the data of a model")
    args = parser.parse_args()
    if args.model is None:
        for name, path in available_models().items():
            print("%-20s %s" % (name, os.path.relpath(path, PROJECT_DIR)))
        return
    robot = load(args.model)
    print("model:      %s (%s)" % (robot.name, os.path.relpath(robot.path, PROJECT_DIR)))
    if robot.description:
        print("            %s" % (robot.description,))
    print("axes:       %s" % (", ".join("rax_%d" % a for a in robot.rapid_axes),))
    print(
        "kinematics: %s" % ("closed form" if robot.analytic else "numeric (damped least squares)",)
    )
    print("dynamics:   %s" % ("yes" if robot.has_dynamics else "no"))
    cad = _load_options(robot.name).get("cad_meshes")
    if cad:
        files = list(cad.get("links", {}).values())
        found = sum(os.path.exists(os.path.join(MODELS_DIR, f)) for f in files)
        print(
            "view:       CAD meshes %d of %d%s" % (found, len(files), "" if found else " (boxes)")
        )
    for i, axis in enumerate(robot.rapid_axes):
        print(
            "  axis %d: %8.1f .. %6.1f deg  %6.1f deg/s  %7.1f deg/s^2%s"
            % (
                axis,
                math.degrees(robot.lower[i]),
                math.degrees(robot.upper[i]),
                math.degrees(robot.velocity[i]),
                math.degrees(robot.acceleration[i]),
                "  %.0f Nm" % robot.effort[i] if robot.effort is not None else "",
            )
        )


if __name__ == "__main__":
    main()
