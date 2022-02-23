"""PyLabware driver for NEW_DEVICE."""

# You may want to import serial if the device is using serial connection and any
# connection options (baudrate/parity/...) need to be changed
# import serial

# You would need appropriate abstract types from typing
from typing import Optional, Union

# Core imports
from .. import parsers as parser
from ..controllers import AbstractHotplate, in_simulation_device_returns
from ..exceptions import PLConnectionError, PLDeviceCommandError
import serial

# You would typically need at minimum SLConnectionError to handle broken
# connection exceptions properly in is_connected()/is_idle()
# from ..exceptions import SLConnectionError

from ..models import LabDeviceCommands, ConnectionParameters


class RadleysCarouselConnectCommands(LabDeviceCommands):
    """Collection of command definitions for for NEW_DEVICE. These commands are
    based on the <language> section of the manufacturers user manual,
    version <version>, pages <pages>.
    """

    # ##########################  Constants ##################################
    # Add any relevant constants/literals - e.g device id, name - to this
    # section.
    DEFAULT_NAME = "Radleys Carousel Connect"
    TEMP_MODE = {0: "PRECISE", 1: "FAST"}
    # Does motor and stirrer turn off when resuming after power return?
    RESET_MODE = {0: "ALL OFF", 1: "ALL ON"}
    STATUS = {-1: "REMOTE BLOCKED", 0: "MANUAL", 1: "REMOTE START", 2: "REMOTE STOP"}

    # ################### Control commands ###################################
    # Add command dealing with device control/operation to this section.

    SET_TEMP = {"name": "OUT_SP_1", "type": int, "check": {"min": 20, "max": 300},
                "reply": {"type": float, "parser": parser.slicer, "args": [9, None]}}
    SET_SPEED = {"name": "OUT_SP_3", "type": float, "check": {"min": 100, "max": 1400},
                 "reply": {"type": str, "parser": parser.slicer, "args": [9, None]}}
    SET_RESET_MODE = {"name": "OUT_MODE_2", "type": int, "check": {"min": 0, "max": 1},
                      "reply": {"type": str, "parser": parser.slicer, "args": [0, None]}}
    SET_TEMP_MODE = {"name": "OUT_MODE_4", "type": int, "check": {"min": 0, "max": 1},
                      "reply": {"type": str, "parser": parser.slicer, "args": [0, None]}}
    START_HEAT = {"name": "START_1", "reply": {"type":str}}
    START_STIR = {"name": "START_2", "reply": {"type":str}}
    STOP_HEAT = {"name": "STOP_1", "reply": {"type":str}}
    STOP_STIR = {"name": "STOP_2", "reply": {"type":str}}
    RESET = {"name": "RESET"}
    GET_PROBE_TEMP = {"name": "IN_PV_1", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_PROBE_SAFETY_TEMP = {"name": "IN_PV_2", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_HOTPLATE_TEMP = {"name": "IN_PV_3", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_HOTPLATE_SAFETY_TEMP = {"name": "IN_PV_4", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_STIR_SPEED = {"name": "IN_PV_5", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_SET_TEMP = {"name": "IN_SP_1", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_SET_TEMP_SAFETY_DELTA = {"name": "IN_SP_2", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    GET_SET_MOTOR_SPEED = {"name": "IN_SP_3", "reply": {"type": float, "parser": parser.slicer, "args": [8, None]}}
    QUERY_TEMP_SENSOR_TYPE = {"name": "IN_MODE_1", "type": int, "reply": {"type": int, "parser": parser.slicer, "args": [10, None]}}
    QUERY_RESET_MODE = {"name": "IN_MODE_2", "type": int, "reply": {"type": int, "parser": parser.slicer, "args": [10, None]}}
    QUERY_TEMP_MODE = {"name": "IN_MODE_4", "type": int, "reply": {"type": int, "parser": parser.slicer, "args": [10, None]}}
    QUERY_STATUS = {"name": "STATUS", "type": int, "reply": {"type": int, "parser": parser.slicer, "args": [7, None]}}


    # ################### Configuration commands #############################
    # Add commands altering device configuration/settings to this section.
    PROTOCOL_NEW = {"name": "PA_NEW", "reply": {"type": str}}
    PROTOCOL_OLD = {"name": "PA_OLD", "reply": {"type": str}}
    SOFTWARE_VERSION = {"name": "SW_VERS", "reply": {"type": str}}
    CHECK_CONNECTION_ON = {"name": "CC_ON", "reply": {"type": str}}
    CHECK_CONNECTION_OFF = {"name": "CC_OFF", "reply": {"type": str}}


class RadleysCarouselConnect(AbstractHotplate):
    """
    This provides a Python class for the IKA RCT Digital hotplate
    based on the english section of the original
    operation manual 201811_IKAPlate-Lab_A1_25002139a.
    """

    def __init__(self, device_name: str, connection_mode: str, address: Optional[str], port: Union[str, int]):
        """Default constructor
        """

        # Load commands from helper class
        self.cmd = RadleysCarouselConnectCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        # Change any connection settings to device specific ones, if needed
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE
        connection_parameters["encoding"] = "utf_8"
        connection_parameters["force_7bit"] = True

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        # Terminator for the command string (from host to device)
        self.command_terminator = "\r\n"
        # Terminator for the reply string (from device to host)
        self.reply_terminator = "\r\n"
        # Separator between command and command arguments, if any
        self.args_delimiter = " "

    def initialize_device(self):
        """Set default operation mode & reset.
        """
        self.connection.open_connection()
        self.send(self.cmd.PROTOCOL_NEW)
        self.logger.info("Device initialised")

    # Wrapping is_connected is an easy way to ensure correct behavior in
    # simulation. See respective documentation section for the detailed explanation.
    @in_simulation_device_returns(RadleysCarouselConnectCommands.DEFAULT_NAME)
    def is_connected(self) -> bool:
        """"""
        try:
            reply = self.send(self.cmd.QUERY_STATUS)
            if reply == -1:
                self.logger.error("Device connection blocked")
                return False
            elif reply < -1:
                self.logger.error("Device error")
                return False
        except PLConnectionError:
            return False
        return True

    def is_idle(self) -> bool:
        """
        Checks whether the device is currently heating or stirring
        """
        reply = self.get_status
        if reply != 1:
            return False
        else:
            return True

    def get_status(self):
        """
        Checks the current device status
        """
        reply = self.send(self.cmd.QUERY_STATUS)
        if 3 > reply > -2:
            reply = self.cmd.STATUS[reply]
        else:
            reply = "ERROR"
        return reply

    def check_errors(self):
        """Not supported"""

    def clear_errors(self):
        """not supported"""

    def start_temperature_regulation(self) -> None:
        self.send(self.cmd.START_HEAT)
        self.logger.info("Started heating")

    def stop_temperature_regulation(self) -> None:
        self.send(self.cmd.STOP_HEAT)

    def start_stirring(self):
        self.send(self.cmd.START_STIR)
        self.logger.info("Started stirring")

    def stop_stirring(self):
        self.send(self.cmd.STOP_STIR)
        self.logger.info("Stopped stirring")

    def set_speed(self, speed: int):
        self.send(self.cmd.SET_SPEED, speed)

    def get_speed(self):
        return self.send(self.cmd.GET_STIR_SPEED)

    def get_speed_setpoint(self):
        return self.send(self.cmd.GET_SET_MOTOR_SPEED)

    def set_temperature(self, temperature: float, sensor: int = 0):
        self.send(self.cmd.SET_TEMP, temperature)

    def get_temperature_setpoint(self, sensor: int = 0):
        return self.send(self.cmd.GET_SET_TEMP)

    def get_temperature(self, sensor: int = 0):
        if sensor == 0:
            return self.send(self.cmd.GET_HOTPLATE_TEMP)
        elif sensor == 1:
            return self.send(self.cmd.GET_PROBE_TEMP)
        else:
            raise PLDeviceCommandError(f"Invalid sensor provided. Use 0 for hotplate or 1 for external probe")

    def get_temperature_safety_delta(self):
        self.send(self.cmd.GET_SET_TEMP_SAFETY_DELTA)

    def get_sensor_type(self):
        reply = self.send(self.cmd.QUERY_TEMP_SENSOR_TYPE)
        if reply == 0:
            return "HOTPLATE (0)"
        else:
            return "PROBE (1)"

    def set_reset_mode(self, mode=0):
        self.send(self.cmd.SET_RESET_MODE, mode)

    def get_reset_mode(self):
        return self.cmd.RESET_MODE[self.send(self.cmd.QUERY_RESET_MODE)]

    def set_heat_mode(self, mode=0):
        self.send(self.cmd.SET_TEMP_MODE, mode)

    def get_heat_mode(self):
        return self.cmd.TEMP_MODE[self.send(self.cmd.QUERY_TEMP_MODE)]

    def reset(self):
        self.send(self.cmd.RESET)

    def set_connection_check_on(self):
        self.send(self.cmd.CHECK_CONNECTION_ON)

    def set_connection_check_off(self):
        self.send(self.cmd.CHECK_CONNECTION_OFF)

