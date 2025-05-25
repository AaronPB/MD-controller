import math
import logging

from collections import deque
from enums.states import ControllerState

class PIControllerPump:
    def __init__(self, id: str, params: dict) -> None:
        self.id = id
        self.state = ControllerState.MANUAL
        # Control params
        self.kp = float(params["control"]["kp"])
        self.ti = float(params["control"]["ti"])
        # Time steps
        self.tr  = int(params["time_steps"]["tr"])
        self.dt = int(params["time_steps"]["dt"])
        # Default setpoint (m3/h) and manual operation point (%)
        self.r = float(params["default"]["sp"])
        self.manual_u = float(params["default"]["u"])
        # Last written values
        self.last_u: float = 0
        # Default settings
        self.hyst_top_offset = float(params["hysteresis"]["top_offset"])
        self.hyst_bottom_offset = float(params["hysteresis"]["bottom_offset"])
        self.sat_top_limit = float(params["saturation"]["top_limit"])
        self.sat_bottom_limit = float(params["saturation"]["bottom_limit"])
        self.aw_gain = float(params["anti_windup"]["gain"])
        # Default control values of u and e
        self.u = self.manual_u
        # Control integral acumulator
        self.ui: float = 0

    # If control value is out of hysteresis bounds, the compute will return true
    def compute(self, y: float) -> bool:
        if self.state is ControllerState.MANUAL:
            self.r = y
            self.u = self.ui = self.manual_u
            return self.u > self.last_u + self.hyst_top_offset or self.u < self.last_u - self.hyst_bottom_offset
        e = self.r - y
        up = self.kp * e
        ui = self.ui + self.kp * (self.dt / self.ti) * e
        u_unsat = up + ui
        self.u = min(max(u_unsat, self.sat_bottom_limit), self.sat_top_limit)
        logging.debug(f"[{self.id}]\n\t\t\t u_unsat: {u_unsat:.2f}\n\t\t\t u_sat: {self.u:.2f}\n\t\t\t e: {e:.2f}\n\t\t\t ui: {self.ui:.2f}")
        self.ui = ui + self.aw_gain * (self.u - u_unsat)
        return self.u > self.last_u + self.hyst_top_offset or self.u < self.last_u - self.hyst_bottom_offset

    def set_sp(self, sp: float) -> None:
        self.r = sp
        logging.info(f"[{self.id}] Set SP to: {self.r}")

    def set_manual(self, enable: bool = True) -> None:
        self.state = ControllerState.AUTO
        if enable:
            self.state = ControllerState.MANUAL
        logging.info(f"[{self.id}] Set mode to: {self.state}")
    
    def set_manual_op(self, op: float) -> None:
        self.manual_u = op
        logging.info(f"[{self.id}] Set manual OP to: {self.manual_u}")
    
    def set_last_u(self, u: float) -> None:
        self.last_u = u
    
    def get_op(self) -> float:
        return self.u
    
    def get_sp(self) -> float:
        return self.r
    
    def is_manual(self) -> bool:
        return self.state == ControllerState.MANUAL
    
    def get_manual_op(self) -> float:
        return self.manual_u
