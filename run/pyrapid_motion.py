"""Motion of the robot for the programs translated by rapid2py.

The comment "!robot: <model>" in a module selects the robot model (robotmodel.py);
rapid2py translates it into a call of UseRobot.
"""

from typing import Any, Optional

import robotmodel


class Controller:
    """the robot of the task"""

    def __init__(self) -> None:
        self.robot: Optional[robotmodel.RobotModel] = None
        self.axes: Any = None

    def use_robot(self, name: str) -> None:
        if self.robot is not None and self.robot.name.lower() == name.lower():
            return
        self.robot = robotmodel.load(name, geometry=False)
        self.axes = self.robot.home.copy()


CONTROLLER = Controller()


def UseRobot(name: str) -> None:
    """the robot model of the task (comment !robot: <model>)"""
    CONTROLLER.use_robot(name)
