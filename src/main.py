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
import math

# Brain should be defined by default
brain = Brain()

class XMode:
    """
    The mode of the XDrive.
    """
    SINGLE_MOVE = 0
    FLUID = 1
    FIELD_CENTRIC = 2

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
            motor.stop(BRAKE)

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
    def __init__(self, m1port, m2port, m3port, m4port, mode = XMode.FLUID):
        """
        Create a class for the XDrive and initialize the motors.
        The last two motors are reversed. This is because the motors are mounted
        in opposite directions, and so they need to spin in opposite directions.
        """
        m1 = Motor(m1port)
        m2 = Motor(m2port)
        m3 = Motor(m3port, True)
        m4 = Motor(m4port, True)
        self.imu = Inertial(Ports.PORT10)

        self.mode = mode
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
        self.group.spin_some(FORWARD, speed, PERCENT, 1, 2)
        self.group.spin_some(REVERSE, speed, PERCENT, 0, 3)

    def move_right(self, speed) -> None:
        """
        Move the XDrive right at the given speed.
        """
        self.group.spin_some(REVERSE, speed, PERCENT, 1, 2)
        self.group.spin_some(FORWARD, speed, PERCENT, 0, 3)

    def turn_right(self, speed) -> None:
        """
        Turn the XDrive right at the given speed.
        """
        self.group.spin_some(FORWARD, speed, PERCENT, 0, 1)
        self.group.spin_some(REVERSE, speed, PERCENT, 2, 3)

    def turn_left(self, speed) -> None:
        """
        Turn the XDrive left at the given speed.
        """
        self.group.spin_some(REVERSE, speed, PERCENT, 0, 1)
        self.group.spin_some(FORWARD, speed, PERCENT, 2, 3)

    def stop(self) -> None:
        """
        Stop all motors in the XDrive.
        """
        self.group.stop()

    def set_mode(self, mode):
        """
        Set the mode of the XDrive.
        """
        self.mode = mode

    def process_input(self, controller: Controller) -> None:
        """
        Process the input from the controller and move the XDrive accordingly.
        """

        left_y = controller.axis3.position()
        left_x = controller.axis4.position()
        right_x = controller.axis1.position()

        if self.mode == XMode.FLUID or self.mode == XMode.FIELD_CENTRIC:
            self.move_fluid(left_y, left_x, right_x)

        elif self.mode == XMode.SINGLE_MOVE:
            self.move_single(left_y, left_x, right_x)

    def move_single(self, left_y, left_x, right_x) -> None:
        """
        Legacy single-move code to only perform one movement
        action at a time. May be useful for debugging and 
        autonomous movement.
        """
        # Check if the controller's joysticks are being used. If they are, 
        # move the XDrive in the direction of the joystick.

        if left_y > 10:
            self.move_up(left_y)

        elif left_y < -10:
            self.move_down(abs(left_y))
        
        elif left_x > 10:
            self.move_right(left_x)

        elif left_x < -10:
            self.move_left(abs(left_x))

        elif right_x > 10:
            self.turn_right(right_x)

        elif right_x < -10:
            self.turn_left(abs(right_x))

        else:
            self.stop()

    def move_fluid(self, left_y, left_x, right_x) -> None:
        mr1 = 0
        mr2 = 0
        mr3 = 0
        mr4 = 0

        left_dead = (
            left_y < 10 and left_y > -10 and
            left_x < 10 and left_x > -10
        )
        right_dead = (
            right_x < 10 and right_x > -10
        )

        if not right_dead:
            mr1 += right_x
            mr2 += right_x
            mr3 -= right_x
            mr4 -= right_x

        if not left_dead:
            mr1 += left_y
            mr2 += left_y
            mr3 += left_y
            mr4 += left_y

            mr1 += left_x
            mr2 -= left_x
            mr3 -= left_x
            mr4 += left_x
            
        if not (mr1 or mr2 or mr3 or mr4):
            self.stop()

        else:
            if self.mode == XMode.FIELD_CENTRIC:
                mr1, mr2, mr3, mr4 = self.get_centric_power(left_x, left_y, right_x)
            self.group[0].spin(FORWARD, mr1, PERCENT)
            self.group[1].spin(FORWARD, mr2, PERCENT)
            self.group[2].spin(FORWARD, mr3, PERCENT)
            self.group[3].spin(FORWARD, mr4, PERCENT)

    def get_centric_power(self, x, y, rx) -> tuple[float, float, float, float]:
        """
        To calculate the power of field-centric movement. Still in development and 
        does not work.
        """
        heading = self.imu.heading()
        heading = heading * (math.pi / 180) # Convert to radians

        print(heading)

        rotation_x = x * math.cos(-heading) - y * math.sin(-heading)
        rotation_y = x * math.sin(-heading) + y * math.cos(-heading)

        denominator = max(abs(rotation_y) + abs(rotation_x) + abs(rx), 1)
        front_left_power = (rotation_y + rotation_x + rx) / denominator
        back_left_power = (rotation_y - rotation_x + rx) / denominator
        front_right_power = (rotation_y - rotation_x - rx) / denominator
        back_right_power = (rotation_y + rotation_x - rx) / denominator

        return (
            front_left_power,
            back_left_power,
            front_right_power,
            back_right_power
        )

class Puncher:
    def __init__(self, port):
        """
        Initialize the puncher motor.
        """
        self.motor = Motor(port)
        self.active = False

    def run(self, speed) -> None:
        """
        Run the puncher motor at the given speed.
        """
        self.motor.spin(FORWARD, speed, PERCENT)

    def stop(self) -> None:
        """
        Stop the puncher motor.
        """
        self.motor.stop(BRAKE)

puncher = Puncher(Ports.PORT7) # Initialize the puncher mechanism
xdrive = XDrive(Ports.PORT1, Ports.PORT2, Ports.PORT4, Ports.PORT5) # Initialize the XDrive
controller = Controller() # Initialize the controller

def control_loop():
    """
    The control loop of the XDrive robot. 
    This is where interactions with the controller take place.
    """
    while True: 
        # Handle movement for the puncher
        if controller.buttonA.pressing():
            puncher.active = not puncher.active

        if puncher.active:
            puncher.run(100)

        if controller.buttonR1.pressing():
            puncher.run(100)

        # Handle the XDrive movement
        xdrive.process_input(controller)


Thread(control_loop()) # Start the control loop


