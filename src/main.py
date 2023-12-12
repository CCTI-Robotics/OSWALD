# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       8510                                                         #
# 	Created:      12/12/2023, 12:55:06 PM                                       #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #

# Library imports
from vex import *

# Brain should be defined by default
brain = Brain()

class XMotorGroup:
    def __init__(self, *motors: Motor):
        """
        Initialize the group and store the motors in a tuple.
        """
        self._motors: tuple[Motor, ...] = motors

    def spin(self, direction, speed, units) -> None:
        """
        Spin all motors in the group at a certain distance, speed, and direction.
        """
        for motor in self._motors:
            motor.spin(direction, speed, units)

    def stop(self) -> None:
        """
        Stop all motors in the group.
        """
        for motor in self._motors:
            motor.stop()

    def spin_some(self, direction, speed, units, *motors: int) -> None:
        """
        Spin the specified motors at a certain distance, speed, and direction.
        This eliminates the need to create a new motor group for every movement,
        or to access the motors list outside of the class.
        """
        for motor_index in motors:
            self[motor_index].spin(direction, speed, units)

    def __getitem__(self, index) -> Motor:
        """
        Get the motor from the list of motors.
        """
        return self._motors[index]

class XDrive:
    def __init__(self, m1port, m2port, m3port, m4port):
        """
        Initialize the XDrive.
        """
        m1 = Motor(m1port, True)
        m2 = Motor(m2port, True)
        m3 = Motor(m3port, True)
        m4 = Motor(m4port, True)

        self.group = XMotorGroup(m1, m2, m3, m4)

    def move_up(self, speed) -> None:
        """
        Move the XDrive up at the given speed. Relative to the robot, this would be forward.
        """
        self.group.spin(FORWARD, speed, PERCENT)

    def move_down(self, speed) -> None:
        """
        Move the XDrive down at the given speed. Relative to the robot, this would be backward.
        """
        self.group.spin(REVERSE, speed, PERCENT)

    def move_left(self, speed) -> None:
        """
        Move the XDrive left at the given speed.
        """
        self.group.spin_some(REVERSE, speed, PERCENT, 0, 3)
        self.group.spin_some(FORWARD, speed, PERCENT, 1, 2)

    def move_right(self, speed) -> None:
        """
        Move the XDrive right at the given speed.
        """
        self.group.spin_some(FORWARD, speed, PERCENT, 0, 3)
        self.group.spin_some(REVERSE, speed, PERCENT, 1, 2)

    def stop(self) -> None:
        """
        Stop all motors in the XDrive.
        """
        self.group.stop()


xdrive = XDrive(4, 5, 1, 2) # Initialize the XDrive
controller = Controller() # Initialize the controller


def control_loop():
    """
    The control loop of the XDrive robot. 
    This is where interactions with the controller take place.
    """
    while True:
        # Check if the controller's joysticks are being used. If they are, 
        # move the XDrive in the direction of the joystick.

        if controller.axis3.value() > 10:
            xdrive.move_up(controller.axis3.value())

        elif controller.axis3.value() < -10:
            xdrive.move_down(controller.axis3.value())
        
        elif controller.axis4.value() > 10:
            xdrive.move_right(controller.axis4.value())

        elif controller.axis4.value() < -10:
            xdrive.move_left(controller.axis4.value())

        else:
            xdrive.stop()

        # sleep(20) # Sleep for 20 milliseconds to prevent the CPU from being overloaded

Thread(control_loop()) # Start the control loop


