MODULE robot
    ! executed by test_rapid2py.py: the robot model of the task
    !robot: irb120_3_58
    PROC main()
        !python:import pyrapid_motion
        !python:print("robot", pyrapid_motion.CONTROLLER.robot.name, len(pyrapid_motion.CONTROLLER.axes))
    ENDPROC
ENDMODULE
